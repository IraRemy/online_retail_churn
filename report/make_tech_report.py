"""Build the PDF technical report: report/Online_Retail_Technical_Report.pdf

Every number is read from outputs/ or recomputed from data/processed/ with the
project's own code, so the report stays in sync after `python run_all.py`.

    python report/make_tech_report.py
"""
import json
import sys
from pathlib import Path

import pandas as pd
from reportlab.graphics.shapes import Drawing, Line, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, Image, KeepTogether,
                                NextPageTemplate, PageBreak, PageTemplate,
                                Paragraph, Spacer, Table, TableStyle)
from reportlab.platypus.tableofcontents import TableOfContents

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
ASSETS = ROOT / "report" / "assets"
OUT = ROOT / "outputs"
PDF = ROOT / "report" / "Online_Retail_Technical_Report.pdf"

AUTHOR = ""          # e.g. "Your Name - Student ID"; left blank = not printed
REPORT_DATE = "November 2026"

# ---------------------------------------------------------------- palette
WINE = colors.HexColor("#421A30")
BERRY = colors.HexColor("#C0507C")
INK = colors.HexColor("#33202C")
MUTED = colors.HexColor("#6B5B66")
GREY = colors.HexColor("#8A8A93")
GOLD = colors.HexColor("#C98A2D")
TINT = colors.HexColor("#F7F1F4")
RULE = colors.HexColor("#EADDE3")

# ---------------------------------------------------------------- fonts
FONT_DIR = Path("C:/Windows/Fonts")
try:
    pdfmetrics.registerFont(TTFont("Body", str(FONT_DIR / "calibri.ttf")))
    pdfmetrics.registerFont(TTFont("Body-Bold", str(FONT_DIR / "calibrib.ttf")))
    pdfmetrics.registerFont(TTFont("Body-Italic", str(FONT_DIR / "calibrii.ttf")))
    pdfmetrics.registerFont(TTFont("Body-BoldItalic", str(FONT_DIR / "calibriz.ttf")))
    pdfmetrics.registerFontFamily("Body", normal="Body", bold="Body-Bold",
                                  italic="Body-Italic", boldItalic="Body-BoldItalic")
    BODY, BOLD = "Body", "Body-Bold"
except Exception:  # non-Windows fallback
    BODY, BOLD = "Helvetica", "Helvetica-Bold"
MONO = "Courier"

# ---------------------------------------------------------------- styles
st = {
    "body": ParagraphStyle("body", fontName=BODY, fontSize=10.5, leading=14.5,
                           textColor=INK, spaceAfter=6),
    "h1": ParagraphStyle("h1", fontName=BOLD, fontSize=17, leading=21,
                         textColor=WINE, spaceBefore=4, spaceAfter=8,
                         keepWithNext=1),
    "h2": ParagraphStyle("h2", fontName=BOLD, fontSize=12.5, leading=16,
                         textColor=BERRY, spaceBefore=10, spaceAfter=4,
                         keepWithNext=1),
    "caption": ParagraphStyle("caption", fontName=BODY, fontSize=9, leading=12,
                              textColor=MUTED, spaceBefore=3, spaceAfter=10),
    "cell": ParagraphStyle("cell", fontName=BODY, fontSize=9, leading=11.5,
                           textColor=INK),
    "cellb": ParagraphStyle("cellb", fontName=BOLD, fontSize=9, leading=11.5,
                            textColor=colors.white),
    "bullet": ParagraphStyle("bullet", fontName=BODY, fontSize=10.5, leading=14.5,
                             textColor=INK, leftIndent=14, bulletIndent=3,
                             spaceAfter=3),
    "code": ParagraphStyle("code", fontName=MONO, fontSize=8.5, leading=11,
                           textColor=INK, backColor=TINT, borderPadding=6,
                           leftIndent=6, rightIndent=6, spaceBefore=4,
                           spaceAfter=10),
    "kpi_num": ParagraphStyle("kpi_num", fontName=BOLD, fontSize=20, leading=23,
                              textColor=BERRY, alignment=TA_CENTER),
    "kpi_lbl": ParagraphStyle("kpi_lbl", fontName=BODY, fontSize=8.5, leading=11,
                              textColor=MUTED, alignment=TA_CENTER),
    "toc1": ParagraphStyle("toc1", fontName=BODY, fontSize=11, leading=18,
                           textColor=INK, leftIndent=0),
    "toc2": ParagraphStyle("toc2", fontName=BODY, fontSize=9.5, leading=14,
                           textColor=MUTED, leftIndent=16),
}

PAGE_W, PAGE_H = A4
MARGIN = 2.2 * cm
CONTENT_W = PAGE_W - 2 * MARGIN


# ---------------------------------------------------------------- helpers
class Doc(BaseDocTemplate):
    """Registers h1/h2 headings in the table of contents and PDF outline."""

    def afterFlowable(self, f):
        if isinstance(f, Paragraph) and f.style.name in ("h1", "h2"):
            level = 0 if f.style.name == "h1" else 1
            text = f.getPlainText()
            key = f"h{id(f)}"
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(text, key, level=level, closed=False)
            self.notify("TOCEntry", (level, text, self.page, key))


def P(text, style="body"):
    return Paragraph(text, st[style])


def bullets(items):
    return [Paragraph(t, st["bullet"], bulletText="\u2022") for t in items]


def figure(path, caption, width=CONTENT_W * 0.86):
    from PIL import Image as PILImage
    w, h = PILImage.open(path).size
    img = Image(str(path), width=width, height=width * h / w)
    img.hAlign = "CENTER"
    return KeepTogether([img, P(caption, "caption")])


def table(rows, col_widths, header=True, highlight_row=None, align_right_from=None):
    data = [[c if isinstance(c, Paragraph) else
             Paragraph(str(c), st["cellb"] if (header and i == 0) else st["cell"])
             for c in r] for i, r in enumerate(rows)]
    t = Table(data, colWidths=col_widths, repeatRows=1 if header else 0)
    style = [
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, RULE),
    ]
    if header:
        style += [("BACKGROUND", (0, 0), (-1, 0), WINE)]
    for r in range(1 if header else 0, len(rows)):
        if r % 2 == 0:
            style.append(("BACKGROUND", (0, r), (-1, r), TINT))
    if highlight_row is not None:
        style += [("BACKGROUND", (0, highlight_row), (-1, highlight_row),
                   colors.HexColor("#F6E3C6"))]
    t.setStyle(TableStyle(style))
    t.hAlign = "LEFT"
    return t


def kpi_strip(items):
    cells = [[P(n, "kpi_num") for n, _ in items], [P(l, "kpi_lbl") for _, l in items]]
    w = CONTENT_W / len(items)
    t = Table(cells, colWidths=[w] * len(items))
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), TINT),
        ("LINEABOVE", (0, 0), (-1, 0), 2, BERRY),
        ("TOPPADDING", (0, 0), (-1, 0), 10),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 10),
        ("LINEAFTER", (0, 0), (-2, -1), 0.5, RULE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return t


def timeline_drawing():
    """Snapshot design: 90-day feature window + 60-day outcome window per cutoff."""
    W, H = CONTENT_W, 190
    d = Drawing(W, H)
    x0, x1 = 95, W - 10
    start, end = pd.Timestamp("2010-12-01"), pd.Timestamp("2011-12-10")
    span = (end - start).days

    def X(date):
        return x0 + (pd.Timestamp(date) - start).days / span * (x1 - x0)

    rows = [("Train 1", "2011-04-01", GREY), ("Train 2", "2011-05-01", GREY),
            ("Train 3", "2011-06-01", GREY), ("Validation", "2011-08-01", BERRY),
            ("Final test", "2011-10-01", GOLD)]
    top = H - 22
    for i, (lab, cut, col) in enumerate(rows):
        y = top - i * 27
        T = pd.Timestamp(cut)
        d.add(String(0, y + 3, lab, fontName=BOLD, fontSize=8.5, fillColor=INK))
        d.add(Rect(X(T - pd.Timedelta(days=90)), y, X(T) - X(T - pd.Timedelta(days=90)),
                   12, fillColor=col, strokeColor=None, fillOpacity=0.35))
        d.add(Rect(X(T), y, X(T + pd.Timedelta(days=60)) - X(T), 12,
                   fillColor=col, strokeColor=None))
        d.add(Line(X(T), y - 3, X(T), y + 15, strokeColor=INK, strokeWidth=1))
        d.add(String(X(T) + 2, y + 15.5, T.strftime("%d %b"), fontName=BODY,
                     fontSize=7, fillColor=MUTED))
    # axis
    ya = 30
    d.add(Line(x0, ya, x1, ya, strokeColor=MUTED, strokeWidth=0.6))
    for m in pd.date_range("2010-12-01", "2011-12-01", freq="MS"):
        d.add(Line(X(m), ya - 3, X(m), ya, strokeColor=MUTED, strokeWidth=0.6))
        d.add(String(X(m) - 8, ya - 13, m.strftime("%b"), fontName=BODY,
                     fontSize=7, fillColor=MUTED))
    # legend
    d.add(Rect(x0, 2, 14, 7, fillColor=GREY, fillOpacity=0.35, strokeColor=None))
    d.add(String(x0 + 18, 2, "Feature window: 90 days before cutoff",
                 fontName=BODY, fontSize=7.5, fillColor=INK))
    d.add(Rect(x0 + 175, 2, 14, 7, fillColor=GREY, strokeColor=None))
    d.add(String(x0 + 193, 2, "Outcome window: next 60 days (target)",
                 fontName=BODY, fontSize=7.5, fillColor=INK))
    return d


def on_page(canv, doc):
    canv.saveState()
    canv.setStrokeColor(RULE)
    canv.setLineWidth(0.6)
    canv.line(MARGIN, PAGE_H - 1.4 * cm, PAGE_W - MARGIN, PAGE_H - 1.4 * cm)
    canv.setFont(BODY, 8)
    canv.setFillColor(MUTED)
    canv.drawString(MARGIN, PAGE_H - 1.2 * cm,
                    "Customer Follow-up in Online Retail - Technical Report")
    canv.drawRightString(PAGE_W - MARGIN, 1.2 * cm, str(doc.page))
    canv.restoreState()


def on_cover(canv, doc):
    canv.saveState()
    canv.setFillColor(WINE)
    canv.rect(0, PAGE_H * 0.42, PAGE_W, PAGE_H * 0.58, stroke=0, fill=1)
    canv.setFillColor(BERRY)
    canv.rect(0, PAGE_H * 0.42 - 6, PAGE_W, 6, stroke=0, fill=1)
    canv.restoreState()


# ---------------------------------------------------------------- data
def load():
    eda = json.loads((OUT / "eda_summary.json").read_text())
    drivers = pd.read_csv(OUT / "model_drivers.csv")
    latest = pd.read_csv(OUT / "latest_scores.csv")
    chosen = (OUT / "models" / "chosen_model.txt").read_text().strip()

    from clean_data import clean, load_raw
    from models import (FEATURE_SETS, bootstrap_ap_diff, evaluate,
                        fit_logistic, recency_scores)
    import contextlib, io
    with contextlib.redirect_stdout(io.StringIO()):
        raw = load_raw()
    n_raw = len(raw)
    # replay cleaning to capture per-rule counts
    steps, df = [], raw
    rules = [
        ("Missing CustomerID", lambda d: d[d["CustomerID"].notna()]),
        ("Exact duplicate rows", lambda d: d.drop_duplicates()),
        ("Cancellations (invoice starts with C)", lambda d: d[~d["InvoiceNo"].str.startswith("C")]),
        ("Non-positive unit price", lambda d: d[d["UnitPrice"] > 0]),
        ("Admin codes: POST, M, C2, DOT, BANK CHARGES",
         lambda d: d[~d["StockCode"].str.strip().str.upper()
                     .isin({"POST", "M", "C2", "DOT", "BANK CHARGES"})]),
    ]
    for name, fn in rules:
        before = len(df)
        df = fn(df)
        steps.append((name, before - len(df), len(df)))
    clean_stats = dict(lines=len(df), customers=df["CustomerID"].nunique(),
                       invoices=df["InvoiceNo"].nunique())

    proc = ROOT / "data" / "processed"
    tr = pd.read_csv(proc / "snapshot_train.csv")
    va = pd.read_csv(proc / "snapshot_validation.csv")
    te = pd.read_csv(proc / "snapshot_test.csv")
    yv, yt = va["target_no_purchase"].to_numpy(), te["target_no_purchase"].to_numpy()
    sv = {"recency": recency_scores(va)}
    stt = {"recency": recency_scores(te)}
    for k, f in FEATURE_SETS.items():
        m = fit_logistic(tr, f)
        sv[k] = m.predict_proba(va[f])[:, 1]
        stt[k] = m.predict_proba(te[f])[:, 1]
    ci_rfm_rec = bootstrap_ap_diff(yv, sv["rfm"], sv["recency"])
    ci_tim_rfm = bootstrap_ap_diff(yv, sv["rfm_timing"], sv["rfm"])
    test_all = {k: evaluate(yt, s) for k, s in stt.items()}
    return dict(eda=eda, drivers=drivers, latest=latest, chosen=chosen,
                n_raw=n_raw, steps=steps, clean=clean_stats,
                n_train=len(tr), train_rate=tr["target_no_purchase"].mean(),
                ci_rfm_rec=ci_rfm_rec, ci_tim_rfm=ci_tim_rfm, test_all=test_all,
                n_leavers_test=int(yt.sum()))


# ---------------------------------------------------------------- report
def build():
    D = load()
    eda, val, ft = D["eda"], D["eda"]["validation"], D["eda"]["final_test"]
    rc, nv, mr = eda["revenue_concentration"], eda["new_vs_returning"], eda["money_at_risk"]
    latest = D["latest"]
    high = latest[latest["risk_level"] == "High"]
    med = latest[latest["risk_level"] == "Medium"]
    pct = lambda v, d=0: f"{v * 100:.{d}f}%"

    doc = Doc(str(PDF), pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN,
              topMargin=2 * cm, bottomMargin=2 * cm,
              title="Customer Follow-up in Online Retail - Technical Report",
              author=AUTHOR or "Final-year data science project",
              subject="Predicting which regular customers stop buying in the next 60 days")
    frame = Frame(MARGIN, 2 * cm, CONTENT_W, PAGE_H - 4 * cm, id="f")
    doc.addPageTemplates([
        PageTemplate("cover", frames=[frame], onPage=on_cover),
        PageTemplate("body", frames=[frame], onPage=on_page),
    ])

    s = []
    # ---------------- cover
    cover_title = ParagraphStyle("ct", fontName=BOLD, fontSize=30, leading=35,
                                 textColor=colors.white)
    cover_sub = ParagraphStyle("cs", fontName=BODY, fontSize=14, leading=19,
                               textColor=colors.HexColor("#F0B3CB"))
    cover_meta = ParagraphStyle("cm", fontName=BODY, fontSize=10.5, leading=15,
                                textColor=INK)
    s += [Spacer(1, 3.2 * cm),
          Paragraph("TECHNICAL REPORT", ParagraphStyle(
              "kick", fontName=BOLD, fontSize=10, textColor=colors.HexColor("#F0B3CB"),
              spaceAfter=14)),
          Paragraph("Customer Follow-up<br/>in Online Retail", cover_title),
          Spacer(1, 14),
          Paragraph("Which regular customers may stop buying in the next 60 days, "
                    "and who should the retailer call first?", cover_sub),
          Spacer(1, 8.6 * cm)]
    logo = ASSETS / "kdu_logo.jpeg"
    meta = ("Final-year data science course project<br/>"
            + (f"{AUTHOR}<br/>" if AUTHOR else "")
            + f"{REPORT_DATE}<br/><br/>"
            "<font color='#6B5B66'>Data: UCI Online Retail dataset "
            "(UK online retailer, 1 Dec 2010 - 9 Dec 2011)</font>")
    if logo.exists():
        from PIL import Image as PILImage
        lw, lh = PILImage.open(logo).size
        img = Image(str(logo), width=3.2 * cm, height=3.2 * cm * lh / lw)
        t = Table([[Paragraph(meta, cover_meta), img]],
                  colWidths=[CONTENT_W - 3.6 * cm, 3.6 * cm])
        t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                               ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
        s.append(t)
    else:
        s.append(Paragraph(meta, cover_meta))
    s += [NextPageTemplate("body"), PageBreak()]

    # ---------------- contents
    s.append(Paragraph("Contents", ParagraphStyle(
        "toch", parent=st["h1"])))  # not registered in TOC (different style name)
    toc = TableOfContents()
    toc.levelStyles = [st["toc1"], st["toc2"]]
    s += [toc, PageBreak()]

    # ---------------- 1 executive summary
    s.append(P("1. Executive summary", "h1"))
    s.append(P(
        "A UK online gift retailer has limited staff time for customer follow-up. This "
        "project builds a scoring system that ranks every <b>regular</b> customer by their "
        "risk of making <b>no purchase in the next 60 days</b>, using only their last 90 "
        "days of orders. The top 10% are placed on a follow-up list with the reasons "
        "behind each score."))
    s.append(Spacer(1, 4))
    s.append(kpi_strip([
        (f"{ft['hits']} / {ft['k']}", "correct on the locked<br/>final test (1 Oct 2011)"),
        (f"{ft['lift']:.1f}x", "lift over random<br/>follow-up"),
        (pct(rc["top10pct_share"]), "of revenue from the<br/>top 10% of customers"),
        (f"{len(high)}", "customers on the live<br/>list (10 Dec 2011)"),
    ]))
    s.append(Spacer(1, 10))
    s += bullets([
        f"<b>Data.</b> {D['n_raw']:,} raw invoice lines were reduced by five frozen "
        f"cleaning rules to {D['clean']['lines']:,} lines, {D['clean']['customers']:,} "
        f"customers and {D['clean']['invoices']:,} invoices.",
        "<b>Design.</b> Time-split snapshots: features come only from the 90 days before a "
        "cutoff, the outcome from the 60 days after. Three training cutoffs (Apr-Jun 2011), "
        "one validation cutoff (1 Aug) and one locked test cutoff (1 Oct).",
        f"<b>Model.</b> Three candidates were compared on validation; logistic regression on "
        f"RFM plus purchase-timing features won ({val['rfm_timing']['hits']} of "
        f"{val['rfm_timing']['k']} correct, {pct(val['rfm_timing']['precision'], 1)} vs a "
        f"{pct(val['base_rate'], 1)} base rate) and was frozen.",
        f"<b>Test.</b> On the untouched 1 Oct 2011 test the frozen model found "
        f"{ft['hits']} real non-buyers in its top {ft['k']} ({pct(ft['precision'], 1)} vs "
        f"{pct(ft['base_rate'], 1)} at random): about twice as useful as calling at random.",
        "<b>Key driver.</b> The depth of the buying habit (number of separate order days) is "
        "by far the strongest signal; customers with only 3 order days in 90 days stop at "
        "20%, those with 9+ almost never do.",
        "<b>Deliverables.</b> A reproducible pipeline (<font face='Courier'>run_all.py</font>), "
        "a ranked follow-up list with plain-English reasons, and a Streamlit dashboard for "
        "business users.",
    ])
    s.append(PageBreak())

    # ---------------- 2 problem
    s.append(P("2. Business problem and scope", "h1"))
    s.append(P(
        "The retailer sells mainly to small businesses and repeat buyers. Revenue is highly "
        "concentrated (Section 4), so losing a handful of good regular customers costs far "
        "more than losing many one-off buyers. Staff can only contact a limited number of "
        "customers, so the task is framed as <b>ranking</b>, not yes/no classification: "
        "<i>who should be on the top-10% call list this week?</i>"))
    s.append(P("Scope decisions", "h2"))
    s += bullets([
        "<b>Who is scored:</b> regular, recent customers only - at least 3 distinct purchase "
        "dates in the 90 days before the cutoff and at least 1 purchase in the last 30 days. "
        "One-off buyers are excluded: there is no habit to protect and no history to learn from.",
        "<b>What is predicted:</b> target = 1 if the customer makes <b>no purchase in the next "
        "60 days</b>. This is a practical, observable proxy for churn in a non-contractual "
        "setting where customers never formally cancel.",
        "<b>How success is measured:</b> precision in the top 10% (how many people on the "
        "call list really stop buying), always shown next to the base rate, plus lift and "
        "Average Precision (AP) as a whole-ranking measure.",
    ])

    # ---------------- 3 data
    s.append(P("3. Data and cleaning", "h1"))
    s.append(P(
        "The source is the public <b>UCI Online Retail</b> dataset: every transaction of a "
        "UK-based, non-store online retailer between 1 December 2010 and 9 December 2011. "
        "Each row is one invoice line with InvoiceNo, StockCode, Description, Quantity, "
        "InvoiceDate, UnitPrice, CustomerID and Country. Revenue per line is computed as "
        "Quantity x UnitPrice."))
    s.append(P("3.1 Cleaning rules", "h2"))
    s.append(P(
        "Five rules were fixed in Week 3 and not changed afterwards, so later modelling "
        "choices could not be tuned by quietly altering the data. Rows removed at each step:"))
    rows = [["#", "Rule", "Rows removed", "Rows left"]]
    for i, (name, rem, left) in enumerate(D["steps"], 1):
        rows.append([str(i), name, f"{rem:,}", f"{left:,}"])
    rows.insert(1, ["", "Raw file", "", f"{D['n_raw']:,}"])
    s.append(table(rows, [1 * cm, 9 * cm, 3 * cm, 3.6 * cm]))
    s.append(P(
        f"Result: <b>{D['clean']['lines']:,}</b> invoice lines, "
        f"<b>{D['clean']['customers']:,}</b> customers, <b>{D['clean']['invoices']:,}</b> "
        "invoices. Missing CustomerID is the largest loss (about a quarter of rows): those "
        "sales cannot be linked to a person, so they are useless for customer-level "
        "prediction. The stock code PADS looks administrative but is a real product and "
        "was deliberately kept.", "caption"))

    # ---------------- 4 EDA
    s.append(PageBreak())
    s.append(P("4. Exploratory analysis", "h1"))
    s.append(P("4.1 Strong seasonality", "h2"))
    s.append(P(
        "Monthly active customers sit between 740 and 1,050 for most of the year, then climb "
        "sharply from September to a peak of 1,660 in November as shops stock up for "
        "Christmas. This matters for evaluation: the final test window (Oct-Nov) is peak "
        "season, when fewer regulars stop buying, so results are always reported against "
        "that window's own base rate."))
    s.append(figure(ASSETS / "fig_seasonality.png",
                    "Figure 1. Customers who bought in each month, Dec 2010 - Nov 2011 "
                    "(December 2011 is incomplete and omitted).", CONTENT_W * 0.72))
    s.append(P("4.2 Revenue is concentrated in few customers", "h2"))
    s.append(P(
        f"The top 10% of customers generate <b>{pct(rc['top10pct_share'])}</b> of total "
        f"revenue (GBP {rc['total_revenue'] / 1e6:.2f}m) and the top 20% generate "
        f"<b>{pct(rc['top20pct_share'])}</b>. Keeping the right few customers is worth far "
        "more than broad, untargeted campaigns."))
    s.append(figure(ASSETS / "fig_revenue_concentration.png",
                    "Figure 2. Cumulative share of revenue by share of customers, "
                    "largest spenders first.", CONTENT_W * 0.72))
    s.append(P("4.3 Returning customers pay most of the bills", "h2"))
    s.append(P(
        f"Returning customers bring <b>{pct(nv['returning_share_of_revenue'])}</b> of all "
        f"revenue, and their share grows every month. Yet <b>{pct(eda['one_time_buyer_share'])}</b> "
        "of customers never place a second order."))
    s.append(figure(ASSETS / "fig_new_vs_returning.png",
                    "Figure 3. Monthly revenue from new vs returning customers.",
                    CONTENT_W * 0.72))
    s.append(P("4.4 Cohort retention", "h2"))
    s.append(P(
        "Grouping customers by the month of their first purchase shows that typically only "
        "15-25% of a new cohort is active one month later. The December 2010 cohort is "
        "unusually loyal (35-40% active most months) because it mixes in long-standing "
        "customers whose real first purchase predates the dataset. Losses happen early, which "
        "supports focusing the model on customers who have already formed a habit."))
    s.append(figure(ASSETS / "cohort_retention_berry.png",
                    "Figure 4. Share of each first-purchase cohort active N months later.",
                    CONTENT_W * 0.9))

    # ---------------- 5 design
    s.append(PageBreak())
    s.append(P("5. Prediction design", "h1"))
    s.append(P("5.1 Time-split snapshots", "h2"))
    s.append(P(
        "A random train/test split would leak the future into the past. Instead the data is "
        "cut into <b>snapshots</b>. At each cutoff date T, features are computed only from "
        "orders in [T-90, T) and the target only from orders in [T, T+60). Each split's "
        "outcome window ends before the next split's cutoff, so no information from the "
        "validation or test periods reaches training."))
    s.append(timeline_drawing())
    s.append(P("Figure 5. Snapshot cutoffs, feature windows (light) and outcome windows "
               "(solid). Training uses three stacked monthly snapshots.", "caption"))
    split_rows = [["Split", "Cutoff(s)", "Eligible customer-snapshots", "Stopped buying (base rate)"],
                  ["Train", "1 Apr, 1 May, 1 Jun 2011", f"{D['n_train']}", pct(D["train_rate"], 1)],
                  ["Validation", "1 Aug 2011", "311", pct(val["base_rate"], 1)],
                  ["Final test (locked)", "1 Oct 2011", f"{ft['n']}", pct(ft["base_rate"], 1)]]
    s.append(table(split_rows, [3.4 * cm, 4.6 * cm, 4.6 * cm, 4 * cm]))
    s.append(Spacer(1, 4))
    s.append(P(
        "The test set was <b>locked</b>: it was not looked at until the model and its "
        "decision rule had been frozen on validation, and it was then scored exactly once."))

    s.append(P("5.2 Features", "h2"))
    feat_rows = [["Group", "Feature", "Definition (within the 90-day window)"],
                 ["RFM", "recency_days", "Days from the last purchase date to the cutoff"],
                 ["RFM", "log_frequency", "log(1 + number of distinct purchase dates)"],
                 ["RFM", "log_monetary", "log(1 + total revenue)"],
                 ["Timing", "usual_gap", "Median gap in days between consecutive purchase dates"],
                 ["Timing", "gap_spread", "Standard deviation of those gaps (irregularity)"],
                 ["Timing", "delay_ratio", "recency_days / usual_gap - how late the customer is "
                                           "relative to their own rhythm"]]
    s.append(table(feat_rows, [2.2 * cm, 3.4 * cm, 11 * cm]))
    s.append(P("Logs reduce the heavy right skew of order counts and spending. All model "
               "inputs are standardised (z-scores) using training-set statistics.", "caption"))

    # ---------------- 6 modelling
    s.append(P("6. Models and selection rule", "h1"))
    mod_rows = [["Model", "Description", "Role"],
                ["Recency ranking", "Sort customers by days since last purchase "
                                    "(random jitter breaks ties). No training.", "Baseline 1"],
                ["RFM logistic regression", "StandardScaler + LogisticRegression on recency, "
                                            "log frequency and log spend.", "Baseline 2"],
                ["RFM + timing", "Same pipeline plus usual_gap, gap_spread and delay_ratio "
                                 "(Week 5).", "Candidate"]]
    s.append(table(mod_rows, [4 * cm, 9.6 * cm, 3 * cm]))
    s.append(Spacer(1, 6))
    s.append(P(
        "Logistic regression was chosen deliberately: with only 776 training rows and ~96 "
        "positive cases, a simple, regularised, interpretable model is less likely to "
        "overfit than tree ensembles, and its coefficients translate directly into reasons "
        "staff can act on."))
    s.append(P(
        "<b>Pre-stated selection rule.</b> The timing features are kept only if RFM + timing "
        "beats the best baseline's top-10% precision on validation; otherwise the baseline "
        "with the higher AP is chosen. A 2,000-sample bootstrap over customers gives 95% "
        "confidence intervals for AP differences."))

    # ---------------- 7 results
    s.append(Spacer(1, 8))
    s.append(P("7. Results", "h1"))
    s.append(P("7.1 Validation (1 Aug 2011)", "h2"))
    vr = [["Model", "Correct in top 32", "Precision", "Lift", "AP"],
          ["Random pick", "~4", pct(val["base_rate"], 1), "1.0", "-"]]
    for key, name in [("recency", "Recency ranking"), ("rfm", "RFM model"),
                      ("rfm_timing", "RFM + timing")]:
        r = val[key]
        vr.append([name, f"{r['hits']}", pct(r["precision"], 1), f"{r['lift']:.1f}",
                   f"{r['ap']:.2f}"])
    s.append(table(vr, [4.6 * cm, 3.4 * cm, 3 * cm, 2.6 * cm, 3 * cm], highlight_row=4))
    lo, hi = D["ci_rfm_rec"]
    lo2, hi2 = D["ci_tim_rfm"]
    s.append(Spacer(1, 6))
    s.append(P(
        f"RFM + timing has the best precision and the best AP, so under the pre-stated rule "
        f"it was <b>frozen as the final model</b>. The differences are small, however: the "
        f"bootstrap 95% CI for AP(RFM) - AP(recency) is [{lo:+.2f}, {hi:+.2f}] and for "
        f"AP(RFM + timing) - AP(RFM) it is [{lo2:+.2f}, {hi2:+.2f}]. Both include zero, so on "
        f"a 311-customer validation set the three rankings cannot be cleanly separated."))
    s.append(figure(ASSETS / "fig_bakeoff.png",
                    "Figure 6. Share of each model's top-10% list that really stopped buying "
                    "(validation).", CONTENT_W * 0.66))

    s.append(P("7.2 Final test (1 Oct 2011, scored once)", "h2"))
    s.append(P(
        f"The frozen model, trained only on the three training snapshots, ranked {ft['n']} "
        f"eligible customers. Of its top {ft['k']}, <b>{ft['hits']} really stopped buying</b>: "
        f"precision {pct(ft['precision'], 1)} against a base rate of {pct(ft['base_rate'], 1)}, "
        f"a lift of <b>{ft['lift']:.1f}x</b> (AP {ft['ap']:.2f}). Precision is lower than on "
        "validation mainly because the test window is peak season - far fewer regulars stop "
        "buying in Oct-Nov - which is why lift over the base rate is the fairer comparison."))
    s.append(figure(ASSETS / "fig_gains.png",
                    f"Figure 7. Cumulative gains on the locked test: contacting the riskiest "
                    f"10% finds 21% of the {D['n_leavers_test']} real leavers; the riskiest "
                    "30% finds 52%.", CONTENT_W * 0.72))
    ta = D["test_all"]
    s.append(P("7.3 Post-hoc check of the baselines on test", "h2"))
    s.append(P(
        "After the final result was recorded, the two baselines were also scored on the test "
        "snapshot purely as a diagnostic. This does not change the frozen choice, but it is "
        "reported for transparency:"))
    pr = [["Model (test, top 34 of 334)", "Correct", "Precision", "Lift", "AP"]]
    for key, name in [("recency", "Recency ranking"), ("rfm", "RFM model"),
                      ("rfm_timing", "RFM + timing (frozen)")]:
        r = ta[key]
        pr.append([name, f"{r['hits']}", pct(r["precision_at_k"], 1), f"{r['lift']:.1f}",
                   f"{r['average_precision']:.2f}"])
    s.append(table(pr, [5.6 * cm, 2.6 * cm, 3 * cm, 2.4 * cm, 3 * cm], highlight_row=3))
    s.append(Spacer(1, 6))
    s += bullets([
        f"<b>Recency alone breaks down in peak season</b> ({ta['recency']['hits']} of 34, "
        "below random). In October almost all regulars are recent buyers, so days-since-last-"
        "order carries little information. Any learned model is clearly safer than this rule "
        "of thumb.",
        f"<b>The timing features did not add value on test.</b> Plain RFM found the same "
        f"{ta['rfm']['hits']} non-buyers and had a higher AP "
        f"({ta['rfm']['average_precision']:.2f} vs {ta['rfm_timing']['average_precision']:.2f}). "
        "Together with the validation CIs this suggests the Week 5 gain was partly noise; a "
        "simpler RFM model would be a defensible production choice.",
    ])

    # ---------------- 8 drivers
    s.append(PageBreak())
    s.append(P("8. What drives the risk score", "h1"))
    s.append(P(
        "Because inputs are standardised, coefficient sizes are directly comparable: each bar "
        "shows the change in log-odds of stopping for a one-standard-deviation increase in "
        "that feature."))
    s.append(figure(ASSETS / "fig_model_drivers.png",
                    "Figure 8. Standardised logistic-regression coefficients of the frozen "
                    "model.", CONTENT_W * 0.7))
    dr = D["drivers"].set_index("feature")["coef"]
    s += bullets([
        f"<b>Number of order days</b> dominates ({dr['log_frequency']:+.2f}): a deeper buying "
        "habit is strongly protective. This matches the raw data (Figure 9).",
        f"<b>Money spent</b> ({dr['log_monetary']:+.2f}) is also protective: larger accounts "
        "are more committed.",
        "<b>Irregular, widely spaced and late</b> customers (gap spread, usual gap, delay "
        "ratio, each about +0.2) are moderately riskier.",
        f"<b>Days since last order</b> is near zero ({dr['recency_days']:+.2f}) in the joint "
        "model. On its own recency does matter (Figure 10), but its information is largely "
        "absorbed by delay_ratio and frequency, which are built from it. Coefficients of "
        "correlated features should therefore not be read as independent causal effects.",
    ])
    s.append(figure(ASSETS / "fig_risk_habit.png",
                    "Figure 9. Share of eligible regulars (all training + validation "
                    "snapshots) who stopped buying, by number of order days.",
                    CONTENT_W * 0.62))
    s.append(figure(ASSETS / "fig_risk_silence.png",
                    "Figure 10. Share who stopped buying, by days since their last order. "
                    "Risk nearly doubles after three quiet weeks.", CONTENT_W * 0.62))
    dl = eda["risk_by_delay"]
    s.append(P(
        f"The delay ratio on its own shows no upward trend ({pct(dl['<0.5x']['rate'])} for "
        f"customers well within their rhythm vs {pct(dl['>2x']['rate'])} for those more than "
        "twice their usual gap late). It only helps in combination with other features, "
        "consistent with the weak test result for the timing set."))

    # ---------------- 9 deployment
    s.append(Spacer(1, 8))
    s.append(P("9. Deployment: the follow-up list and dashboard", "h1"))
    s.append(P("9.1 Live scoring", "h2"))
    s.append(P(
        f"<font face='Courier'>score_latest.py</font> applies the frozen model at the day "
        f"after the last invoice ({latest['cutoff'].iloc[0]}). Of <b>{len(latest)}</b> "
        f"eligible regulars, the riskiest 10% (<b>{len(high)}</b>) are labelled High and the "
        f"next 20% (<b>{len(med)}</b>) Medium. The High group represents GBP "
        f"{high['monetary'].sum():,.0f} of 90-day spend. Outcomes at this date are unknown - "
        "the locked test is the evidence that the ranking works."))
    s.append(P(
        "Each customer receives rule-based, plain-English reasons derived from their features "
        "(e.g. <i>shallow habit</i> for 3 or fewer order days, <i>late</i> when the delay "
        "ratio is at least 1, <i>irregular orders</i>, <i>low spend</i> under GBP 300), so "
        "staff know what to say: a reorder nudge for a shallow habit, a check-in for a late "
        "customer. The five highest-risk customers at the latest date:"))
    tr_ = [["Rank", "Customer", "Risk score", "Days quiet", "Order days", "90-day spend", "Reasons"]]
    for _, r in latest.head(5).iterrows():
        tr_.append([str(r["rank"]), str(r["CustomerID"]), f"{r['risk_score']:.2f}",
                    str(r["recency_days"]), str(r["n_dates"]), f"GBP {r['monetary']:,.0f}",
                    r["reasons"]])
    s.append(table(tr_, [1.1 * cm, 1.8 * cm, 1.7 * cm, 1.7 * cm, 1.7 * cm, 2.3 * cm, 6.3 * cm]))
    s.append(Spacer(1, 4))
    s.append(P(
        f"On the test cutoff the {mr['list_size']}-customer list covered GBP "
        f"{mr['list_90d_spend']:,.0f} of 90-day spend (GBP {mr['avg_90d_spend_per_listed']:,.0f} "
        "per customer). The model ranks by probability of stopping, not by value, so flagged "
        "customers tend to be smaller accounts; Section 10 discusses value-weighting.",
        "caption"))
    s.append(P("9.2 Dashboard", "h2"))
    s.append(P(
        "A Streamlit app (<font face='Courier'>dashboard/app.py</font>) reads only the files "
        "in <font face='Courier'>outputs/</font> and presents four plain-English tabs:"))
    s += bullets([
        "<b>Who to contact</b> - adjustable list size, suggested action per customer, CSV download.",
        "<b>Why customers leave</b> - the EDA charts, each paired with a recommended action.",
        "<b>Look up a customer</b> - score, risk level and reasons for any eligible customer.",
        "<b>How reliable is this?</b> - the locked-test evidence in non-technical terms.",
    ])

    # ---------------- 10 limitations
    s.append(P("10. Limitations and future work", "h1"))
    s += bullets([
        "<b>Small evaluation sets.</b> 311 validation and 334 test customers give only ~35 "
        "positives each; bootstrap CIs overlap and model rankings are uncertain. Rolling-origin "
        "evaluation over more cutoffs would give tighter estimates.",
        "<b>One year of data.</b> Each season is seen once, so the model cannot learn how "
        "seasonality shifts the base rate. With more history, cutoff month could be added as a "
        "feature or the threshold recalibrated per season.",
        "<b>Proxy target.</b> No purchase in 60 days is not permanent churn; some flagged "
        "customers are simply slow re-orderers. Survival models (e.g. BG/NBD or Cox) would "
        "model time-to-next-purchase directly.",
        "<b>Risk is not value.</b> Ranking by expected lost revenue (probability x typical "
        "spend) would better align the list with business impact given Figure 2.",
        "<b>Prediction is not persuasion.</b> The model identifies who is likely to leave, not "
        "who will respond to contact. A small randomised trial of the follow-up list (contact "
        "half, hold out half) is needed to measure real retention uplift.",
        "<b>Excluded customers.</b> Sales without CustomerID (~25% of lines) and one-off buyers "
        "are outside scope; a separate first-to-second-order conversion model could address "
        "the 36% who never return.",
    ])

    # ---------------- 11 reproducibility
    s.append(P("11. Reproducibility", "h1"))
    s.append(P(
        "The whole pipeline runs from one command. Each step is also an independent script in "
        "<font face='Courier'>src/</font>; randomness (tie-breaking jitter, bootstrap, model) "
        "uses a fixed seed of 42."))
    s.append(Paragraph("pip install -r requirements.txt<br/>python run_all.py<br/>"
                       "streamlit run dashboard/app.py<br/>python report/make_tech_report.py",
                       st["code"]))
    pipe = [["Step", "Script", "Output"],
            ["0", "download_data.py", "Raw UCI file converted to CSV"],
            ["1", "clean_data.py", "data/processed/retail_clean.csv"],
            ["2", "explore.py", "Monthly activity and cohort charts"],
            ["3", "snapshots.py", "Train / validation / test snapshot CSVs"],
            ["4", "evaluate_validation.py", "validation_results.csv, chosen_model.txt"],
            ["5", "final_test.py", "followup_list.csv, test_scores_all.csv"],
            ["6", "eda_risk.py", "eda_summary.json and business-risk charts"],
            ["7", "score_latest.py", "latest_scores.csv, model_drivers.csv"]]
    s.append(table(pipe, [1.4 * cm, 4.8 * cm, 10.4 * cm]))
    s.append(P("Software: Python with pandas, NumPy, scikit-learn, matplotlib, Streamlit "
               "and Altair. Data: Chen, D. (2015). <i>Online Retail</i> [Dataset]. UCI "
               "Machine Learning Repository. https://doi.org/10.24432/C5BW33", "caption"))

    doc.multiBuild(s)
    print(f"Saved {PDF}")


if __name__ == "__main__":
    build()
