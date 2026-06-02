"""
GALZURA PRESTIGE REPORT — 8 Sayfa Premium PDF Builder
═══════════════════════════════════════════════════════════════════════════════
Royal Opulence tasarım. AI dinamik içerik (Claude Sonnet 4.6).
Her veri satırının yanında doğrulama linki.

pdf_verisi sözlüğü orchestrator'dan gelir, tüm AI metinleri hazır halde.
═══════════════════════════════════════════════════════════════════════════════
"""
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from reportlab.lib.units import mm
import os

FONT_DIR = "/usr/share/fonts/truetype/dejavu"
pdfmetrics.registerFont(TTFont("Serif",       f"{FONT_DIR}/DejaVuSerif.ttf"))
pdfmetrics.registerFont(TTFont("SerifBold",   f"{FONT_DIR}/DejaVuSerif-Bold.ttf"))
pdfmetrics.registerFont(TTFont("SerifItalic", f"{FONT_DIR}/DejaVuSerif-Italic.ttf"))
pdfmetrics.registerFont(TTFont("Sans",        f"{FONT_DIR}/DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("SansBold",    f"{FONT_DIR}/DejaVuSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("Mono",        f"{FONT_DIR}/DejaVuSansMono.ttf"))

NAVY  = HexColor("#0a1a4d")
GOLD  = HexColor("#c9a55c")
GOLD_LIGHT = HexColor("#e6d4a8")
INK   = HexColor("#0a0a0c")
CREAM = HexColor("#faf7f0")
GREY  = HexColor("#6b6b70")
GREY_LIGHT = HexColor("#d4d4d8")
GREY_BG = HexColor("#f8f7f3")
RED   = HexColor("#9b1c1c")
RED_BG = HexColor("#fbe9e9")
GREEN = HexColor("#2d5a2d")
GREEN_BG = HexColor("#eaf2ea")
AMBER = HexColor("#a86a1c")
AMBER_BG = HexColor("#fcf3e0")
BLUE  = HexColor("#1e3a8a")
BLUE_BG = HexColor("#e6edf9")

W, H = A4
MX = 18*mm
CW = W - 2*MX
TOTAL_PAGES = 8


def wrap(text, font, size, max_w):
    if not text:
        return [""]
    words = str(text).split()
    lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if pdfmetrics.stringWidth(test, font, size) <= max_w:
            cur = test
        else:
            if cur: lines.append(cur)
            cur = w
            while pdfmetrics.stringWidth(cur, font, size) > max_w:
                for i in range(len(cur), 0, -1):
                    if pdfmetrics.stringWidth(cur[:i], font, size) <= max_w:
                        lines.append(cur[:i]); cur = cur[i:]; break
                else:
                    break
    if cur: lines.append(cur)
    return lines


def onem_renk(onem):
    o = (onem or "").lower()
    if o in ("yuksek", "yüksek", "high"): return RED, RED_BG, "YÜKSEK"
    if o in ("orta", "medium"):           return AMBER, AMBER_BG, "ORTA"
    return GREY, GREY_BG, "DÜŞÜK"


def page_header(c, page_no, section, rapor_no):
    c.setFillColor(GREY); c.setFont("Sans", 7.5)
    c.drawString(MX, H - 12*mm, "GALZURA PRESTIGE REPORT")
    c.drawCentredString(W/2, H - 12*mm, section.upper())
    c.drawRightString(W - MX, H - 12*mm, f"{page_no:02d} / {TOTAL_PAGES:02d}")
    c.setStrokeColor(GOLD); c.setLineWidth(0.5)
    c.line(MX, H - 14*mm, W - MX, H - 14*mm)

def page_footer(c, rapor_no, tarih):
    c.setFillColor(GREY); c.setFont("Sans", 6.5)
    c.drawString(MX, 12*mm, "GALZURA INTELLIGENCE  ·  Premium Web & AI SEO Ajansı")
    c.drawRightString(W - MX, 12*mm, f"{rapor_no}  ·  {tarih}")
    c.setFont("SansBold", 6.5); c.setFillColor(GOLD)
    c.drawCentredString(W/2, 8*mm, "B U   B E L G E   K İ Ş İ Y E   Ö Z E L D İ R")

def section_title(c, y_top, roman, baslik, alt):
    c.setFillColor(GOLD); c.setFont("SansBold", 8)
    c.drawString(MX, y_top, f"BÖLÜM {roman}")
    c.setFillColor(NAVY); c.setFont("SerifBold", 22)
    c.drawString(MX, y_top - 8*mm, baslik)
    c.setFillColor(GREY); c.setFont("SerifItalic", 10)
    c.drawString(MX, y_top - 13*mm, alt)
    c.setStrokeColor(GOLD); c.setLineWidth(0.7)
    c.line(MX, y_top - 15*mm, MX + 40*mm, y_top - 15*mm)
    return y_top - 23*mm

def intro_paragraph(c, y, text):
    c.setFillColor(GREY); c.setFont("SerifItalic", 9.5)
    for ln in wrap(text, "SerifItalic", 9.5, CW):
        c.drawString(MX, y, ln); y -= 4*mm
    return y - 3*mm


# ═════════════════════════════════════════════════════════════
# SAYFA 1 — KAPAK
# ═════════════════════════════════════════════════════════════
def page_1(c, d):
    c.setFillColor(NAVY); c.rect(0, H - 100*mm, W, 100*mm, fill=1, stroke=0)
    c.setStrokeColor(GOLD); c.setLineWidth(0.6)
    c.rect(12*mm, 12*mm, W - 24*mm, H - 24*mm, fill=0, stroke=1)
    c.setLineWidth(0.3)
    c.rect(14*mm, 14*mm, W - 28*mm, H - 28*mm, fill=0, stroke=1)

    c.setFillColor(GOLD); c.setFont("SerifBold", 28)
    c.drawCentredString(W/2, H - 38*mm, "G A L Z U R A")
    c.setFillColor(CREAM); c.setFont("Sans", 7.5)
    c.drawCentredString(W/2, H - 44*mm,
                        "I N T E L L I G E N C E  ·  S T R A T E G Y  ·  V I S I O N")
    c.setStrokeColor(GOLD); c.setLineWidth(0.5)
    c.line(W/2 - 30*mm, H - 52*mm, W/2 + 30*mm, H - 52*mm)
    c.setFillColor(GOLD); c.setFont("Sans", 9)
    c.drawCentredString(W/2, H - 62*mm, "D İ J İ T A L   P E R F O R M A N S   A N A L İ Z İ")
    c.setFillColor(CREAM); c.setFont("SerifBold", 30)
    c.drawCentredString(W/2, H - 80*mm, "Prestige Report")
    c.setFillColor(GOLD); c.setFont("SerifItalic", 14)
    c.drawCentredString(W/2, H - 90*mm, "Dijital Sağlık Taraması")

    # 3 skor
    y_top = H - 128*mm
    box_w = (CW - 12*mm) / 3
    box_h = 48*mm
    skor = d["skor"]
    if skor < 40:   ana_col, ana_et = RED, "KRİTİK"
    elif skor < 65: ana_col, ana_et = AMBER, "GELİŞİM ALANI"
    else:           ana_col, ana_et = GREEN, "İYİ"
    boxes = [
        ("SİZİN SKORUNUZ", str(skor), ana_et, ana_col),
        ("SEKTÖR ORTALAMASI", str(d["sektor_skor"]), "ortalama", GREY),
        ("BÖLGE LİDERİ", str(d["lider_skor"]), d.get("lider_isim","lider")[:14], GREEN),
    ]
    for i, (lbl, num, et, col) in enumerate(boxes):
        bx = MX + i * (box_w + 6*mm)
        by = y_top - box_h
        c.setStrokeColor(col); c.setLineWidth(0.8)
        c.rect(bx, by, box_w, box_h, fill=0, stroke=1)
        c.setFillColor(col); c.setFont("SansBold", 7.5)
        c.drawCentredString(bx + box_w/2, by + box_h - 7*mm, lbl)
        c.setFillColor(INK); c.setFont("SerifBold", 36)
        c.drawCentredString(bx + box_w/2, by + box_h/2 - 4*mm, num)
        c.setFillColor(GREY); c.setFont("Sans", 8)
        c.drawCentredString(bx + box_w/2, by + 11*mm, "/ 100")
        c.setFillColor(col); c.setFont("SansBold", 8)
        c.drawCentredString(bx + box_w/2, by + 5*mm, et.upper())

    # AI skor yorumu (içeriğe göre yükseklik)
    y_a = y_top - box_h - 10*mm
    yorum_lines = wrap(d.get("skor_yorum",""), "SerifItalic", 10, CW - 16*mm)
    box_yorum_h = max(len(yorum_lines) * 4.2*mm + 12*mm, 24*mm)
    c.setFillColor(GREY_BG)
    c.rect(MX, y_a - box_yorum_h, CW, box_yorum_h, fill=1, stroke=0)
    c.setStrokeColor(GOLD); c.setLineWidth(0.3)
    c.line(MX, y_a, W - MX, y_a); c.line(MX, y_a - box_yorum_h, W - MX, y_a - box_yorum_h)
    c.setFillColor(GOLD); c.setFont("Sans", 7.5)
    c.drawCentredString(W/2, y_a - 6*mm, "D U R U M   Ö Z E T İ")
    c.setFillColor(INK); c.setFont("SerifItalic", 10)
    yy = y_a - 12*mm
    for ln in yorum_lines:
        c.drawCentredString(W/2, yy, ln); yy -= 4.2*mm

    # Meta
    y_meta = 42*mm
    c.setStrokeColor(GOLD); c.setLineWidth(0.4)
    c.rect(MX + 20*mm, y_meta - 28*mm, CW - 40*mm, 28*mm, fill=0, stroke=1)
    c.setFillColor(GOLD); c.setFont("Sans", 7)
    c.drawCentredString(W/2, y_meta - 6*mm, "H A Z I R L A N A N   F İ R M A")
    c.setFillColor(INK); c.setFont("SerifBold", 14)
    c.drawCentredString(W/2, y_meta - 13*mm, d["firma_adi"])
    c.setFillColor(GREY); c.setFont("SerifItalic", 9)
    c.drawCentredString(W/2, y_meta - 18.5*mm, d["lokasyon"])
    c.setFont("Sans", 8); c.setFillColor(GREY)
    c.drawCentredString(W/2, y_meta - 24*mm,
        f"Rapor No: {d['rapor_no']}   ·   Tarih: {d['tarih']}")


# ═════════════════════════════════════════════════════════════
# SAYFA 2 — İŞLETME VERİ KARTI
# ═════════════════════════════════════════════════════════════
def page_2(c, d):
    page_header(c, 2, "İşletme Veri Kartı", d["rapor_no"])
    y = section_title(c, H - 26*mm, "I", "İşletme Veri Kartı",
        "Google Places API canlı veri · Place ID ile doğrulanabilir")
    y = intro_paragraph(c, y,
        f"Aşağıdaki tüm bilgiler Google Places API üzerinden {d['tarih']} tarihinde "
        "canlı çekildi. Place ID kalıcı bir kimliktir; herhangi bir Google Maps "
        "istemcisinde doğrulanabilir.")

    c.setFillColor(NAVY); c.rect(MX, y - 6*mm, CW, 6*mm, fill=1, stroke=0)
    c.setFillColor(CREAM); c.setFont("SansBold", 8.5)
    c.drawString(MX + 3*mm, y - 4*mm, "ALAN")
    c.drawString(MX + 55*mm, y - 4*mm, f"DEĞER  (Places API · {d['tarih']})")
    y -= 6*mm

    for i, (alan, deger) in enumerate(d["veri_karti"]):
        if i % 2 == 0:
            c.setFillColor(GREY_BG); c.rect(MX, y - 6*mm, CW, 6*mm, fill=1, stroke=0)
        c.setFillColor(INK); c.setFont("SansBold", 9)
        c.drawString(MX + 3*mm, y - 4*mm, alan)
        c.setFillColor(INK); c.setFont("Sans", 9)
        deger_lines = wrap(deger, "Sans", 9, CW - 58*mm)[:1]
        c.drawString(MX + 55*mm, y - 4*mm, deger_lines[0] if deger_lines else "—")
        y -= 6*mm

    y -= 5*mm
    c.setFillColor(GREY_BG); c.rect(MX, y - 20*mm, CW, 20*mm, fill=1, stroke=0)
    c.setStrokeColor(GOLD); c.setLineWidth(0.4)
    c.line(MX, y, W - MX, y); c.line(MX, y - 20*mm, W - MX, y - 20*mm)
    c.setFillColor(GOLD); c.setFont("SansBold", 8)
    c.drawString(MX + 4*mm, y - 5*mm, "B A Ğ I M S I Z   D O Ğ R U L A M A")
    c.setFillColor(INK); c.setFont("Serif", 9)
    yy = y - 10*mm
    for ln in wrap(f"Google Maps açın → \"{d['firma_adi']} {d.get('sehir','')}\" arayın. "
                   "Yukarıdaki tüm veriler işletme profilinde aynen görünür.",
                   "Serif", 9, CW - 8*mm):
        c.drawString(MX + 4*mm, yy, ln); yy -= 3.8*mm

    page_footer(c, d["rapor_no"], d["tarih"])


# ═════════════════════════════════════════════════════════════
# SAYFA 3 — TEKNİK X-RAY (PSI + AI yorum)
# ═════════════════════════════════════════════════════════════
def page_3(c, d):
    page_header(c, 3, "Teknik Analiz", d["rapor_no"])
    y = section_title(c, H - 26*mm, "II", "Teknik Analiz",
        "Site hızı, yapısal veri, ölçüm altyapısı")
    y = intro_paragraph(c, y,
        "Aşağıdaki teknik veriler Google'ın kendi ölçüm araçlarından ve sitenizin "
        "kaynağından alındı. Her satırı sağdaki bağlantıdan kendiniz kontrol edebilirsiniz.")

    # Teknik tablo (veri + doğrulama linki)
    c.setFillColor(NAVY); c.rect(MX, y - 6*mm, CW, 6*mm, fill=1, stroke=0)
    c.setFillColor(CREAM); c.setFont("SansBold", 8)
    c.drawString(MX + 3*mm, y - 4*mm, "ÖLÇÜM")
    c.drawString(MX + 65*mm, y - 4*mm, "DEĞER")
    c.drawString(MX + 100*mm, y - 4*mm, "DOĞRULAMA")
    y -= 6*mm

    for i, row in enumerate(d["teknik_tablo"]):
        if i % 2 == 0:
            c.setFillColor(GREY_BG); c.rect(MX, y - 6*mm, CW, 6*mm, fill=1, stroke=0)
        c.setFillColor(INK); c.setFont("SansBold", 8.5)
        c.drawString(MX + 3*mm, y - 4*mm, row["olcum"])
        # değer renkli
        dr = row.get("durum","neutral")
        col = RED if dr=="fail" else GREEN if dr=="pass" else INK
        c.setFillColor(col); c.setFont("SansBold", 8.5)
        c.drawString(MX + 65*mm, y - 4*mm, row["deger"])
        c.setFillColor(BLUE); c.setFont("Mono", 6.5)
        link_lines = wrap(row.get("link",""), "Mono", 6.5, CW - 100*mm)[:1]
        c.drawString(MX + 100*mm, y - 4*mm, link_lines[0] if link_lines else "—")
        y -= 6*mm

    y -= 4*mm

    # AI teknik yorumlar
    c.setFillColor(GOLD); c.setFont("SansBold", 9)
    c.drawString(MX, y, "B U L G U L A R   N E   A N L A M A   G E L İ Y O R ?")
    y -= 6*mm
    for bulgu in d.get("teknik_yorumlar", [])[:5]:
        col, bg, et = onem_renk(bulgu.get("onem"))
        # ölçüm yüksekliği
        lines = wrap(bulgu.get("yorum",""), "Serif", 9, CW - 26*mm)
        bh = max(len(lines) * 4*mm + 7*mm, 13*mm)
        c.setFillColor(bg); c.rect(MX, y - bh, CW, bh, fill=1, stroke=0)
        c.setFillColor(col); c.rect(MX, y - bh, 1.2*mm, bh, fill=1, stroke=0)
        c.setFillColor(NAVY); c.setFont("SansBold", 9.5)
        bl = wrap(bulgu.get("baslik",""), "SansBold", 9.5, CW - 30*mm)[:1]; c.drawString(MX + 5*mm, y - 5*mm, bl[0] if bl else "")
        # önem chip
        c.setFillColor(col)
        cw_chip = pdfmetrics.stringWidth(et, "SansBold", 6.5) + 4*mm
        c.rect(W - MX - cw_chip - 3*mm, y - 6*mm, cw_chip, 3.5*mm, fill=1, stroke=0)
        c.setFillColor(CREAM); c.setFont("SansBold", 6.5)
        c.drawCentredString(W - MX - cw_chip/2 - 3*mm, y - 5*mm, et)
        c.setFillColor(INK); c.setFont("Serif", 9)
        ty = y - 9*mm
        for ln in lines:
            c.drawString(MX + 5*mm, ty, ln); ty -= 4*mm
        y -= bh + 2*mm

    page_footer(c, d["rapor_no"], d["tarih"])


# ═════════════════════════════════════════════════════════════
# SAYFA 4 — SEO EKSİKLERİ
# ═════════════════════════════════════════════════════════════
def page_4(c, d):
    page_header(c, 4, "SEO Analizi", d["rapor_no"])
    y = section_title(c, H - 26*mm, "III", "SEO Analizi",
        "Google'da görünürlük — eksikler ve güçlü yanlar")

    seo = d.get("seo", {})
    y = intro_paragraph(c, y, seo.get("ozet",
        "SEO analizi sitenin Google arama görünürlüğünü değerlendirir."))

    # Eksikler
    c.setFillColor(RED); c.setFont("SansBold", 9)
    c.drawString(MX, y, "▾  E K S İ K L E R")
    y -= 6*mm
    for item in seo.get("eksikler", [])[:5]:
        col, bg, et = onem_renk(item.get("oncelik"))
        lines = wrap(item.get("aciklama",""), "Serif", 9, CW - 12*mm)
        bh = max(len(lines)*4*mm + 7*mm, 13*mm)
        c.setFillColor(bg); c.rect(MX, y - bh, CW, bh, fill=1, stroke=0)
        c.setFillColor(col); c.rect(MX, y - bh, 1.2*mm, bh, fill=1, stroke=0)
        c.setFillColor(NAVY); c.setFont("SansBold", 9.5)
        kl = wrap(item.get("konu",""), "SansBold", 9.5, CW - 30*mm)[:1]; c.drawString(MX + 5*mm, y - 5*mm, kl[0] if kl else "")
        c.setFillColor(col)
        cw_chip = pdfmetrics.stringWidth(et, "SansBold", 6.5) + 4*mm
        c.rect(W - MX - cw_chip - 3*mm, y - 6*mm, cw_chip, 3.5*mm, fill=1, stroke=0)
        c.setFillColor(CREAM); c.setFont("SansBold", 6.5)
        c.drawCentredString(W - MX - cw_chip/2 - 3*mm, y - 5*mm, et)
        c.setFillColor(INK); c.setFont("Serif", 9)
        ty = y - 9*mm
        for ln in lines:
            c.drawString(MX + 5*mm, ty, ln); ty -= 4*mm
        y -= bh + 2*mm

    y -= 2*mm
    # Güçlü yanlar
    if seo.get("guclu_yanlar"):
        c.setFillColor(GREEN); c.setFont("SansBold", 9)
        c.drawString(MX, y, "▴  G Ü Ç L Ü   Y A N L A R")
        y -= 6*mm
        for item in seo.get("guclu_yanlar", [])[:3]:
            lines = wrap(item.get("aciklama",""), "Serif", 9, CW - 12*mm)
            bh = max(len(lines)*4*mm + 7*mm, 12*mm)
            c.setFillColor(GREEN_BG); c.rect(MX, y - bh, CW, bh, fill=1, stroke=0)
            c.setFillColor(GREEN); c.rect(MX, y - bh, 1.2*mm, bh, fill=1, stroke=0)
            c.setFillColor(NAVY); c.setFont("SansBold", 9.5)
            c.drawString(MX + 5*mm, y - 5*mm, item.get("konu",""))
            c.setFillColor(INK); c.setFont("Serif", 9)
            ty = y - 9*mm
            for ln in lines:
                c.drawString(MX + 5*mm, ty, ln); ty -= 4*mm
            y -= bh + 2*mm

    page_footer(c, d["rapor_no"], d["tarih"])


# ═════════════════════════════════════════════════════════════
# SAYFA 5 — GEO / AI GÖRÜNÜRLÜK
# ═════════════════════════════════════════════════════════════
def page_5(c, d):
    page_header(c, 5, "GEO / AI Görünürlük", d["rapor_no"])
    y = section_title(c, H - 26*mm, "IV", "GEO — Yapay Zeka Görünürlüğü",
        "ChatGPT, Gemini, Claude, Perplexity'de görünürlük")

    geo = d.get("geo", {})
    y = intro_paragraph(c, y, geo.get("ozet",
        "GEO analizi sitenin yapay zeka asistanlarında görünürlüğünü değerlendirir."))

    # Bilgi kutusu — GEO nedir
    c.setFillColor(BLUE_BG); c.rect(MX, y - 20*mm, CW, 20*mm, fill=1, stroke=0)
    c.setFillColor(BLUE); c.rect(MX, y - 20*mm, 1.2*mm, 20*mm, fill=1, stroke=0)
    c.setFillColor(BLUE); c.setFont("SansBold", 8)
    c.drawString(MX + 5*mm, y - 5*mm, "G E O   N E D İ R ?")
    c.setFillColor(INK); c.setFont("Serif", 9)
    yy = y - 10*mm
    for ln in wrap("Müşteriler artık \"en iyi X firma nerede?\" sorusunu Google yerine "
                   "ChatGPT/Gemini'ye soruyor. AI tek cevap veriyor — ya sizin adınız çıkar, "
                   "ya rakibin. GEO, AI'ların sizi tanıması için yapılan optimizasyondur.",
                   "Serif", 9, CW - 8*mm):
        c.drawString(MX + 5*mm, yy, ln); yy -= 3.8*mm
    y -= 25*mm

    # Engeller
    c.setFillColor(AMBER); c.setFont("SansBold", 9)
    c.drawString(MX, y, "A I   G Ö R Ü N Ü R L Ü Ğ Ü N Ü   E N G E L L E Y E N L E R")
    y -= 6*mm
    for eng in geo.get("engeller", [])[:4]:
        lines = wrap(eng.get("aciklama",""), "Serif", 9, CW - 12*mm)
        bh = max(len(lines)*4*mm + 7*mm, 12*mm)
        c.setFillColor(AMBER_BG); c.rect(MX, y - bh, CW, bh, fill=1, stroke=0)
        c.setFillColor(AMBER); c.rect(MX, y - bh, 1.2*mm, bh, fill=1, stroke=0)
        c.setFillColor(NAVY); c.setFont("SansBold", 9.5)
        el = wrap(eng.get("konu",""), "SansBold", 9.5, CW - 12*mm)[:1]; c.drawString(MX + 5*mm, y - 5*mm, el[0] if el else "")
        c.setFillColor(INK); c.setFont("Serif", 9)
        ty = y - 9*mm
        for ln in lines:
            c.drawString(MX + 5*mm, ty, ln); ty -= 4*mm
        y -= bh + 2*mm

    y -= 3*mm
    # Kendi test öneriniz
    test_s = geo.get("test_sorusu", geo.get("test_onerisi", ""))
    test_m = geo.get("test_mantik", "")
    box_h = 30*mm if test_m else 22*mm
    c.setFillColor(GREEN_BG); c.rect(MX, y - box_h, CW, box_h, fill=1, stroke=0)
    c.setFillColor(GREEN); c.rect(MX, y - box_h, 1.5*mm, box_h, fill=1, stroke=0)
    c.setFillColor(GREEN); c.setFont("SansBold", 9)
    c.drawString(MX + 5*mm, y - 5*mm, "K E N D İ N İ Z   T E S T   E D İ N   ( 3 0   S A N İ Y E )")
    c.setFillColor(INK); c.setFont("Serif", 9.5)
    yy = y - 11*mm
    c.setFont("Serif", 9)
    c.drawString(MX + 5*mm, yy, "ChatGPT veya Gemini'ye şunu sorun:")
    yy -= 5*mm
    c.setFillColor(NAVY); c.setFont("SerifBold", 10)
    for ln in wrap(f'"{test_s}"', "SerifBold", 10, CW - 12*mm)[:2]:
        c.drawString(MX + 7*mm, yy, ln); yy -= 4.5*mm
    if test_m:
        yy -= 1*mm
        c.setFillColor(INK); c.setFont("SerifItalic", 9)
        for ln in wrap("→ " + test_m, "SerifItalic", 9, CW - 12*mm)[:2]:
            c.drawString(MX + 5*mm, yy, ln); yy -= 4*mm

    page_footer(c, d["rapor_no"], d["tarih"])


# ═════════════════════════════════════════════════════════════
# SAYFA 6 — RAKİP AYNASI
# ═════════════════════════════════════════════════════════════
def page_6(c, d):
    page_header(c, 6, "Rakip Aynası", d["rapor_no"])
    y = section_title(c, H - 26*mm, "V", "Rakip Aynası",
        "Aynı bölgede yarıştığınız firmalar · Places API canlı")
    y = intro_paragraph(c, y,
        "Aşağıdaki rakipler Google Places API ile çekildi. Her satır işletme adıyla "
        "Google Maps'te doğrulanabilir.")

    cols_x = [MX + 3*mm, MX + 78*mm, MX + 100*mm, MX + 122*mm]
    c.setFillColor(NAVY); c.rect(MX, y - 6*mm, CW, 6*mm, fill=1, stroke=0)
    c.setFillColor(CREAM); c.setFont("SansBold", 8)
    for i, h in enumerate(["FİRMA", "PUAN", "YORUM", "ŞEHİR"]):
        c.drawString(cols_x[i], y - 4*mm, h)
    y -= 6*mm

    for i, row in enumerate(d["rakip_tablo"]):
        is_self = row.get("self", False)
        if is_self:
            c.setFillColor(GOLD_LIGHT); c.rect(MX, y - 5.5*mm, CW, 5.5*mm, fill=1, stroke=0)
        elif i % 2 == 0:
            c.setFillColor(GREY_BG); c.rect(MX, y - 5.5*mm, CW, 5.5*mm, fill=1, stroke=0)
        c.setFillColor(NAVY if is_self else INK)
        c.setFont("SansBold" if is_self else "Sans", 8.5)
        c.drawString(cols_x[0], y - 3.8*mm, row["isim"][:36])
        c.drawString(cols_x[1], y - 3.8*mm, row["puan"])
        c.drawString(cols_x[2], y - 3.8*mm, row["yorum"])
        c.drawString(cols_x[3], y - 3.8*mm, row["sehir"][:18])
        y -= 5.5*mm

    y -= 5*mm
    rakip = d.get("rakip_yorum", {})
    # AI yorumları
    for key, baslik, col, bg in [
        ("ozet", "DURUM", NAVY, GREY_BG),
        ("firsat", "FIRSAT", GREEN, GREEN_BG),
        ("risk", "RİSK", RED, RED_BG),
    ]:
        txt = rakip.get(key, "")
        if not txt: continue
        lines = wrap(txt, "Serif", 9.5, CW - 10*mm)
        bh = max(len(lines)*4.2*mm + 7*mm, 13*mm)
        c.setFillColor(bg); c.rect(MX, y - bh, CW, bh, fill=1, stroke=0)
        c.setFillColor(col); c.rect(MX, y - bh, 1.2*mm, bh, fill=1, stroke=0)
        c.setFillColor(col); c.setFont("SansBold", 9)
        c.drawString(MX + 5*mm, y - 5*mm, baslik)
        c.setFillColor(INK); c.setFont("Serif", 9.5)
        ty = y - 10*mm
        for ln in lines:
            c.drawString(MX + 5*mm, ty, ln); ty -= 4.2*mm
        y -= bh + 2*mm

    page_footer(c, d["rapor_no"], d["tarih"])


# ═════════════════════════════════════════════════════════════
# SAYFA 7 — ÇÖZÜM YOLU
# ═════════════════════════════════════════════════════════════
def page_7(c, d):
    page_header(c, 7, "Çözüm Yolu", d["rapor_no"])
    y = section_title(c, H - 26*mm, "VI", "Galzura Çözüm Yolu",
        "Bu firmaya özel, önceliklendirilmiş yol haritası")

    cozum = d.get("cozum", {})
    y = intro_paragraph(c, y, cozum.get("ozet",
        "Aşağıdaki adımlar firmanızın tespit edilen eksiklerine göre önceliklendirilmiştir."))

    # Öncelikli adımlar
    for i, adim in enumerate(cozum.get("oncelikli_adimlar", [])[:6]):
        neden = adim.get("neden","")
        lines = wrap(neden, "Serif", 9, CW - 22*mm)
        bh = max(len(lines)*4*mm + 9*mm, 15*mm)
        c.setFillColor(GREY_BG); c.rect(MX, y - bh, CW, bh, fill=1, stroke=0)
        c.setStrokeColor(GOLD); c.setLineWidth(0.4)
        c.rect(MX, y - bh, CW, bh, fill=0, stroke=1)
        # numara dairesi
        c.setFillColor(GOLD); c.circle(MX + 8*mm, y - 7*mm, 4*mm, fill=1, stroke=0)
        c.setFillColor(CREAM); c.setFont("SansBold", 11)
        c.drawCentredString(MX + 8*mm, y - 8.5*mm, str(i+1))
        c.setFillColor(NAVY); c.setFont("SansBold", 10)
        baslik_lines = wrap(adim.get("adim",""), "SansBold", 10, CW - 20*mm)[:1]
        c.drawString(MX + 16*mm, y - 6*mm, baslik_lines[0] if baslik_lines else "")
        c.setFillColor(INK); c.setFont("Serif", 9)
        ty = y - 11*mm
        for ln in lines:
            c.drawString(MX + 16*mm, ty, ln); ty -= 4*mm
        y -= bh + 2*mm

    y -= 3*mm
    # Beklenti
    c.setFillColor(AMBER_BG); c.rect(MX, y - 22*mm, CW, 22*mm, fill=1, stroke=0)
    c.setFillColor(AMBER); c.rect(MX, y - 22*mm, 1.5*mm, 22*mm, fill=1, stroke=0)
    c.setFillColor(AMBER); c.setFont("SansBold", 9)
    c.drawString(MX + 5*mm, y - 5*mm, "G E R Ç E K Ç İ   B E K L E N T İ")
    c.setFillColor(INK); c.setFont("Serif", 9.5)
    yy = y - 10*mm
    for ln in wrap(cozum.get("beklenti",
                   "SEO ve GEO kalıcı sonuç için zaman ister. Aylık raporlarla ilerleme gösterilir."),
                   "Serif", 9.5, CW - 10*mm):
        c.drawString(MX + 5*mm, yy, ln); yy -= 4.2*mm

    page_footer(c, d["rapor_no"], d["tarih"])


# ═════════════════════════════════════════════════════════════
# SAYFA 8 — METODOLOJİ + DOĞRULAMA
# ═════════════════════════════════════════════════════════════
def page_8(c, d):
    page_header(c, 8, "Metodoloji & Doğrulama", d["rapor_no"])
    y = section_title(c, H - 26*mm, "VII", "Metodoloji & Doğrulama",
        "Bu raporun her verisi bağımsız doğrulanabilir")
    y = intro_paragraph(c, y,
        "Galzura'nın temel ilkesi: müşteri her ölçümü bağımsız doğrulayabilmeli. "
        "Aşağıda verilerin kaynağı ve doğrulama yöntemi listelenir.")

    # Kaynak tablosu
    cols_x = [MX + 3*mm, MX + 45*mm, MX + 100*mm]
    c.setFillColor(NAVY); c.rect(MX, y - 6*mm, CW, 6*mm, fill=1, stroke=0)
    c.setFillColor(CREAM); c.setFont("SansBold", 8)
    c.drawString(cols_x[0], y - 4*mm, "VERİ TÜRÜ")
    c.drawString(cols_x[1], y - 4*mm, "KAYNAK")
    c.drawString(cols_x[2], y - 4*mm, "DOĞRULAMA")
    y -= 6*mm

    for i, row in enumerate(d["metodoloji"]):
        if i % 2 == 0:
            c.setFillColor(GREY_BG); c.rect(MX, y - 6*mm, CW, 6*mm, fill=1, stroke=0)
        c.setFillColor(NAVY); c.setFont("SansBold", 7.5)
        c.drawString(cols_x[0], y - 4*mm, row[0])
        c.setFillColor(INK); c.setFont("Sans", 7.5)
        c.drawString(cols_x[1], y - 4*mm, row[1])
        c.setFillColor(BLUE); c.setFont("Mono", 6.5)
        ll = wrap(row[2], "Mono", 6.5, CW - 100*mm)[:1]
        c.drawString(cols_x[2], y - 4*mm, ll[0] if ll else "—")
        y -= 6*mm

    y -= 5*mm
    # SİZ DE ÖLÇÜN
    c.setFillColor(AMBER_BG); c.rect(MX, y - 32*mm, CW, 32*mm, fill=1, stroke=0)
    c.setFillColor(AMBER); c.rect(MX, y - 32*mm, 1.5*mm, 32*mm, fill=1, stroke=0)
    c.setFillColor(AMBER); c.setFont("SansBold", 9)
    c.drawString(MX + 5*mm, y - 5*mm, "S İ Z   D E   Ö L Ç Ü N  —  3 0   S A N İ Y E")
    c.setFillColor(INK); c.setFont("Mono", 8)
    yy = y - 11*mm
    for m in d["dogrulama_linkleri"][:5]:
        c.drawString(MX + 5*mm, yy, m); yy -= 4.2*mm

    y -= 37*mm
    # Şeffaflık prensibi
    c.setFillColor(GREY_BG); c.rect(MX, y - 20*mm, CW, 20*mm, fill=1, stroke=0)
    c.setStrokeColor(GOLD); c.setLineWidth(0.4)
    c.line(MX, y, W - MX, y); c.line(MX, y - 20*mm, W - MX, y - 20*mm)
    c.setFillColor(GOLD); c.setFont("SansBold", 8)
    c.drawString(MX + 4*mm, y - 5*mm, "Ş E F F A F L I K   P R E N S İ B İ")
    c.setFillColor(INK); c.setFont("SerifItalic", 9)
    yy = y - 10*mm
    for ln in wrap("Galzura, müşterinin her ölçümü bağımsız doğrulayabileceği bir "
                   "metodoloji kullanır. Skor formülü gizli değildir. Bu rapor için ham "
                   "veri talebiniz halinde paylaşılır.", "SerifItalic", 9, CW - 8*mm):
        c.drawString(MX + 4*mm, yy, ln); yy -= 3.8*mm

    page_footer(c, d["rapor_no"], d["tarih"])


# ─── BUILD ──────────────────────────────────────────────────
def build(d, output_path):
    c = canvas.Canvas(output_path, pagesize=A4)
    c.setTitle(f"Galzura Prestige Report — {d['firma_adi']}")
    c.setAuthor("Galzura Intelligence")
    c.setSubject(d["rapor_no"])
    c.setCreator("Galzura Prestige Report — AI Powered")

    page_1(c, d); c.showPage()
    page_2(c, d); c.showPage()
    page_3(c, d); c.showPage()
    page_4(c, d); c.showPage()
    page_5(c, d); c.showPage()
    if len(d.get("rakip_tablo", [])) >= 2:
        page_6(c, d); c.showPage()
    page_7(c, d); c.showPage()
    page_8(c, d); c.showPage()

    c.save()
    return output_path
