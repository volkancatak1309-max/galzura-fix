"""
GALZURA DATA COLLECTOR
═══════════════════════════════════════════════════════════════════════════════
URL alır, Açık Karne raporu için gerekli TÜM veriyi toplar:
  1. HTML kaynak (anasayfa + about + contact)
  2. HTTP headers (CDN, server, cache)
  3. robots.txt + sitemap.xml
  4. Google PageSpeed Insights (mobile + desktop)
  5. Google Places (firma + ipucu adres/koordinat)
  6. Schema JSON-LD parse
  7. Analytics tespit (GA/GTM/Pixel)
  8. Hack/spam link tespit
  9. Hreflang + dil tespit
  10. Sektör tespit

KULLANIM:
  from data_collector import veri_topla
  veri = veri_topla("https://example.com", psi_key, places_key)
═══════════════════════════════════════════════════════════════════════════════
"""
import requests
import re
import json
import os
from urllib.parse import urlparse
from datetime import datetime
from typing import Dict, List, Optional


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36 Galzura-Scanner/1.0"
}

# Hack/Spam tespit için bilinen kumar/casino kelime listesi
SPAM_KEYWORDS = [
    "betsafe", "tadhana", "casino", "kasino", "kasyno",
    "slot", "pinco", "pinup", "gama-casino", "kolaybet",
    "1xbet", "betwinner", "mostbet", "888casino", "ladbrokes",
    "wettbüro", "wager", "jackpot", "roulette", "blackjack",
    "poker.com", "betting", "doorway"
]

CLOAKING_PATTERNS = [
    r'position:\s*absolute;[^"]*left:\s*-\d{3,}px',  # left: -39298px
    r'text-indent:\s*-\d{4,}px',                       # off-screen
    r'visibility:\s*hidden\s*;\s*position:\s*absolute',
    r'display:\s*none\s*;\s*position:\s*absolute',
]


def _safe_get(url: str, timeout: int = 12) -> Optional[requests.Response]:
    """Güvenli GET — hata durumunda None döner."""
    try:
        return requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
    except Exception as e:
        print(f"  ⚠ GET hatası ({url}): {e}")
        return None


def _normalize_url(url: str) -> str:
    """URL'yi normalize et — https:// ekle eğer yoksa."""
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    if not url.endswith("/") and "/" not in urlparse(url).path:
        url += "/"
    return url


def _domain(url: str) -> str:
    """URL'den domain çıkart."""
    p = urlparse(url)
    return p.netloc.replace("www.", "")


# ═════════════════════════════════════════════════════════════
# 1. HTML KAYNAK ANALİZİ
# ═════════════════════════════════════════════════════════════
def html_analiz(html: str) -> Dict:
    """HTML kaynaktan tüm bilgileri çıkar."""
    if not html:
        return {}

    sonuc = {
        "title": "",
        "meta_description": "",
        "canonical": "",
        "h1_count": 0,
        "h2_count": 0,
        "h1_texts": [],
        "lang_html_attr": "",
        "hreflang_tags": [],
        "schema_blocks": 0,
        "schema_types": [],
        "og_tags": {},
        "twitter_tags": {},
        "viewport": "",
        "theme_color": "",
        "robots_meta": "",
        "favicon": "",
        "stack": {
            "wordpress": False,
            "elementor": False,
            "elementor_version": "",
            "rank_math": False,
            "yoast": False,
            "litespeed_cache": False,
            "wpml": False,
            "shopify": False,
            "wix": False,
            "vercel": False,
            "next_js": False,
            "tailwind": False,
        },
        "analytics": {
            "ga4": False,
            "gtm": False,
            "ua_legacy": False,
            "meta_pixel": False,
            "hotjar": False,
            "clarity": False,
        },
        "hack_signals": {
            "spam_keywords_found": [],
            "cloaking_detected": False,
            "suspicious_links": [],
        },
        "image_count": 0,
        "images_with_alt": 0,
    }

    # Title
    m = re.search(r'<title[^>]*>([^<]+)</title>', html, re.IGNORECASE | re.DOTALL)
    if m: sonuc["title"] = m.group(1).strip()

    # Meta description
    m = re.search(r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']+)["\']',
                  html, re.IGNORECASE)
    if m: sonuc["meta_description"] = m.group(1).strip()

    # Canonical
    m = re.search(r'<link\s+rel=["\']canonical["\']\s+href=["\']([^"\']+)["\']',
                  html, re.IGNORECASE)
    if m: sonuc["canonical"] = m.group(1).strip()

    # H1 / H2
    h1_matches = re.findall(r'<h1[^>]*>(.+?)</h1>', html, re.IGNORECASE | re.DOTALL)
    sonuc["h1_count"] = len(h1_matches)
    sonuc["h1_texts"] = [re.sub(r'<[^>]+>', '', h).strip()[:80] for h in h1_matches[:3]]
    sonuc["h2_count"] = len(re.findall(r'<h2[^>]*>', html, re.IGNORECASE))

    # <html lang="...">
    m = re.search(r'<html[^>]*\blang=["\']([^"\']+)["\']', html, re.IGNORECASE)
    if m: sonuc["lang_html_attr"] = m.group(1).strip()

    # Hreflang
    hreflang = re.findall(r'hreflang=["\']([^"\']+)["\']', html, re.IGNORECASE)
    sonuc["hreflang_tags"] = list(set(hreflang))

    # Schema JSON-LD
    jsonld_blocks = re.findall(
        r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html, re.IGNORECASE | re.DOTALL
    )
    sonuc["schema_blocks"] = len(jsonld_blocks)
    schema_types = set()
    for block in jsonld_blocks:
        type_matches = re.findall(r'"@type"\s*:\s*"([^"]+)"', block)
        for t in type_matches:
            schema_types.add(t)
        # Array @type
        array_types = re.findall(r'"@type"\s*:\s*\[([^\]]+)\]', block)
        for arr in array_types:
            for t in re.findall(r'"([^"]+)"', arr):
                schema_types.add(t)
    sonuc["schema_types"] = sorted(schema_types)

    # Open Graph
    og_matches = re.findall(
        r'<meta\s+property=["\']og:([^"\']+)["\']\s+content=["\']([^"\']+)["\']',
        html, re.IGNORECASE
    )
    for prop, val in og_matches:
        sonuc["og_tags"][prop] = val

    # Twitter Card
    tw_matches = re.findall(
        r'<meta\s+name=["\']twitter:([^"\']+)["\']\s+content=["\']([^"\']+)["\']',
        html, re.IGNORECASE
    )
    for prop, val in tw_matches:
        sonuc["twitter_tags"][prop] = val

    # Viewport
    m = re.search(r'<meta\s+name=["\']viewport["\']\s+content=["\']([^"\']+)["\']',
                  html, re.IGNORECASE)
    if m: sonuc["viewport"] = m.group(1).strip()

    # Theme color
    m = re.search(r'<meta\s+name=["\']theme-color["\']\s+content=["\']([^"\']+)["\']',
                  html, re.IGNORECASE)
    if m: sonuc["theme_color"] = m.group(1).strip()

    # Stack tespit
    s = html.lower()
    if "wp-content" in s or "wp-includes" in s:
        sonuc["stack"]["wordpress"] = True
    if "elementor" in s:
        sonuc["stack"]["elementor"] = True
        m = re.search(r'elementor[^"\']*?(\d+\.\d+\.\d+)', s)
        if m: sonuc["stack"]["elementor_version"] = m.group(1)
    if "rank-math" in s or "rankmath" in s:
        sonuc["stack"]["rank_math"] = True
    if "yoast" in s:
        sonuc["stack"]["yoast"] = True
    if "litespeed" in s or "x-litespeed" in s:
        sonuc["stack"]["litespeed_cache"] = True
    if "wpml" in s:
        sonuc["stack"]["wpml"] = True
    if "cdn.shopify.com" in s or "shopify-section" in s:
        sonuc["stack"]["shopify"] = True
    if "wix.com" in s or "wixstatic" in s:
        sonuc["stack"]["wix"] = True
    if "vercel" in s or "_next/static" in s:
        sonuc["stack"]["vercel"] = True
    if "_next/" in s or "__next_data__" in s:
        sonuc["stack"]["next_js"] = True
    if "tailwind" in s:
        sonuc["stack"]["tailwind"] = True

    # Analytics tespit
    if re.search(r'\bG-[A-Z0-9]{6,12}\b', html):
        sonuc["analytics"]["ga4"] = True
    if re.search(r'\bGTM-[A-Z0-9]{4,10}\b', html):
        sonuc["analytics"]["gtm"] = True
    if re.search(r'\bUA-\d{4,10}-\d{1,3}\b', html):
        sonuc["analytics"]["ua_legacy"] = True
    if "fbq(" in html or "facebook.com/tr?id=" in html:
        sonuc["analytics"]["meta_pixel"] = True
    if "hotjar" in s:
        sonuc["analytics"]["hotjar"] = True
    if "clarity.ms" in s:
        sonuc["analytics"]["clarity"] = True

    # Hack/Spam tespit
    found_spam = []
    for kw in SPAM_KEYWORDS:
        if kw.lower() in s:
            found_spam.append(kw)
    sonuc["hack_signals"]["spam_keywords_found"] = found_spam

    # Cloaking pattern
    for pattern in CLOAKING_PATTERNS:
        if re.search(pattern, html, re.IGNORECASE):
            sonuc["hack_signals"]["cloaking_detected"] = True
            break

    # Şüpheli outbound link'ler (kumar domainleri)
    spam_domains = ["betsafe", "tadhana", "1xbet", "casino", "kasino", "slot"]
    for sd in spam_domains:
        for m in re.finditer(rf'href=["\']https?://[^"\']*{re.escape(sd)}[^"\']*["\']', html, re.IGNORECASE):
            sonuc["hack_signals"]["suspicious_links"].append(m.group(0)[:200])

    # Görsel sayımı
    img_tags = re.findall(r'<img[^>]+>', html, re.IGNORECASE)
    sonuc["image_count"] = len(img_tags)
    sonuc["images_with_alt"] = sum(1 for t in img_tags
                                    if re.search(r'\balt=["\'][^"\']+["\']', t))

    return sonuc


# ═════════════════════════════════════════════════════════════
# 2. PSI (PAGESPEED INSIGHTS)
# ═════════════════════════════════════════════════════════════
def psi_olc(url: str, api_key: str, strategy: str = "mobile") -> Dict:
    """PageSpeed Insights API çağrısı."""
    api_url = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
    params = {
        "url": url,
        "strategy": strategy,
        "category": ["performance", "accessibility", "best-practices", "seo"],
        "key": api_key,
    }
    try:
        r = requests.get(api_url, params=params, timeout=60)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"  ⚠ PSI hatası ({strategy}): {e}")
        return {"hata": str(e)}

    cats = data.get("lighthouseResult", {}).get("categories", {})
    audits = data.get("lighthouseResult", {}).get("audits", {})

    def _audit_val(key, num=False):
        a = audits.get(key, {})
        if num:
            return a.get("numericValue")
        return a.get("displayValue", "—")

    def _audit_score(key):
        return audits.get(key, {}).get("score")

    return {
        "strategy": strategy,
        "scores": {
            "performance":    cats.get("performance",     {}).get("score"),
            "accessibility":  cats.get("accessibility",   {}).get("score"),
            "best_practices": cats.get("best-practices",  {}).get("score"),
            "seo":            cats.get("seo",             {}).get("score"),
        },
        "vitals": {
            "lcp_display": _audit_val("largest-contentful-paint"),
            "lcp_ms":       _audit_val("largest-contentful-paint", num=True),
            "fcp_display": _audit_val("first-contentful-paint"),
            "fcp_ms":       _audit_val("first-contentful-paint", num=True),
            "cls_display": _audit_val("cumulative-layout-shift"),
            "cls_val":      _audit_val("cumulative-layout-shift", num=True),
            "tbt_display": _audit_val("total-blocking-time"),
            "tbt_ms":       _audit_val("total-blocking-time", num=True),
            "si_display":  _audit_val("speed-index"),
            "tti_display": _audit_val("interactive"),
        },
        "audit_fails": {
            "is_on_https":          _audit_score("is-on-https") == 0,
            "image_size_responsive": _audit_score("image-size-responsive") == 0,
            "link_name":            _audit_score("link-name") == 0,
            "errors_in_console":    _audit_score("errors-in-console") == 0,
            "uses_responsive_images": _audit_score("uses-responsive-images") == 0,
            "color_contrast":       _audit_score("color-contrast") == 0,
        },
    }


# ═════════════════════════════════════════════════════════════
# 3. HTTP HEADERS
# ═════════════════════════════════════════════════════════════
def header_analiz(url: str) -> Dict:
    """HTTP response headers'tan stack bilgileri çek."""
    try:
        r = requests.head(url, headers=HEADERS, timeout=10, allow_redirects=True)
        h = {k.lower(): v for k, v in r.headers.items()}
    except Exception as e:
        try:
            r = requests.get(url, headers=HEADERS, timeout=10, allow_redirects=True, stream=True)
            h = {k.lower(): v for k, v in r.headers.items()}
            r.close()
        except Exception:
            return {}

    return {
        "server":        h.get("server", "—"),
        "x_powered_by":  h.get("x-powered-by", "—"),
        "cache_control": h.get("cache-control", "—"),
        "cdn":           "Cloudflare" if "cf-ray" in h
                         else "BunnyCDN" if "bunny" in h.get("server", "").lower()
                         else "Vercel" if "vercel" in h.get("server", "").lower()
                         else "Yok",
        "litespeed_cache": h.get("x-litespeed-cache", "—"),
        "alt_svc":       h.get("alt-svc", "—"),
        "x_robots_tag":  h.get("x-robots-tag", "—"),
        "all_headers":   {k: v[:200] for k, v in h.items()},
    }


# ═════════════════════════════════════════════════════════════
# 4. ROBOTS.TXT + SITEMAP
# ═════════════════════════════════════════════════════════════
def robots_sitemap(url: str) -> Dict:
    base = url.rstrip("/")
    sonuc = {
        "robots_txt": "",
        "sitemap_url": "",
        "sitemap_url_count": 0,
        "sitemap_spam_count": 0,
        "sitemap_spam_urls_sample": [],
    }

    # robots.txt
    r = _safe_get(f"{base}/robots.txt")
    if r and r.status_code == 200:
        sonuc["robots_txt"] = r.text[:2000]
        m = re.search(r'Sitemap:\s*(\S+)', r.text, re.IGNORECASE)
        if m: sonuc["sitemap_url"] = m.group(1).strip()

    # Sitemap fallback
    if not sonuc["sitemap_url"]:
        for path in ["/wp-sitemap.xml", "/sitemap.xml", "/sitemap_index.xml"]:
            test = _safe_get(f"{base}{path}")
            if test and test.status_code == 200 and "<url" in test.text:
                sonuc["sitemap_url"] = f"{base}{path}"
                break

    # Sitemap parse + spam tarama
    if sonuc["sitemap_url"]:
        # Index'ten alt sitemap'leri çek
        r = _safe_get(sonuc["sitemap_url"])
        if r and r.status_code == 200:
            text = r.text
            sub_sitemaps = re.findall(r'<loc>([^<]+\.xml[^<]*)</loc>', text)
            urls_to_scan = sub_sitemaps if sub_sitemaps else [sonuc["sitemap_url"]]

            all_urls = []
            for sm in urls_to_scan[:8]:  # max 8 alt sitemap
                rr = _safe_get(sm)
                if rr and rr.status_code == 200:
                    found = re.findall(r'<loc>(https?://[^<]+)</loc>', rr.text)
                    # Sadece sayfa URL'leri (alt sitemap'leri tekrar alma)
                    found = [u for u in found if not u.endswith(".xml")]
                    all_urls.extend(found)

            sonuc["sitemap_url_count"] = len(all_urls)
            spam_urls = []
            for u in all_urls:
                ul = u.lower()
                for sk in SPAM_KEYWORDS:
                    if sk in ul:
                        spam_urls.append(u)
                        break
            sonuc["sitemap_spam_count"] = len(spam_urls)
            sonuc["sitemap_spam_urls_sample"] = spam_urls[:10]

    return sonuc


# ═════════════════════════════════════════════════════════════
# 5. GOOGLE PLACES (firma + rakipler)
# ═════════════════════════════════════════════════════════════
def _domain_to_isim(domain: str) -> str:
    """Domain'den okunabilir firma adı türet: skyimport.eu → 'Sky Import'."""
    if not domain:
        return ""
    ad = re.split(r"[./]", domain)[0]
    ad = re.sub(r"^(www|web)", "", ad)
    ad = re.sub(r"[-_]+", " ", ad)
    ad = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", ad)
    parca = re.findall(r"[a-z]+|[A-Z][a-z]*|\d+", ad)
    return " ".join(p.capitalize() for p in parca if p).strip()


def _places_textsearch(query: str, api_key: str) -> Dict:
    """Tek bir textsearch sorgusu çalıştır, ilk makul sonucu döndür."""
    if not query.strip():
        return {}
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    try:
        r = requests.get(url, params={"query": query, "key": api_key, "language": "tr"},
                         timeout=15)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"  ⚠ Places sorgu hatası ({query}): {e}")
        return {}
    results = data.get("results", [])
    if not results:
        return {}
    first = results[0]
    loc = first.get("geometry", {}).get("location", {})
    return {
        "name":          first.get("name"),
        "place_id":      first.get("place_id"),
        "address":       first.get("formatted_address"),
        "rating":        first.get("rating"),
        "user_ratings_total": first.get("user_ratings_total"),
        "lat":           loc.get("lat"),
        "lng":           loc.get("lng"),
        "types":         first.get("types", []),
        "opening_hours": first.get("opening_hours", {}),
    }


def places_firma_bul(firma_adi: str, sehir_ipucu: str, api_key: str,
                     domain: str = "") -> Dict:
    """Firma adı + domain + şehir ile sırayla birden fazla arama dener,
    ilk bulunanı döndürür. Katı isim eşleştirmesi yapmaz."""
    domain_isim = _domain_to_isim(domain)

    # Sırayla denenecek sorgular (ilk bulunan kazanır)
    adaylar = [
        f"{firma_adi} {sehir_ipucu}",      # title + şehir
        firma_adi,                          # sadece title
        f"{domain_isim} {sehir_ipucu}",     # domain ismi + şehir
        domain_isim,                        # sadece domain ismi
        sehir_ipucu and f"{domain_isim} Österreich",  # geniş: domain + ülke
    ]

    denenen = []
    for q in adaylar:
        q = (q or "").strip()
        if not q or q in denenen:
            continue
        denenen.append(q)
        sonuc = _places_textsearch(q, api_key)
        if sonuc.get("place_id"):
            print(f"  ✓ Places bulundu: '{q}' → {sonuc.get('name')}")
            return sonuc

    print(f"  ⚠ Places: hiçbir sorgu sonuç vermedi. Denenen: {denenen}")
    return {}


# ═════════════════════════════════════════════════════════════
# ANA FONKSİYON
# ═════════════════════════════════════════════════════════════
def veri_topla(url: str, psi_key: str, places_key: str = "",
               firma_adi_ipucu: str = "", sehir_ipucu: str = "") -> Dict:
    """
    URL'den tüm veriyi toplar.
    
    Returns: Açık Karne için hazır veri sözlüğü.
    """
    url = _normalize_url(url)
    domain = _domain(url)
    print(f"\n▸ Veri toplama başladı: {url}")

    veri = {
        "url": url,
        "domain": domain,
        "tarih": datetime.now().strftime("%d %B %Y"),
        "tarih_iso": datetime.now().isoformat(),
    }

    # 1. HTML anasayfa
    print("  1/6  HTML kaynak çekiliyor...")
    r = _safe_get(url, timeout=20)
    html = r.text if r and r.status_code == 200 else ""
    veri["html_analysis"] = html_analiz(html)
    veri["http_status"] = r.status_code if r else 0

    # 2. HTTP headers
    print("  2/6  HTTP headers...")
    veri["headers"] = header_analiz(url)

    # 3. robots.txt + sitemap
    print("  3/6  robots.txt + sitemap (spam taraması)...")
    veri["robots_sitemap"] = robots_sitemap(url)

    # 4. PSI mobile
    print("  4/6  PageSpeed Insights (mobile)...")
    veri["psi_mobile"] = psi_olc(url, psi_key, "mobile") if psi_key else {}

    # 5. PSI desktop
    print("  5/6  PageSpeed Insights (desktop)...")
    veri["psi_desktop"] = psi_olc(url, psi_key, "desktop") if psi_key else {}

    # 6. Places (firma + ipucu)
    print("  6/6  Google Places...")
    firma_adi_kullan = firma_adi_ipucu or veri["html_analysis"].get("title", "").split("|")[0].split("–")[0].strip()
    sehir_kullan = sehir_ipucu or sehir_html_cikar(html) or "Österreich"
    veri["lokasyon_ipucu"] = sehir_kullan
    veri["places_firma"] = places_firma_bul(firma_adi_kullan, sehir_kullan, places_key, domain) if places_key else {}

    # Hack tespit özet
    spam_kw = veri["html_analysis"]["hack_signals"]["spam_keywords_found"]
    cloaking = veri["html_analysis"]["hack_signals"]["cloaking_detected"]
    spam_sitemap = veri["robots_sitemap"]["sitemap_spam_count"]
    veri["hack_summary"] = {
        "is_hacked": bool(spam_kw) and (cloaking or spam_sitemap > 0),
        "html_spam_keywords": spam_kw,
        "cloaking_in_html": cloaking,
        "sitemap_spam_count": spam_sitemap,
        "severity": "DURDURUCU" if (cloaking or spam_sitemap > 5) else
                    "ORTA" if spam_kw else "TEMİZ",
    }

    print(f"  ✓ Veri toplama bitti.\n")
    return veri


# ─── DEMO ───
if __name__ == "__main__":
    import sys
    psi_key = os.environ.get("PSI_KEY", "")
    places_key = os.environ.get("PLACES_KEY", "")
    test_url = sys.argv[1] if len(sys.argv) > 1 else "https://www.liftsanmakine.com"

    veri = veri_topla(test_url, psi_key, places_key)
    print(json.dumps(
        {k: v for k, v in veri.items() if k != "html_analysis"},
        indent=2, ensure_ascii=False, default=str
    )[:3000])
    print("...")
    print("\nHTML özet:")
    h = veri["html_analysis"]
    print(f"  Title: {h.get('title', '')[:80]}")
    print(f"  Meta desc: {bool(h.get('meta_description'))}")
    print(f"  H1 count: {h.get('h1_count')}")
    print(f"  Schema blocks: {h.get('schema_blocks')}")
    print(f"  Schema types: {h.get('schema_types')}")
    print(f"  Hreflang: {h.get('hreflang_tags')}")
    print(f"  Stack: {[k for k,v in h.get('stack', {}).items() if v]}")
    print(f"  Analytics: {[k for k,v in h.get('analytics', {}).items() if v]}")
    print(f"  Hack: {veri['hack_summary']['severity']}")


def sehir_html_cikar(html: str) -> str:
    """HTML'den 'PLZ Sehir' paternini cikarir (orn. '6800 Feldkirch').
    Bulamazsa bos doner."""
    import re as _re
    from collections import Counter
    if not html:
        return ""
    eslesme = _re.findall(r'\b([0-9]{4})\s+([A-ZAOU][a-zaouA-ZAOU\.\- ]{2,30})', html)
    if not eslesme:
        return ""
    sayac = Counter(f"{plz} {sehir.strip()}" for plz, sehir in eslesme)
    return sayac.most_common(1)[0][0]
