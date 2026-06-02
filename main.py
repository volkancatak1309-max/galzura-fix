#!/usr/bin/env python3
"""
GALZURA PRESTIGE REPORT — Ana Çalıştırıcı (v2)
═══════════════════════════════════════════════════════════════════════════════
URL al → veri topla → sektör tespit → rakip seç → Claude AI analiz → PDF üret

ÇEVRE DEĞİŞKENLERİ (zorunlu):
  PSI_KEY            = Google PageSpeed Insights API key
  PLACES_KEY         = Google Places API key
  ANTHROPIC_API_KEY  = Claude API key (Sonnet 4.6)

KULLANIM:
  python3 main.py <URL> [output.pdf]
═══════════════════════════════════════════════════════════════════════════════
"""
import sys
import os
from datetime import datetime

from data_collector import veri_topla
from sektor_tespit import sektor_tespit
from rakip_secim import akilli_rakip_sec, places_textsearch
from orchestrator_v2 import test_god_verisi_hazirla
from pdf_builder_v2 import build

# Avusturya/DACH şehir ve posta kodu ipuçları
_AT_SEHIRLER = ["Wien", "Graz", "Linz", "Salzburg", "Innsbruck", "Dornbirn",
                "Feldkirch", "Bregenz", "Bludenz", "Hohenems", "Lustenau",
                "Sulz", "Götzis", "Rankweil", "Hard", "Wolfurt", "Vorarlberg"]


def _html_lokasyon_tahmin(veri: dict) -> str:
    """Places yoksa HTML metninden şehir/bölge tahmin et."""
    html = veri.get("html_analysis", {})
    metin = " ".join([
        str(html.get("title", "")), str(html.get("meta_description", "")),
        str(html.get("address_raw", "")), str(veri.get("ham_metin", "")),
    ])
    # Bilinen şehirleri ara
    for s in _AT_SEHIRLER:
        if s.lower() in metin.lower():
            # Vorarlberg şehriyse bölgeyi döndür (daha geniş rakip havuzu)
            if s in ["Dornbirn","Feldkirch","Bregenz","Bludenz","Hohenems",
                     "Lustenau","Sulz","Götzis","Rankweil","Hard","Wolfurt"]:
                return "Vorarlberg"
            return s
    # .at domaini → Avusturya geneli
    if veri.get("domain","").endswith(".at"):
        return "Österreich"
    return ""


def _rakip_ara_lokasyonsuz(sektor: str, sehir: str, api_key: str) -> dict:
    """Koordinat yokken sektör+şehir metniyle rakip ara."""
    from rakip_secim import SEKTOR_PLACES_QUERY
    queries = SEKTOR_PLACES_QUERY.get(sektor, ["business"])
    all_results, seen = [], set()
    for q in queries[:2]:
        full_q = f"{q} {sehir}"
        try:
            # location=0,0 + radius yok → query metnine güven
            url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
            import requests
            r = requests.get(url, params={"query": full_q, "key": api_key,
                                          "language": "de"}, timeout=10)
            results = r.json().get("results", [])
        except Exception as e:
            print(f"  ⚠ '{full_q}' arama hatası: {e}")
            continue
        for res in results:
            pid = res.get("place_id")
            if not pid or pid in seen:
                continue
            seen.add(pid)
            all_results.append({
                "isim": res.get("name", ""),
                "puan": res.get("rating", 0) or 0,
                "yorum_sayisi": res.get("user_ratings_total", 0) or 0,
                "adres": res.get("formatted_address", ""),
            })
    # Puan*yorum gücüne göre sırala, ilk 6
    all_results.sort(key=lambda x: (x["puan"], x["yorum_sayisi"]), reverse=True)
    return {
        "rakipler": all_results[:6],
        "secim_kaynagi": f"Places API · '{sektor} {sehir}' metin araması",
    }


def prestige_report_uret(url: str, output_path: str = None,
                         psi_key: str = "", places_key: str = "",
                         anthropic_key: str = "") -> str:
    """Bir URL için Prestige Report PDF üretir. Returns: PDF dosya yolu."""
    psi_key = psi_key or os.environ.get("PSI_KEY", "")
    places_key = places_key or os.environ.get("PLACES_KEY", "")
    anthropic_key = anthropic_key or os.environ.get("ANTHROPIC_API_KEY", "")

    if not psi_key:
        raise ValueError("PSI_KEY çevre değişkeni eksik")
    if not places_key:
        raise ValueError("PLACES_KEY çevre değişkeni eksik")
    if not anthropic_key:
        raise ValueError("ANTHROPIC_API_KEY çevre değişkeni eksik")

    print("═" * 70)
    print("GALZURA PRESTIGE REPORT")
    print(f"URL: {url}")
    print(f"Başlama: {datetime.now().strftime('%H:%M:%S')}")
    print("═" * 70)

    # 1. Veri toplama (HTML + PSI + Places + sitemap)
    veri = veri_topla(url, psi_key, places_key)

    # 2. Sektör tespit
    print("▸ Sektör tespit ediliyor...")
    html = veri["html_analysis"]
    places = veri.get("places_firma", {})
    sektor_bilgisi = sektor_tespit(
        html=str(html)[:5000],
        title=html.get("title", ""),
        meta_description=html.get("meta_description", ""),
        url=url,
        gmb_kategoriler=places.get("types", []),
    )
    print(f"  → Sektör: {sektor_bilgisi['sektor']} ({sektor_bilgisi['etiket']})")

    # 3. Akıllı rakip seçim
    print("▸ Rakipler aranıyor...")
    rakip_sonuc = {"rakipler": [], "secim_kaynagi": "—"}

    # Lokasyon belirle: önce Places, yoksa HTML metninden ülke/şehir tahmini
    lat = places.get("lat")
    lng = places.get("lng")
    sehir = ""
    if places.get("address"):
        ap = places["address"].split(",")
        sehir = ap[-2].strip() if len(ap) >= 2 else ""

    # Places profili yoksa HTML'den lokasyon ipucu çıkar
    if not sehir:
        sehir = veri.get("lokasyon_ipucu", "") or _html_lokasyon_tahmin(veri)

    try:
        if lat and lng:
            # Koordinat varsa tam akıllı seçim
            rakip_sonuc = akilli_rakip_sec(
                musteri_sektor=sektor_bilgisi["sektor"],
                musteri_lat=lat, musteri_lng=lng,
                musteri_yorum_sayisi=places.get("user_ratings_total", 0) or 0,
                musteri_puan=places.get("rating", 0) or 0,
                api_key=places_key,
                musteri_place_id=places.get("place_id"),
                sehir=sehir,
            )
        elif sehir:
            # Koordinat yok ama şehir/ülke var → metin tabanlı rakip arama
            rakip_sonuc = _rakip_ara_lokasyonsuz(
                sektor_bilgisi["sektor"], sehir, places_key)
        print(f"  → {len(rakip_sonuc['rakipler'])} rakip bulundu (lokasyon: {sehir or 'bilinmiyor'})")
    except Exception as e:
        print(f"  ⚠ Rakip arama hatası: {e}")

    # 4. Claude AI analiz + PDF verisi
    print("▸ Claude AI analiz (6 çağrı)...")
    pdf_veri = test_god_verisi_hazirla(
        veri=veri,
        sektor_bilgisi=sektor_bilgisi,
        rakipler=[],  # rakip bolumu iptal edildi
        rakip_kaynak=rakip_sonuc.get("secim_kaynagi", "Places API"),
        api_key=anthropic_key,
    )

    # 5. PDF üret
    if output_path is None:
        firma_safe = "".join(c if c.isalnum() else "-" for c in pdf_veri["firma_adi"]).lower()
        output_path = f"/tmp/prestige-{firma_safe}-{datetime.now().strftime('%Y%m%d-%H%M')}.pdf"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    print(f"▸ PDF üretiliyor: {output_path}")
    build(pdf_veri, output_path)

    print("═" * 70)
    print(f"✓ Tamamlandı: {output_path}")
    print(f"  Skor: {pdf_veri['skor']}/100")
    print("═" * 70)
    return output_path


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    url = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) >= 3 else None
    try:
        path = prestige_report_uret(url, output_path)
        print(f"\nPDF: {path}")
    except Exception as e:
        print(f"\n✗ HATA: {e}")
        import traceback; traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
