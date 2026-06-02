"""
GALZURA TEST GOD — Orchestrator v2
═══════════════════════════════════════════════════════════════════════════════
Akış:
  veri_topla (data_collector) → sektör tespit → rakip seç →
  her sayfa için Claude AI çağrısı → pdf_verisi sözlüğü → pdf_builder_v2.build
═══════════════════════════════════════════════════════════════════════════════
"""
import json
from datetime import datetime
from typing import Dict, List

from claude_client import claude_json, claude_call, ClaudeError
from prompts import (PROMPT_SKOR_YORUM, PROMPT_TEKNIK, PROMPT_SEO, PROMPT_GEO,
                     PROMPT_RAKIP, PROMPT_COZUM, sektor_baglami)


# ─── 12 KATMAN SKOR (data_collector verisinden) ───
def skor_hesapla(veri: Dict) -> int:
    """Basit ağırlıklı skor — pdf_builder'daki ile aynı mantık."""
    html = veri.get("html_analysis", {})
    psi = veri.get("psi_mobile", {}).get("scores", {})
    places = veri.get("places_firma", {})
    headers = veri.get("headers", {})
    robots = veri.get("robots_sitemap", {})

    toplam = 0.0

    # CWV %25
    perf = psi.get("performance")
    toplam += (int(perf*100) if perf is not None else 50) * 0.25
    # Schema %15
    sc = html.get("schema_blocks", 0)
    st = html.get("schema_types", [])
    schema_skor = 90 if (sc and any(t in st for t in ["Restaurant","Dentist","Manufacturer","LocalBusiness","Organization","Product"])) else (30 if sc else 0)
    toplam += schema_skor * 0.15
    # Hreflang %10
    hl = len(html.get("hreflang_tags", []))
    toplam += (90 if hl>=3 else 50 if hl>=1 else 0) * 0.10
    # İçerik tazeliği %10
    smc = robots.get("sitemap_url_count", 0)
    sms = robots.get("sitemap_spam_count", 0)
    toplam += (15 if sms>0 else 80 if smc>=30 else 50 if smc>=5 else 25) * 0.10
    # Analytics %5
    an = [k for k,v in html.get("analytics",{}).items() if v]
    toplam += (85 if len(an)>=2 else 50 if an else 0) * 0.05
    # GMB %10
    rating = places.get("rating")
    rc = places.get("user_ratings_total",0) or 0
    toplam += (90 if (rating and rating>=4.5 and rc>=50) else 60 if (rating and rating>=4.0) else 30 if rating else 20) * 0.10
    # Çoklu dil %5
    toplam += (85 if (hl>=3 and html.get("lang_html_attr")) else 40 if hl>=1 else 10) * 0.05
    # Mobil UX %5
    mob = sum([bool(html.get("viewport")), html.get("h1_count",0)>=1, bool(html.get("meta_description"))])
    toplam += int(mob/3*100) * 0.05
    # Sosyal %5
    og = html.get("og_tags",{}); tw = html.get("twitter_tags",{})
    toplam += (70 if (len(og)>=3 and len(tw)>=2) else 40 if len(og)>=2 else 10) * 0.05
    # Dizinler %5
    toplam += (50 if places.get("place_id") else 15) * 0.05
    # Erişilebilirlik %3
    a11y = psi.get("accessibility")
    toplam += (int(a11y*100) if a11y is not None else 50) * 0.03
    # CDN %2
    cdn = headers.get("cdn","Yok")
    toplam += (80 if cdn!="Yok" else 20) * 0.02

    return round(toplam)


# ─── VERİ KARTI (Places API → tablo satırları) ───
def veri_karti_hazirla(veri: Dict) -> List:
    p = veri.get("places_firma", {})
    html = veri.get("html_analysis", {})
    rows = []
    if p.get("name"): rows.append(("Firma Adı", p["name"]))
    elif html.get("title"): rows.append(("Firma Adı", html["title"].split("|")[0].split("–")[0].strip()))
    if p.get("place_id"): rows.append(("Place ID", p["place_id"]))
    if p.get("types"): rows.append(("Kategori (Google)", " · ".join(p["types"][:3])))
    if p.get("address"): rows.append(("Adres", p["address"]))
    if p.get("phone_number"): rows.append(("Telefon", p["phone_number"]))
    rows.append(("Web Sitesi", veri.get("domain","—")))
    if p.get("lat"): rows.append(("Koordinatlar", f"{p['lat']}, {p['lng']}"))
    if p.get("rating"): rows.append(("Google Puanı", f"{p['rating']} / 5,0"))
    rc = p.get("user_ratings_total")
    if rc is not None and p.get("rating"): rows.append(("Yorum Sayısı", f"{rc} yorum"))

    # Google profili yoksa açık uyarı + site verisi
    if not p.get("place_id"):
        rows.append(("Google İşletme Profili", "BULUNAMADI — kayıtlı değil veya eksik"))
        if html.get("title"): rows.append(("Site Başlığı", html["title"][:50]))
        if html.get("meta_description"): rows.append(("Google Tanıtım Yazısı", html["meta_description"][:50]))
        site_dili = html.get("lang_html_attr") or "belirtilmemiş"
        rows.append(("Site Dili", site_dili))
    return rows


# ─── TEKNİK TABLO (PSI + HTML → değer + link) ───
def teknik_tablo_hazirla(veri: Dict) -> List:
    domain = veri.get("domain","")
    html = veri.get("html_analysis", {})
    psi = veri.get("psi_mobile", {})
    vit = psi.get("vitals", {})
    sc = psi.get("scores", {})
    rows = []

    # LCP
    lcp = vit.get("lcp_ms")
    if lcp:
        rows.append({"olcum":"Site hızı (LCP, mobil)", "deger":f"{round(lcp/1000,1)} sn",
                     "durum":"fail" if lcp>2500 else "pass",
                     "link":f"pagespeed.web.dev/analysis?url={domain}"})
    # Performance skor
    perf = sc.get("performance")
    if perf is not None:
        rows.append({"olcum":"Performans skoru", "deger":f"{int(perf*100)}/100",
                     "durum":"fail" if perf<0.5 else "pass" if perf>=0.9 else "neutral",
                     "link":f"pagespeed.web.dev/analysis?url={domain}"})
    # Schema
    scb = html.get("schema_blocks",0)
    rows.append({"olcum":"Google tanıtım kodu", "deger":"YOK" if scb==0 else f"{scb} adet",
                 "durum":"fail" if scb==0 else "pass",
                 "link":f"search.google.com/test/rich-results?url={domain}"})
    # Hreflang
    hl = len(html.get("hreflang_tags",[]))
    rows.append({"olcum":"Çoklu dil ayarı", "deger":"YOK" if hl==0 else f"{hl} dil",
                 "durum":"fail" if hl==0 else "pass", "link":"—"})
    # Analytics
    an = [k for k,v in html.get("analytics",{}).items() if v]
    rows.append({"olcum":"Ziyaretçi ölçümü", "deger":"YOK" if not an else "VAR",
                 "durum":"fail" if not an else "pass", "link":"—"})
    # H1
    h1 = html.get("h1_count",0)
    rows.append({"olcum":"Sayfa başlığı", "deger":"YOK" if h1==0 else f"{h1} adet",
                 "durum":"fail" if h1==0 else "pass", "link":"—"})
    # Mobil
    a11y = sc.get("accessibility")
    if a11y is not None:
        rows.append({"olcum":"Mobilde kullanım kolaylığı", "deger":f"{int(a11y*100)}/100",
                     "durum":"fail" if a11y<0.7 else "pass",
                     "link":f"search.google.com/test/mobile-friendly?url={domain}"})
    return rows


# ─── ANA FONKSİYON ───
def test_god_verisi_hazirla(veri: Dict, sektor_bilgisi: Dict,
                             rakipler: List[Dict], rakip_kaynak: str,
                             api_key: str = "") -> Dict:
    """Toplanan veriyi Claude ile zenginleştirip pdf_builder formatına çevirir."""
    sektor = sektor_bilgisi["sektor"]
    sektor_etiket = sektor_bilgisi["etiket"]
    html = veri.get("html_analysis", {})
    places = veri.get("places_firma", {})
    baglam = sektor_baglami(sektor)

    firma_adi = places.get("name") or html.get("title","").split("|")[0].split("–")[0].strip() or veri.get("domain","Firma")
    sehir = ""
    if places.get("address"):
        parts = places["address"].split(",")
        sehir = parts[-2].strip() if len(parts)>=2 else ""
    lokasyon = places.get("address", veri.get("domain",""))

    skor = skor_hesapla(veri)

    # Sektör ortalama + lider (rakip verisinden hesapla)
    if rakipler:
        rakip_puanlar = [r.get("puan",0) for r in rakipler if r.get("puan")]
        # basit: ortalama yorum bazlı görünürlük tahmini değil, sadece referans
    sektor_skor = 62  # sabit referans (sektör ort. dijital olgunluk)
    lider_skor = 84
    lider_isim = rakipler[0]["isim"] if rakipler else "lider"

    # ─── CLAUDE ÇAĞRILARI ───
    print("  → Claude: skor yorumu...")
    skor_yorum = ""
    try:
        skor_yorum = claude_call(PROMPT_SKOR_YORUM,
            f"Firma: {firma_adi}\nSektör: {sektor_etiket}\nBağlam: {baglam}\n"
            f"Skor: {skor}/100\nSektör ortalaması: {sektor_skor}\nLider: {lider_skor}\n"
            f"Schema bloğu: {html.get('schema_blocks',0)}\n"
            f"Hreflang: {len(html.get('hreflang_tags',[]))} dil\n"
            f"Analytics: {[k for k,v in html.get('analytics',{}).items() if v] or 'yok'}\n"
            f"Google: {places.get('rating','?')}/{places.get('user_ratings_total','?')} yorum",
            api_key=api_key, max_tokens=200)
    except ClaudeError as e:
        skor_yorum = f"Skor {skor}/100. (AI yorum üretilemedi: {e})"

    print("  → Claude: teknik yorumlar...")
    teknik_yorumlar = []
    try:
        teknik_data = {
            "firma": firma_adi, "sektor_baglam": baglam,
            "lcp_sn": round(veri.get("psi_mobile",{}).get("vitals",{}).get("lcp_ms",0)/1000,1) if veri.get("psi_mobile",{}).get("vitals",{}).get("lcp_ms") else None,
            "performans_skor": int(veri.get("psi_mobile",{}).get("scores",{}).get("performance",0)*100) if veri.get("psi_mobile",{}).get("scores",{}).get("performance") is not None else None,
            "schema_blok": html.get("schema_blocks",0),
            "hreflang_dil": len(html.get("hreflang_tags",[])),
            "h1_var": html.get("h1_count",0)>0,
            "analytics": [k for k,v in html.get("analytics",{}).items() if v],
            "erisilebilirlik_skor": int(veri.get("psi_mobile",{}).get("scores",{}).get("accessibility",0)*100) if veri.get("psi_mobile",{}).get("scores",{}).get("accessibility") is not None else None,
            "viewport": html.get("viewport",""),
        }
        teknik_yorumlar = claude_json(PROMPT_TEKNIK,
            "Teknik veriyi yorumla:\n" + json.dumps(teknik_data, ensure_ascii=False, indent=2),
            api_key=api_key, max_tokens=1200)
        if isinstance(teknik_yorumlar, dict):
            teknik_yorumlar = teknik_yorumlar.get("bulgular", teknik_yorumlar.get("items", []))
    except ClaudeError as e:
        print(f"    ⚠ teknik yorum hatası: {e}")
        teknik_yorumlar = []

    print("  → Claude: SEO analizi...")
    seo = {}
    try:
        seo_data = {
            "firma": firma_adi, "sektor_baglam": baglam, "site": veri.get("domain",""),
            "html_bulgular": {
                "title": html.get("title",""),
                "meta_description": html.get("meta_description",""),
                "h1_var_mi": html.get("h1_count",0)>0,
                "schema_blok_sayisi": html.get("schema_blocks",0),
                "schema_tipleri": html.get("schema_types",[]),
                "hreflang_etiket_sayisi": len(html.get("hreflang_tags",[])),
                "site_dili": html.get("lang_html_attr","belirsiz"),
                "viewport": html.get("viewport",""),
                "analytics": {k:v for k,v in html.get("analytics",{}).items()},
                "sitemap_url_sayisi": veri.get("robots_sitemap",{}).get("sitemap_url_count","bilinmiyor"),
            }
        }
        seo = claude_json(PROMPT_SEO,
            "SEO verisini analiz et:\n" + json.dumps(seo_data, ensure_ascii=False, indent=2),
            api_key=api_key, max_tokens=1500)
    except ClaudeError as e:
        print(f"    ⚠ SEO hatası: {e}")
        seo = {"ozet":"SEO analizi üretilemedi.", "eksikler":[], "guclu_yanlar":[]}

    print("  → Claude: GEO analizi...")
    geo = {}
    try:
        geo_data = {
            "firma": firma_adi, "sektor_baglam": baglam,
            "schema_blok": html.get("schema_blocks",0),
            "hreflang_dil": len(html.get("hreflang_tags",[])),
            "yapilandirilmis_veri": html.get("schema_types",[]),
            "icerik_dili": html.get("lang_html_attr","belirsiz"),
            "meta_description_var": bool(html.get("meta_description")),
            "sehir": (places.get("address","").split(",")[-2].strip() if places.get("address") and "," in places.get("address","") else sehir),
        }
        geo = claude_json(PROMPT_GEO,
            "GEO verisini analiz et:\n" + json.dumps(geo_data, ensure_ascii=False, indent=2),
            api_key=api_key, max_tokens=1000)
    except ClaudeError as e:
        print(f"    ⚠ GEO hatası: {e}")
        geo = {"ozet":"GEO analizi üretilemedi.", "engeller":[], "test_onerisi":""}

    print("  → Claude: rakip yorumu...")
    rakip_yorum = {}
    try:
        rakip_data = {
            "firma": firma_adi, "sektor_baglam": baglam,
            "firma_google": {"puan": places.get("rating"), "yorum_sayisi": places.get("user_ratings_total"), "sehir": sehir},
            "rakipler": [{"isim":r["isim"],"puan":r.get("puan"),"yorum":r.get("yorum_sayisi"),"sehir":r.get("adres","").split(",")[-2].strip() if r.get("adres") and "," in r.get("adres","") else ""} for r in rakipler[:6]]
        }
        rakip_yorum = claude_json(PROMPT_RAKIP,
            "Rakip verisini yorumla:\n" + json.dumps(rakip_data, ensure_ascii=False, indent=2),
            api_key=api_key, max_tokens=800)
    except ClaudeError as e:
        print(f"    ⚠ rakip hatası: {e}")
        rakip_yorum = {"ozet":"", "firsat":"", "risk":""}

    print("  → Claude: çözüm yolu...")
    cozum = {}
    try:
        cozum_data = {
            "firma": firma_adi, "sektor_baglam": baglam, "skor": skor,
            "eksikler_ozet": {
                "schema": html.get("schema_blocks",0)==0,
                "hreflang": len(html.get("hreflang_tags",[]))==0,
                "analytics": not any(html.get("analytics",{}).values()),
                "h1": html.get("h1_count",0)==0,
                "site_hizi_sorun": (veri.get("psi_mobile",{}).get("vitals",{}).get("lcp_ms",0) or 0)>2500,
                "google_yorum_az": (places.get("user_ratings_total",0) or 0)<50,
            }
        }
        cozum = claude_json(PROMPT_COZUM,
            "Çözüm yolu öner:\n" + json.dumps(cozum_data, ensure_ascii=False, indent=2),
            api_key=api_key, max_tokens=1500)
    except ClaudeError as e:
        print(f"    ⚠ çözüm hatası: {e}")
        cozum = {"ozet":"", "oncelikli_adimlar":[], "beklenti":""}

    # ─── RAKİP TABLOSU (firma + rakipler birleşik, puana göre sıralı) ───
    rakip_tablo = []
    all_firms = list(rakipler)
    # firma kendini ekle
    self_entry = {
        "isim": firma_adi, "puan": places.get("rating",0) or 0,
        "yorum_sayisi": places.get("user_ratings_total",0) or 0,
        "adres": places.get("address",""), "self": True
    }
    combined = all_firms + [self_entry]
    combined.sort(key=lambda r: (r.get("puan",0), r.get("yorum_sayisi",0)), reverse=True)
    for r in combined:
        sehir_r = ""
        if r.get("adres") and "," in r.get("adres",""):
            sehir_r = r["adres"].split(",")[-2].strip()
        rakip_tablo.append({
            "isim": r["isim"],
            "puan": f"{r.get('puan',0):.1f}".replace(".",","),
            "yorum": str(r.get("yorum_sayisi",0)),
            "sehir": sehir_r,
            "self": r.get("self", False),
        })

    # ─── METODOLOJİ + DOĞRULAMA ───
    domain = veri.get("domain","")
    metodoloji = [
        ("İşletme verisi", "Google Places API", f"maps.google.com → {firma_adi[:20]}"),
        ("Site hızı", "PageSpeed Insights API", f"pagespeed.web.dev/analysis?url={domain}"),
        ("Schema", "HTML JSON-LD parse", f"search.google.com/test/rich-results"),
        ("Mobil uyum", "Lighthouse", f"search.google.com/test/mobile-friendly"),
        ("Rakipler", "Places API textsearch", f"maps.google.com"),
        ("SEO/GEO analizi", "Galzura + Claude AI", "ham veri talep edilebilir"),
    ]
    # GEO promptundan üretilen gerçek test sorusunu kullan (firma adı içermez)
    ai_test_q = geo.get("test_sorusu", "") or f"{sektor_etiket} {sehir}".strip()
    dogrulama_linkleri = [
        f"1. Hız:    pagespeed.web.dev/analysis?url={domain}",
        f"2. Schema: search.google.com/test/rich-results",
        f"3. Mobil:  search.google.com/test/mobile-friendly",
        f"4. Profil: maps.google.com → \"{firma_adi[:25]}\"",
        f"5. AI:     ChatGPT'ye sorun: \"{ai_test_q[:60]}\"",
    ]

    rapor_no = f"GAK-{domain.split('.')[0][:6].upper()}-{datetime.now().strftime('%y%m%d')}"

    return {
        "firma_adi": firma_adi[:55],
        "sehir": sehir,
        "lokasyon": lokasyon[:65],
        "sektor_ad": sektor_etiket,
        "tarih": datetime.now().strftime("%d.%m.%Y"),
        "rapor_no": rapor_no,
        "skor": skor,
        "sektor_skor": sektor_skor,
        "lider_skor": lider_skor,
        "lider_isim": lider_isim,
        "skor_yorum": skor_yorum,
        "veri_karti": veri_karti_hazirla(veri),
        "teknik_tablo": teknik_tablo_hazirla(veri),
        "teknik_yorumlar": teknik_yorumlar if isinstance(teknik_yorumlar, list) else [],
        "seo": seo,
        "geo": geo,
        "rakip_tablo": rakip_tablo,
        "rakip_yorum": rakip_yorum,
        "cozum": cozum,
        "metodoloji": metodoloji,
        "dogrulama_linkleri": dogrulama_linkleri,
    }
