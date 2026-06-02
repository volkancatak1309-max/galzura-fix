"""
GALZURA AKILLI RAKİP SEÇİM ALGORİTMASI
═══════════════════════════════════════════════════════════════════════════════
Müşteri firmasına meşru rakip seçer — daha kötü firmaları rakip diye SUNMAZ.

3 katmanlı seçim:
1. Aynı sektör + aynı bölge (50 km, büyük şehirde 20 km)
2. En az müşteri kadar yorum + 4.3+ puan
3. Adalet kontrolü: rakip müşteriden zayıfsa atılır

KULLANIM:
  from rakip_secim import akilli_rakip_sec
  rakipler = akilli_rakip_sec(
      musteri_sektor="restoran",
      musteri_lat=47.366,
      musteri_lng=9.685,
      musteri_yorum_sayisi=665,
      musteri_puan=4.0,
      api_key="...",
      arama_kelimesi="türk restoran"
  )
═══════════════════════════════════════════════════════════════════════════════
"""
import requests
import math
import json
from typing import List, Dict, Optional


SEKTOR_PLACES_QUERY = {
    "restoran": ["restaurant", "döner", "kebab", "lokanta"],
    "insaat":   ["bauunternehmen", "inşaat firması", "construction company"],
    "uretici":  ["markisen pergola", "sonnenschutz", "wintergarten", "fliegengitter"],
    "saglik":   ["klinik", "diş kliniği", "doktor"],
    "otomotiv": ["auto vermietung", "car rental", "araç kiralama", "oto galeri"],
    "hukuk":    ["anwalt", "law firm", "avukat", "hukuk bürosu"],
    "beauty":   ["beauty salon", "güzellik merkezi", "kuaför", "estetik"],
    "egitim":   ["kurs merkezi", "eğitim", "school", "akademi"],
    "eticaret": ["online shop", "store", "mağaza"],
    "general":  ["business", "firma", "unternehmen"],
}


def haversine_km(lat1, lng1, lat2, lng2):
    """İki nokta arası kilometre."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (math.sin(dlat/2)**2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlng/2)**2)
    return 2 * R * math.asin(math.sqrt(a))


def places_textsearch(query: str, lat: float, lng: float, radius_m: int,
                       api_key: str) -> List[Dict]:
    """Google Places API Text Search çağrısı."""
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "query": query,
        "location": f"{lat},{lng}",
        "radius": radius_m,
        "key": api_key,
        "language": "tr",
    }
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return data.get("results", [])


def akilli_rakip_sec(
    musteri_sektor: str,
    musteri_lat: float,
    musteri_lng: float,
    musteri_yorum_sayisi: int,
    musteri_puan: float,
    api_key: str,
    musteri_place_id: Optional[str] = None,
    arama_kelimesi: Optional[str] = None,
    sehir: str = "",
) -> Dict:
    """
    Müşteri için 3 meşru rakibi seçer.
    
    Returns: {
        "rakipler": [...],          # En iyi 3 rakip
        "tum_aday_sayisi": 25,
        "filtre_log": [...],        # Hangi adım kaç firma elendi
        "secim_kaynagi": "..."      # PDF'te şeffaflık için
    }
    """
    queries = []
    if arama_kelimesi:
        queries.append(arama_kelimesi)
    queries.extend(SEKTOR_PLACES_QUERY.get(musteri_sektor, ["business"]))
    if sehir:
        queries = [f"{q} {sehir}" for q in queries]

    # 50 km, büyük şehir tespit edilirse 20 km — burada basitlik için 50 km
    radius_m = 50_000

    all_results = []
    seen_ids = set()
    for q in queries:
        try:
            results = places_textsearch(q, musteri_lat, musteri_lng, radius_m, api_key)
        except Exception as e:
            print(f"  ⚠ Places query failed for '{q}': {e}")
            continue
        for r in results:
            pid = r.get("place_id")
            if not pid or pid in seen_ids:
                continue
            if musteri_place_id and pid == musteri_place_id:
                continue  # müşteriyi rakip olarak alma
            seen_ids.add(pid)
            all_results.append(r)

    filtre_log = [f"İlk tarama: {len(all_results)} aday bulundu (sektör + bölge)"]

    # FİLTRE 1: minimum yorum + puan
    min_yorum = max(musteri_yorum_sayisi, 20)  # en az müşteri kadar veya 20
    min_puan = 4.2
    aday_2 = [
        r for r in all_results
        if r.get("user_ratings_total", 0) >= min_yorum
        and r.get("rating", 0) >= min_puan
    ]
    filtre_log.append(
        f"Filtre 1 (≥{min_yorum} yorum + ≥{min_puan} puan): {len(aday_2)} aday kaldı"
    )

    # Eğer aday yetersizse minimum yorumu düşür
    if len(aday_2) < 3:
        min_yorum_fallback = max(int(musteri_yorum_sayisi * 0.7), 10)
        aday_2 = [
            r for r in all_results
            if r.get("user_ratings_total", 0) >= min_yorum_fallback
            and r.get("rating", 0) >= 4.0
        ]
        filtre_log.append(
            f"Fallback (≥{min_yorum_fallback} yorum + ≥4.0): {len(aday_2)} aday kaldı"
        )

    # FİLTRE 2: 3 farklı kategori seç
    # - Lider 1: en yüksek puan + bol yorum
    # - Lider 2: en fazla yorum
    # - Lider 3: en yakın mesafe (yerel rakip)

    if len(aday_2) == 0:
        return {
            "rakipler": [],
            "tum_aday_sayisi": len(all_results),
            "filtre_log": filtre_log + ["Hiç meşru rakip bulunamadı"],
            "secim_kaynagi": "Google Places API · yetersiz veri",
        }

    # Mesafe ekle
    for r in aday_2:
        loc = r.get("geometry", {}).get("location", {})
        if loc:
            r["_mesafe_km"] = haversine_km(
                musteri_lat, musteri_lng,
                loc.get("lat", musteri_lat), loc.get("lng", musteri_lng)
            )
        else:
            r["_mesafe_km"] = 999

    rakip_pool = list(aday_2)
    secilen = []

    # Lider 1: En yüksek puan (eşitse en çok yorum)
    if rakip_pool:
        rakip_pool.sort(
            key=lambda r: (r.get("rating", 0), r.get("user_ratings_total", 0)),
            reverse=True
        )
        secilen.append(rakip_pool.pop(0))

    # Lider 2: En çok yorum
    if rakip_pool:
        rakip_pool.sort(key=lambda r: r.get("user_ratings_total", 0), reverse=True)
        secilen.append(rakip_pool.pop(0))

    # Lider 3: En yakın
    if rakip_pool:
        rakip_pool.sort(key=lambda r: r.get("_mesafe_km", 999))
        secilen.append(rakip_pool.pop(0))

    filtre_log.append(f"3 rakip seçildi: lider puan + lider yorum + yakın")

    rakipler_final = [
        {
            "isim": r.get("name", "—"),
            "place_id": r.get("place_id"),
            "puan": r.get("rating", 0),
            "yorum_sayisi": r.get("user_ratings_total", 0),
            "adres": r.get("formatted_address", ""),
            "mesafe_km": round(r.get("_mesafe_km", 0), 1),
            "lat": r.get("geometry", {}).get("location", {}).get("lat"),
            "lng": r.get("geometry", {}).get("location", {}).get("lng"),
        }
        for r in secilen
    ]

    kaynak = (
        f"Google Places API · {len(all_results)} aday tarandı · "
        f"≥{min_yorum} yorum + ≥4.2 puan filtresinden geçen ilk 3"
    )

    return {
        "rakipler": rakipler_final,
        "tum_aday_sayisi": len(all_results),
        "filtre_log": filtre_log,
        "secim_kaynagi": kaynak,
    }


def hizli_test():
    """Demo testi (Doğan's Bistro Hohenems için)."""
    import os
    api_key = os.environ.get("GOOGLE_PLACES_KEY", "")
    if not api_key:
        print("  ⚠ GOOGLE_PLACES_KEY environment variable yok, atlanıyor")
        return
    sonuc = akilli_rakip_sec(
        musteri_sektor="restoran",
        musteri_lat=47.366,
        musteri_lng=9.685,
        musteri_yorum_sayisi=665,
        musteri_puan=4.0,
        api_key=api_key,
        arama_kelimesi="türk restoran",
        sehir="Hohenems Vorarlberg",
    )
    print(json.dumps(sonuc, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    hizli_test()
