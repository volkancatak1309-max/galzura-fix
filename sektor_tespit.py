"""
GALZURA SEKTÖR TESPİT
═══════════════════════════════════════════════════════════════════════════════
HTML içeriği, sayfa başlığı, meta description, GMB kategorisi ve URL'den
sektörü otomatik tespit eder.

Desteklenen sektörler:
  restoran, insaat, saglik, otomotiv, hukuk, beauty, egitim, eticaret,
  uretici (B2B/sanayi), general (varsayılan)
═══════════════════════════════════════════════════════════════════════════════
"""
import re
from typing import Dict


SEKTOR_KEYWORDS = {
    "restoran": {
        "html_tr": ["restoran", "lokanta", "döner", "kebap", "kebab", "pide", "lahmacun",
                    "menü", "yemek", "rezervasyon", "sipariş", "mutfak", "şef",
                    "tatlı", "kahvaltı", "mezeler"],
        "html_de": ["restaurant", "speisekarte", "küche", "menü", "döner", "kebab",
                    "reservierung", "essen", "frühstück", "imbiss", "bistro"],
        "html_en": ["restaurant", "menu", "cuisine", "reservation", "dining",
                    "kebab", "doner", "food", "chef", "bistro", "eatery"],
        "gmb_kategoriler": ["restaurant", "kebab_shop", "turkish_restaurant",
                            "food", "meal_takeaway", "bakery", "pizza_restaurant",
                            "fast_food_restaurant", "cafe"],
        "url_patterns": ["restaurant", "bistro", "kebab", "döner", "yemek",
                         "mutfak", "essen"],
    },
    "insaat": {
        "html_tr": ["inşaat", "yapı", "müteahhit", "tadilat", "boya", "elektrik",
                    "tesisat", "izolasyon", "çatı", "renovasyon", "betonarme",
                    "kaba inşaat", "ince işler"],
        "html_de": ["bau", "renovierung", "umbau", "sanierung", "tiefbau",
                    "hochbau", "spengler", "spengler", "dachdecker", "bauunternehmen",
                    "bauarbeiter", "bauleitung"],
        "html_en": ["construction", "renovation", "building", "contractor",
                    "remodeling", "roofing", "plumbing", "electrical"],
        "gmb_kategoriler": ["general_contractor", "construction_company",
                            "building_consultant", "remodeler", "roofing_contractor",
                            "electrician", "plumber"],
        "url_patterns": ["bau", "construction", "insaat", "yapi", "renovate"],
    },
    "saglik": {
        "html_tr": ["diş", "dişçi", "doktor", "klinik", "hasta", "implant",
                    "tedavi", "muayene", "estetik", "dental", "ortodonti",
                    "diş hekimi", "randevu", "poliklinik", "ameliyat"],
        "html_de": ["zahnarzt", "klinik", "praxis", "patient", "behandlung",
                    "implantat", "dental", "dentist", "arzt", "termin"],
        "html_en": ["dentist", "clinic", "dental", "patient", "treatment",
                    "implant", "doctor", "physician", "appointment", "medical"],
        "gmb_kategoriler": ["dentist", "dental_clinic", "doctor", "medical_clinic",
                            "hospital", "physiotherapist", "pharmacy"],
        "url_patterns": ["dental", "dis", "klinik", "doktor", "saglik", "zahn"],
    },
    "otomotiv": {
        "html_tr": ["araç", "otomobil", "kiralık", "galeri", "satış", "model",
                    "motor", "yedek parça", "lastik", "servis", "tamir",
                    "marka", "vites", "yakıt"],
        "html_de": ["fahrzeug", "auto", "vermietung", "mieten", "händler",
                    "marke", "modell", "motor", "ersatzteile", "werkstatt"],
        "html_en": ["car", "vehicle", "rental", "luxury", "sport", "model",
                    "engine", "spare parts", "service", "garage"],
        "gmb_kategoriler": ["car_dealer", "car_rental", "auto_repair_shop",
                            "car_wash", "gas_station", "luxury_car_dealer"],
        "url_patterns": ["car", "auto", "vermietung", "rental", "vehicle",
                         "motor", "oto"],
    },
    "hukuk": {
        "html_tr": ["avukat", "hukuk", "dava", "müvekkil", "yasal", "danışmanlık",
                    "tazminat", "ceza", "ticaret hukuku", "iş hukuku", "boşanma"],
        "html_de": ["anwalt", "rechtsanwalt", "kanzlei", "mandant", "recht",
                    "scheidung", "strafrecht", "arbeitsrecht"],
        "html_en": ["lawyer", "attorney", "law firm", "legal", "litigation",
                    "client", "criminal", "divorce", "consultation"],
        "gmb_kategoriler": ["lawyer", "law_firm", "legal_services", "notary",
                            "attorney"],
        "url_patterns": ["law", "legal", "anwalt", "avukat", "hukuk", "kanzlei"],
    },
    "beauty": {
        "html_tr": ["güzellik", "estetik", "saç", "cilt", "lazer", "epilasyon",
                    "manikür", "pedikür", "makyaj", "spa", "masaj", "tırnak",
                    "kuaför", "berber"],
        "html_de": ["schönheit", "kosmetik", "friseur", "haare", "haut",
                    "wimpern", "nägel", "spa", "wellness", "massage"],
        "html_en": ["beauty", "salon", "spa", "hair", "skin", "nails",
                    "makeup", "facial", "massage", "wellness"],
        "gmb_kategoriler": ["beauty_salon", "hair_salon", "barber_shop",
                            "spa", "nail_salon", "wellness_center"],
        "url_patterns": ["beauty", "salon", "spa", "guzellik", "estetik",
                         "kuafor", "friseur"],
    },
    "egitim": {
        "html_tr": ["kurs", "eğitim", "okul", "üniversite", "ders", "öğrenci",
                    "öğretmen", "sertifika", "akademi", "dershane", "tus", "lgs",
                    "ales", "yds", "yks"],
        "html_de": ["schule", "kurs", "ausbildung", "unterricht", "lehrer",
                    "schüler", "universität", "akademie", "weiterbildung"],
        "html_en": ["school", "course", "training", "education", "academy",
                    "student", "teacher", "certificate", "tutorial", "lesson"],
        "gmb_kategoriler": ["school", "education", "training_center",
                            "language_school", "university", "tutoring_service"],
        "url_patterns": ["school", "kurs", "academy", "egitim", "kurs",
                         "training"],
    },
    "eticaret": {
        "html_tr": ["mağaza", "satın al", "sepet", "ürün", "kargo", "indirim",
                    "kampanya", "stok", "ödeme", "online alışveriş"],
        "html_de": ["shop", "kaufen", "warenkorb", "produkt", "versand",
                    "rabatt", "lager", "bezahlung"],
        "html_en": ["shop", "buy", "cart", "product", "shipping", "discount",
                    "stock", "checkout", "online store", "ecommerce"],
        "gmb_kategoriler": ["store", "online_store", "shop", "shopping_mall",
                            "retail"],
        "url_patterns": ["shop", "store", "buy", "magaza", "ecommerce"],
    },
    "uretici": {
        "html_tr": ["üretici", "imalat", "fabrika", "endüstriyel", "sanayi",
                    "ihracat", "b2b", "yedek parça", "makina", "ekipman",
                    "tedarikçi", "OEM"],
        "html_de": ["hersteller", "produktion", "fertigung", "industrie",
                    "export", "lieferant", "ersatzteile", "maschinen",
                    "sonnenschutz", "pergola", "markise", "markisen",
                    "wintergarten", "fliegengitter", "rollladen", "beschattung",
                    "terrassendach", "import"],
        "html_en": ["manufacturer", "production", "industrial", "export",
                    "supplier", "spare parts", "machinery", "equipment", "B2B",
                    "OEM"],
        "gmb_kategoriler": ["manufacturer", "factory", "industrial_equipment_supplier",
                            "machinery_parts_supplier", "wholesaler"],
        "url_patterns": ["manufacturer", "industrial", "machinery", "parts",
                         "supplier", "uretici", "imalat"],
    },
}


SEKTOR_ETIKETLERI = {
    "restoran":  "Restoran / Yemek Hizmetleri",
    "insaat":    "İnşaat / Yapı",
    "saglik":    "Sağlık / Klinik",
    "otomotiv":  "Otomotiv / Araç",
    "hukuk":     "Hukuk Bürosu",
    "beauty":    "Güzellik / Estetik",
    "egitim":    "Eğitim / Kurs",
    "eticaret":  "E-Ticaret",
    "uretici":   "Üretici / B2B Sanayi",
    "general":   "Genel",
}


def sektor_tespit(
    html: str = "",
    title: str = "",
    meta_description: str = "",
    url: str = "",
    gmb_kategoriler: list = None,
) -> Dict:
    """
    Verilen verilerden sektörü tespit eder.
    Returns: {
        "sektor": "restoran",       # kod
        "etiket": "Restoran ...",   # gösterim adı
        "skor_dagilimi": {...},     # her sektör için puan (debug için)
        "kaynak": "gmb + html"      # neye dayanarak karar verildi
    }
    """
    if gmb_kategoriler is None:
        gmb_kategoriler = []

    # Tüm metni birleştir ve küçült
    full_text = (
        (html or "") + " " + (title or "") + " " +
        (meta_description or "") + " " + (url or "")
    ).lower()

    skorlar = {}
    secim_kaynagi = []

    for sektor, keywords in SEKTOR_KEYWORDS.items():
        puan = 0

        # GMB kategorisi (en güçlü sinyal — 50 puan/eşleşme)
        for kat in gmb_kategoriler:
            if kat in keywords["gmb_kategoriler"]:
                puan += 50
                secim_kaynagi.append(f"GMB '{kat}' → {sektor}")

        # URL pattern (orta sinyal — 30 puan/eşleşme)
        for pattern in keywords["url_patterns"]:
            if pattern in (url or "").lower():
                puan += 30

        # HTML keyword'leri (her dil için)
        for lang_key in ["html_tr", "html_de", "html_en"]:
            for kw in keywords[lang_key]:
                # Tam kelime eşleşmesi (kelime sınırları)
                count = len(re.findall(r'\b' + re.escape(kw) + r'\b', full_text))
                if count > 0:
                    puan += min(count * 2, 20)  # max 20 puan/keyword

        skorlar[sektor] = puan

    # En yüksek skor
    en_yuksek = max(skorlar.items(), key=lambda x: x[1])

    # Eşik kontrolü: en az 20 puan olmalı, yoksa general
    if en_yuksek[1] < 20:
        return {
            "sektor": "general",
            "etiket": SEKTOR_ETIKETLERI["general"],
            "skor_dagilimi": skorlar,
            "kaynak": "Yetersiz sinyal · varsayılan",
        }

    return {
        "sektor": en_yuksek[0],
        "etiket": SEKTOR_ETIKETLERI[en_yuksek[0]],
        "skor_dagilimi": skorlar,
        "kaynak": " · ".join(secim_kaynagi[:3]) if secim_kaynagi else "HTML keyword analizi",
    }


# ─── DEMO ───
if __name__ == "__main__":
    # Test 1: Dogan's Bistro
    sonuc = sektor_tespit(
        html="Anatolische / Orientalische Wärme mit mediterraner Genuß Döner Kebap Dürüm Lahmacun",
        title="Dogan's Bistro",
        url="https://dogans.sumupstore.com/",
        gmb_kategoriler=["kebab_shop", "restaurant"],
    )
    print("Test 1 (Dogan's Bistro):")
    print(f"  → {sonuc['sektor']} ({sonuc['etiket']})")
    print(f"  → Kaynak: {sonuc['kaynak']}")
    print()

    # Test 2: Liftsan Machinery
    sonuc = sektor_tespit(
        html="Liftsan Machinery PREMIUM PARTS FOR HYDRAULIC BREAKERS manufacturer industrial spare parts",
        title="Liftsan Machinery – PREMIUM PARTS FOR HYDRAULIC BREAKERS",
        url="https://www.liftsanmakine.com/",
        gmb_kategoriler=["manufacturer"],
    )
    print("Test 2 (Liftsan Machinery):")
    print(f"  → {sonuc['sektor']} ({sonuc['etiket']})")
    print(f"  → Kaynak: {sonuc['kaynak']}")
    print()

    # Test 3: Pikens Sportwagen
    sonuc = sektor_tespit(
        html="Premium Sportwagen Luxus SUV Auto Vermietung Lamborghini Mercedes BMW Porsche",
        title="Piken's | Premium Sportwagen & Luxus-SUVs",
        url="https://pikens-sportwagenvermietung.vercel.app",
        gmb_kategoriler=["car_rental"],
    )
    print("Test 3 (Pikens Sportwagen):")
    print(f"  → {sonuc['sektor']} ({sonuc['etiket']})")
    print(f"  → Kaynak: {sonuc['kaynak']}")
