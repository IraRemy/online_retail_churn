"""Customer Follow-up Dashboard - for shop owners, no technical knowledge needed.

Run from the project folder:
    streamlit run dashboard/app.py

It only reads files produced by `python run_all.py` (outputs/ folder);
it never retrains the model. Colours and fonts live in .streamlit/config.toml;
the CSS below only adds motion and the hero banner, scoped to keyed containers.
"""
import json
from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
ASSETS = Path(__file__).resolve().parent / "assets"

RASP, AMBER, GRAY, INK, BERRY, WINE = ("#C0507C", "#C98A2D", "#8A8A93", "#33202C",
                                       "#6D2E46", "#421A30")

st.set_page_config(page_title="Customer follow-up", page_icon=":material/storefront:",
                   layout="wide")
st.logo(str(ASSETS / "logo.svg"), icon_image=str(ASSETS / "logo_icon.svg"), size="large")

# ------------------------------------------------------- motion + hero ----
st.html(f"""
<style>
  @keyframes cf-fade-up {{ from {{ opacity: 0; transform: translateY(16px); }}
                           to   {{ opacity: 1; transform: none; }} }}
  @keyframes cf-slide-in {{ from {{ opacity: 0; transform: translateX(-14px); }}
                            to   {{ opacity: 1; transform: none; }} }}
  @keyframes cf-gradient {{ 0% {{ background-position: 0% 50%; }}
                            50% {{ background-position: 100% 50%; }}
                            100% {{ background-position: 0% 50%; }} }}
  @keyframes cf-pulse {{ 0% {{ box-shadow: 0 0 0 0 rgba(255,255,255,.75); }}
                         70% {{ box-shadow: 0 0 0 9px rgba(255,255,255,0); }}
                         100% {{ box-shadow: 0 0 0 0 rgba(255,255,255,0); }} }}
  @keyframes cf-float {{ 0%, 100% {{ transform: translateY(0); }}
                         50% {{ transform: translateY(-10px); }} }}

  /* Hero banner */
  .cf-hero {{ position: relative; overflow: hidden; border-radius: 18px;
      padding: 34px 38px 30px; color: #FFF;
      background: linear-gradient(120deg, #2A1220, {BERRY}, {RASP}, {BERRY}, #2A1220);
      background-size: 300% 300%; animation: cf-gradient 16s ease infinite,
      cf-fade-up .7s ease both; box-shadow: 0 10px 30px rgba(66, 26, 48, .25); }}
  .cf-hero::before, .cf-hero::after {{ content: ""; position: absolute; border-radius: 50%;
      background: rgba(255,255,255,.07); animation: cf-float 9s ease-in-out infinite; }}
  .cf-hero::before {{ width: 260px; height: 260px; right: -60px; top: -90px; }}
  .cf-hero::after {{ width: 160px; height: 160px; right: 160px; bottom: -80px;
      animation-delay: -4s; }}
  .cf-eyebrow {{ font-family: inherit; font-size: .78rem; font-weight: 600; line-height: 1; letter-spacing: .16em;
      text-transform: uppercase; color: #F6C6D9; }}
  .cf-hero h1 {{ font: 700 2.5rem/1.15 'Playfair Display', Georgia, serif; color: #FFF;
      margin: 12px 0 8px; padding: 0; }}
  .cf-hero p {{ font-family: inherit; font-size: 1.08rem; line-height: 1.5; color: #F3E8EE;
      margin: 0 0 20px; max-width: 760px; }}
  .cf-chips {{ display: flex; flex-wrap: wrap; gap: 10px; position: relative; z-index: 1; }}
  .cf-chip {{ display: inline-flex; align-items: center; gap: 8px;
      font-family: inherit; font-size: .86rem; font-weight: 500; line-height: 1; padding: 9px 14px; border-radius: 999px;
      background: rgba(255,255,255,.12); border: 1px solid rgba(255,255,255,.22);
      backdrop-filter: blur(4px); color: #FFF; }}
  .cf-dot {{ width: 9px; height: 9px; border-radius: 50%; background: #7CE0A3;
      animation: cf-pulse 2s infinite; }}

  /* KPI and stat cards: rise in one after another, lift on hover */
  [class*="st-key-kpi_"] {{ animation: cf-fade-up .6s cubic-bezier(.2,.7,.2,1) both;
      transition: transform .2s ease, box-shadow .2s ease;
      box-shadow: 0 1px 2px rgba(51, 32, 44, .06); }}
  [class*="st-key-kpi_"]:hover {{ transform: translateY(-4px);
      box-shadow: 0 10px 24px rgba(66, 26, 48, .14); }}
  .st-key-kpi_1, .st-key-kpi_s1 {{ animation-delay: .05s; }}
  .st-key-kpi_2, .st-key-kpi_s2 {{ animation-delay: .15s; }}
  .st-key-kpi_3, .st-key-kpi_s3 {{ animation-delay: .25s; }}
  .st-key-kpi_4 {{ animation-delay: .35s; }}

  /* Chart / content cards */
  [class*="st-key-card_"] {{ animation: cf-fade-up .55s ease both;
      transition: box-shadow .25s ease, transform .25s ease; }}
  [class*="st-key-card_"]:hover {{ box-shadow: 0 12px 28px rgba(66, 26, 48, .12);
      transform: translateY(-2px); }}

  /* Section tabs: big buttons, active one filled; panel fades in on switch */
  .st-key-section [role="tablist"] {{ gap: 10px; padding: 8px; border-radius: 16px;
      background: #F7F1F4; border-bottom: none; margin-bottom: 8px; }}
  .st-key-section [role="tab"] {{ flex: 1 1 0; justify-content: center;
      padding: 14px 10px; border-radius: 12px; background: #FFF;
      border: 1px solid #EADDE3; color: {INK};
      transition: background .2s, color .2s, transform .2s, box-shadow .2s; }}
  .st-key-section [role="tab"] p {{ font-size: 1.05rem; }}
  .st-key-section [role="tab"]:hover {{ background: #FBE9F0; color: {BERRY};
      transform: translateY(-2px); }}
  .st-key-section [role="tab"][aria-selected="true"] {{
      background: linear-gradient(135deg, {RASP}, {BERRY}); border-color: transparent;
      color: #FFF; box-shadow: 0 6px 16px rgba(192, 80, 124, .35); }}
  .st-key-section [role="tab"][aria-selected="true"] p,
  .st-key-section [role="tab"][aria-selected="true"] span {{ color: #FFF; }}
  .st-key-section [data-baseweb="tab-highlight"],
  .st-key-section [data-baseweb="tab-border"] {{ display: none; }}
  .st-key-section [role="tabpanel"] {{ animation: cf-fade-up .45s ease both; }}

  /* "What to do" action strip */
  .cf-action {{ display: flex; gap: 12px; align-items: flex-start;
      background: linear-gradient(135deg, {WINE}, #5A2440); color: #F3E8EE;
      padding: 14px 18px; border-radius: 12px; margin: 6px 0 4px;
      font-family: inherit; font-size: .98rem; line-height: 1.5; animation: cf-slide-in .6s ease both; }}
  .cf-action b {{ color: #F2C078; font-weight: 600; white-space: nowrap; }}

  @media (prefers-reduced-motion: reduce) {{
    .cf-hero, .cf-hero::before, .cf-hero::after, .cf-dot, .cf-action,
    [class*="st-key-kpi_"], [class*="st-key-card_"],
    .st-key-section [role="tabpanel"], .st-key-section [role="tab"] {{
      animation: none !important; transition: none !important; }}
  }}
</style>""")


# ---------------------------------------------------------------- data ----
@st.cache_data
def load():
    needed = ["latest_scores.csv", "test_scores_all.csv", "eda_summary.json",
              "model_drivers.csv"]
    missing = [f for f in needed if not (OUT / f).exists()]
    if missing:
        return None, missing
    latest = pd.read_csv(OUT / "latest_scores.csv")
    test = pd.read_csv(OUT / "test_scores_all.csv").sort_values(
        "risk_score", ascending=False).reset_index(drop=True)
    summary = json.loads((OUT / "eda_summary.json").read_text())
    drivers = pd.read_csv(OUT / "model_drivers.csv")
    return (latest, test, summary, drivers), []


def suggested_action(row, key_account_spend):
    if row["monetary"] >= key_account_spend:
        return "PRIORITY (key account): personal phone call"
    if row["delay_ratio"] >= 1 or row["recency_days"] >= 21:
        return "Personal check-in: 'we haven't seen you lately'"
    if row["n_dates"] <= 3:
        return "Reorder reminder + small loyalty reward"
    return "Friendly e-mail with new products"


def action_box(text):
    st.html(f'<div class="cf-action"><b>What to do</b><span>{text}</span></div>')


def capture_at(test, share):
    """Share of real leavers found when contacting the riskiest `share` (test set)."""
    k = int(np.ceil(share * len(test)))
    return test["target_no_purchase"].iloc[:k].sum() / test["target_no_purchase"].sum()


def bar_chart(df, x, y, color, x_title, y_title, fmt=".0%", height=290):
    base = alt.Chart(df).encode(
        x=alt.X(f"{x}:N", sort=None, title=x_title, axis=alt.Axis(labelAngle=0)),
        y=alt.Y(f"{y}:Q", title=y_title, axis=alt.Axis(format=fmt)),
        tooltip=[alt.Tooltip(f"{x}:N", title=x_title or x),
                 alt.Tooltip(f"{y}:Q", title=y_title, format=fmt)] +
                ([alt.Tooltip("n:Q", title="Customers")] if "n" in df else []))
    bars = base.mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6).encode(
        color=alt.Color(f"{color}:N", scale=None, legend=None))
    labels = base.mark_text(dy=-9, fontSize=14, fontWeight="bold", color=INK).encode(
        text=alt.Text(f"{y}:Q", format=fmt))
    return (bars + labels).properties(height=height)


data, missing = load()
if data is None:
    st.error("Results not found: " + ", ".join(missing) +
             ".  Run `python run_all.py` in the project folder first.",
             icon=":material/error:")
    st.stop()
latest, test, S, drivers = data

score_date = pd.to_datetime(latest["cutoff"].iloc[0])
data_end = (score_date - pd.Timedelta(days=1)).strftime("%d %b %Y")
key_account_spend = latest["monetary"].quantile(0.75)
latest["action"] = latest.apply(suggested_action, axis=1,
                                key_account_spend=key_account_spend)
high = latest[latest["risk_level"] == "High"]
ft = S["final_test"]

# ------------------------------------------------------------- sidebar ----
with st.sidebar:
    st.subheader("How to use this page", icon=":material/menu_book:")
    st.markdown(
        ":material/phone_in_talk: **Who to contact** - choose how many customers "
        "your team can reach, then download the list.\n\n"
        ":material/person_search: **Look up a customer** - check one name "
        "before you call.\n\n"
        ":material/insights: **Why customers leave** - plan longer-term offers.\n\n"
        ":material/verified: **Can I trust it?** - see how the list was tested.")
    st.space("medium")
    st.caption(f":material/event: Sales data up to **{data_end}**")
    st.caption(":material/group: **Regular** = ordered on 3+ separate days in the last "
               "90 days and at least once in the last 30 days.")
    st.caption(":material/trending_down: **Risk** = estimated chance of **no order in "
               "the next 60 days**.")

# -------------------------------------------------------------- header ----
st.html(f"""
<div class="cf-hero">
  <div class="cf-eyebrow">Retention intelligence &middot; UK online retailer</div>
  <h1>Customer follow-up dashboard</h1>
  <p>Which regular customers may stop buying in the next 60 days &mdash;
     and what your team should do about it this week.</p>
  <div class="cf-chips">
    <span class="cf-chip"><span class="cf-dot"></span>Live list &middot; data to {data_end}</span>
    <span class="cf-chip">{len(latest):,} regular customers scored</span>
    <span class="cf-chip">Tested on unseen months &middot; {ft['lift']:.1f}x better than random</span>
  </div>
</div>""")
st.space("small")

kpis = [
    ("Regulars checked", f"{len(latest):,}", ":material/groups:",
     "Customers who ordered on 3+ days in the last 90 days and once in the last 30."),
    ("High risk right now", f"{len(high)}", ":material/warning:",
     "The riskiest 10% of regular customers."),
    ("Spend at risk", f"£{high['monetary'].sum():,.0f}", ":material/payments:",
     "What the high-risk customers spent in the last 90 days."),
    ("Better than random calls", f"{ft['lift']:.1f}x", ":material/verified:",
     f"Proven on Oct 2011 data the model never saw: {ft['hits']} of {ft['k']} "
     f"flagged customers really stopped, vs about {ft['base_rate']:.0%} by chance."),
]
for i, (col, (label, value, icon, tip)) in enumerate(zip(st.columns(4), kpis), start=1):
    with col.container(border=True, key=f"kpi_{i}", height="stretch"):
        st.metric(label, value, icon=icon, help=tip)

st.space("small")
tab1, tab3, tab2, tab4 = st.tabs(
    [":material/phone_in_talk: **Who to contact**",
     ":material/person_search: **Look up a customer**",
     ":material/insights: **Why customers leave**",
     ":material/verified: **Can I trust it?**"],
    key="section")

# ---------------------------------------------------- tab 1: the list ----
with tab1:
    st.subheader("Your call list for this week", icon=":material/phone_in_talk:")
    st.caption("Regular customers most likely to stop buying in the next 60 days, "
               "riskiest first. Choose how many your team can contact, then download "
               "the list and follow the suggested action for each name.")
    with st.container(border=True, key="card_controls"):
        left, right = st.columns([2, 1], vertical_alignment="bottom")
        with left:
            n = st.slider("How many customers can your team contact this week?",
                          min_value=10, max_value=len(latest), value=len(high), step=1)
        with right:
            min_spend = st.number_input(
                "Only show customers who spent at least (£, last 90 days)",
                min_value=0, value=0, step=50)

    share = n / len(latest)
    cap = capture_at(test, share)
    view = latest.head(n)
    view = view[view["monetary"] >= min_spend]

    s1, s2, s3 = st.columns(3)
    with s1.container(border=True, key="kpi_s1", height="stretch"):
        st.metric("Customers on your list", f"{len(view)}", icon=":material/checklist:",
                  help=f"The riskiest {n} regulars ({share:.0%}), after the spend filter.")
    with s2.container(border=True, key="kpi_s2", height="stretch"):
        st.metric("Leavers you would reach", f"{cap:.0%}", icon=":material/target:",
                  delta=f"{(cap - share) * 100:+.0f} pts vs random calls",
                  help="Share of customers who really left that this list size "
                       "reached in our October 2011 test.")
    with s3.container(border=True, key="kpi_s3", height="stretch"):
        st.metric("Their recent spend", f"£{view['monetary'].sum():,.0f}",
                  icon=":material/savings:",
                  help="What these customers spent in the last 90 days.")

    table = pd.DataFrame({
        "Customer": view["CustomerID"].astype(str),
        "Risk": view["risk_level"],
        "Chance of stopping": view["risk_score"] * 100,
        "Suggested action": view["action"],
        "Why flagged": view["reasons"],
        "Days quiet": view["recency_days"],
        "Order days (90 d)": view["n_dates"],
        "Spent (90 d)": view["monetary"],
    })
    risk_colors = {"High": f"color: {RASP}; font-weight: 700",
                   "Medium": f"color: {AMBER}; font-weight: 600",
                   "Low": f"color: {GRAY}"}
    with st.container(border=True, key="card_table"):
        st.dataframe(
            table.style.map(lambda v: risk_colors.get(v, ""), subset=["Risk"]),
            hide_index=True, width="stretch", height=440,
            column_config={
                "Chance of stopping": st.column_config.ProgressColumn(
                    format="%.0f%%", min_value=0, max_value=60),
                "Spent (90 d)": st.column_config.NumberColumn(format="£%.0f"),
                "Suggested action": st.column_config.TextColumn(width="large"),
                "Why flagged": st.column_config.TextColumn(width="medium"),
            })
        st.download_button("Download this list (CSV, opens in Excel)",
                           table.to_csv(index=False).encode("utf-8"),
                           file_name=f"follow_up_list_{score_date:%Y%m%d}.csv",
                           mime="text/csv", type="primary", icon=":material/download:")

# --------------------------------------------- tab 3: customer lookup ----
with tab3:
    st.subheader("Check one customer before you call", icon=":material/person_search:")
    st.caption("Type a customer number to see their risk, why they were flagged, "
               "and what to say when you call.")
    options = latest["CustomerID"].astype(str).tolist()
    cid = st.selectbox("Customer number (type to search)", options, index=0)
    row = latest[latest["CustomerID"].astype(str) == cid].iloc[0]

    k = st.columns(4)
    cards = [
        ("Risk level", row["risk_level"], ":material/flag:",
         f"Rank {int(row['rank'])} of {len(latest)} regular customers."),
        ("Chance of stopping", f"{row['risk_score']:.0%}", ":material/trending_down:",
         "Estimated chance of no order in the next 60 days."),
        ("Days since last order", f"{int(row['recency_days'])}", ":material/schedule:",
         f"Usually orders every {row['usual_gap']:.0f} days."),
        ("Spent in last 90 days", f"£{row['monetary']:,.0f}", ":material/payments:",
         f"{int(row['n_dates'])} separate order days."),
    ]
    for i, (col, (label, value, icon, tip)) in enumerate(zip(k, cards), start=1):
        with col.container(border=True, key=f"kpi_c{i}", height="stretch"):
            st.metric(label, value, icon=icon, help=tip)

    with st.container(border=True, key="card_lookup"):
        st.progress(min(float(row["risk_score"]) / 0.6, 1.0),
                    text=f"Risk meter - {row['risk_score']:.0%} chance of stopping "
                         f"(rank {int(row['rank'])} of {len(latest)})")
        st.markdown(f"**Why flagged:** {row['reasons']}")
        action_box(row["action"])
        typical = latest[["recency_days", "n_dates", "monetary", "usual_gap"]].median()
        comp = pd.DataFrame({
            "Measure": ["Days since last order", "Usual days between orders",
                        "Order days (90 d)", "Spent (90 d), £"],
            "This customer": [int(row["recency_days"]), round(row["usual_gap"]),
                              int(row["n_dates"]), round(row["monetary"])],
            "Typical regular": [int(typical["recency_days"]), round(typical["usual_gap"]),
                                int(typical["n_dates"]), round(typical["monetary"])],
        })
        st.dataframe(comp, hide_index=True, width="content")
    st.caption("Customers who are not on this list are not regulars right now "
               "(fewer than 3 order days in 90 days, or no order in the last 30 days).")

# --------------------------------------------- tab 2: why people leave ----
with tab2:
    st.subheader("The patterns behind the list", icon=":material/insights:")
    st.caption("What one year of sales shows about who stops buying, and what to do "
               "about each pattern. Use it to plan offers and reminders, not just calls.")
    a, b = st.columns(2)
    with a.container(border=True, key="card_habit", height="stretch"):
        st.markdown("##### Shallow buying habits break first")
        f = S["risk_by_frequency"]
        df = pd.DataFrame({"Order days in last 90 days": list(f),
                           "Stopped buying": [v["rate"] for v in f.values()],
                           "n": [v["n"] for v in f.values()]})
        df["c"] = [RASP, RASP, GRAY, GRAY]
        st.altair_chart(bar_chart(df, "Order days in last 90 days", "Stopped buying",
                                  "c", "Order days in last 90 days",
                                  "Stopped buying (next 60 days)"), width="stretch")
        action_box("Send reorder reminders and small loyalty rewards to customers "
                   "with only 3 order days. Getting them to a 4th order cuts the "
                   "risk by more than half.")
    with b.container(border=True, key="card_quiet", height="stretch"):
        st.markdown("##### Three quiet weeks is a warning sign")
        r = S["risk_by_recency"]
        df = pd.DataFrame({"Days since last order": [k.replace(" d", " days") for k in r],
                           "Stopped buying": [v["rate"] for v in r.values()],
                           "n": [v["n"] for v in r.values()]})
        df["c"] = [GRAY, GRAY, GRAY, RASP]
        st.altair_chart(bar_chart(df, "Days since last order", "Stopped buying", "c",
                                  "Days since last order",
                                  "Stopped buying (next 60 days)"), width="stretch")
        action_box("When a regular passes 3 weeks without ordering, send a personal "
                   "check-in before the silence becomes a loss.")

    a, b = st.columns(2)
    with a.container(border=True, key="card_revenue", height="stretch"):
        rc = S["revenue_concentration"]
        st.markdown(f"##### Top 10% of customers bring {rc['top10pct_share']:.0%} of revenue")
        curve = pd.concat([pd.DataFrame({"pct_customers": [0], "pct_revenue": [0]}),
                           pd.DataFrame(rc["curve"]),
                           pd.DataFrame({"pct_customers": [1], "pct_revenue": [1]})])
        area = alt.Chart(curve).mark_area(
            line={"color": RASP, "strokeWidth": 3}, color=RASP, opacity=0.15,
            interpolate="monotone").encode(
            x=alt.X("pct_customers:Q", title="Share of customers (biggest spenders first)",
                    axis=alt.Axis(format=".0%")),
            y=alt.Y("pct_revenue:Q", title="Share of yearly revenue",
                    axis=alt.Axis(format=".0%")),
            tooltip=[alt.Tooltip("pct_customers:Q", title="Customers", format=".0%"),
                     alt.Tooltip("pct_revenue:Q", title="Revenue", format=".0%")])
        diag = alt.Chart(pd.DataFrame({"x": [0, 1], "y": [0, 1]})).mark_line(
            color=GRAY, strokeDash=[6, 4]).encode(x="x:Q", y="y:Q")
        st.altair_chart((diag + area).properties(height=290), width="stretch")
        action_box("Treat big spenders as key accounts. When one appears on the risk "
                   "list, call them first.")
    with b.container(border=True, key="card_returning", height="stretch"):
        nv = S["new_vs_returning"]
        st.markdown(f"##### Returning customers pay "
                    f"{nv['returning_share_of_revenue']:.0%} of the bills")
        m = pd.DataFrame(nv["months"])
        m = m[m["month"] != "Dec 10"]
        long = m.melt(id_vars="month", value_vars=["returning_k", "new_k"],
                      var_name="Customer type", value_name="Revenue (£ thousand)")
        long["Customer type"] = long["Customer type"].map(
            {"returning_k": "Returning", "new_k": "New"})
        st.altair_chart(alt.Chart(long).mark_bar(cornerRadiusTopLeft=3,
                                                 cornerRadiusTopRight=3).encode(
            x=alt.X("month:N", sort=list(m["month"]), title=None,
                    axis=alt.Axis(labelAngle=0)),
            y=alt.Y("Revenue (£ thousand):Q"),
            color=alt.Color("Customer type:N",
                            scale=alt.Scale(domain=["Returning", "New"],
                                            range=[RASP, GRAY]),
                            legend=alt.Legend(orient="top", title=None)),
            order=alt.Order("Customer type:N", sort="descending"),
            tooltip=["month", "Customer type",
                     alt.Tooltip("Revenue (£ thousand):Q", format=",.0f")],
        ).properties(height=290), width="stretch")
        action_box(f"{S['one_time_buyer_share']:.0%} of customers buy only once. "
                   "Follow up every first-time buyer within 30 days to win the "
                   "second order.")

# ------------------------------------------------ tab 4: reliability ----
with tab4:
    st.subheader("Can I trust this list?", icon=":material/verified:")
    st.caption("How the score was tested on months it had never seen, and how it "
               "compares with calling customers at random.")
    t = st.columns(3)
    proof = [
        ("Flagged customers who really left", f"{ft['hits']} of {ft['k']}",
         ":material/task_alt:", "October 2011 test, opened once after the model was frozen."),
        ("Random calls would find", f"about {ft['base_rate'] * ft['k']:.0f}",
         ":material/casino:", f"The base rate that season was {ft['base_rate']:.0%}."),
        ("Lift over random", f"{ft['lift']:.1f}x", ":material/rocket_launch:",
         "How many more real leavers each call reaches than an untargeted call."),
    ]
    for i, (col, (label, value, icon, tip)) in enumerate(zip(t, proof), start=1):
        with col.container(border=True, key=f"kpi_p{i}", height="stretch"):
            st.metric(label, value, icon=icon, help=tip)

    st.caption("Trained on April-June 2011, best version chosen on August 2011, then "
               "tested once on October 2011 - data the model had never seen.")
    a, b = st.columns(2)
    with a.container(border=True, key="card_gains", height="stretch"):
        st.markdown("##### October 2011 test: leavers found")
        y = test["target_no_purchase"].to_numpy()
        g = pd.DataFrame({
            "Customers contacted": np.arange(len(y) + 1) / len(y),
            "Leavers found": np.concatenate([[0], np.cumsum(y) / y.sum()])})
        g["Method"] = "Using the risk score"
        rnd = pd.DataFrame({"Customers contacted": [0, 1], "Leavers found": [0, 1],
                            "Method": "Random calls"})
        st.altair_chart(alt.Chart(pd.concat([g, rnd])).mark_line(strokeWidth=3).encode(
            x=alt.X("Customers contacted:Q", axis=alt.Axis(format=".0%"),
                    title="Share of regulars contacted (riskiest first)"),
            y=alt.Y("Leavers found:Q", axis=alt.Axis(format=".0%"),
                    title="Share of real leavers found"),
            color=alt.Color("Method:N", scale=alt.Scale(
                domain=["Using the risk score", "Random calls"], range=[RASP, GRAY]),
                legend=alt.Legend(orient="bottom", title=None)),
            strokeDash=alt.StrokeDash("Method:N", scale=alt.Scale(
                domain=["Using the risk score", "Random calls"],
                range=[[1, 0], [6, 4]]), legend=None),
            tooltip=[alt.Tooltip("Customers contacted:Q", format=".0%"),
                     alt.Tooltip("Leavers found:Q", format=".0%")],
        ).properties(height=300), width="stretch")
    with b.container(border=True, key="card_method", height="stretch"):
        st.markdown("##### Choosing the method (August 2011)")
        v = S["validation"]
        df = pd.DataFrame({
            "Method": ["Random pick", "Recency only", "RFM model", "RFM + timing (used)"],
            "Correct in top-10% list": [v["base_rate"], v["recency"]["precision"],
                                        v["rfm"]["precision"],
                                        v["rfm_timing"]["precision"]],
            "c": [GRAY, RASP, RASP, AMBER]})
        st.altair_chart(bar_chart(df, "Method", "Correct in top-10% list", "c",
                                  "", "Share of list who really stopped", height=300),
                        width="stretch")

    with st.container(border=True, key="card_drivers"):
        st.markdown("##### What the score looks at")
        st.caption("Bigger bar = stronger effect. Left makes a customer safer, "
                   "right makes them riskier.")
        d = drivers.assign(Effect=np.where(drivers["coef"] > 0, "Raises risk",
                                           "Lowers risk"))
        st.altair_chart(alt.Chart(d).mark_bar(cornerRadius=4).encode(
            y=alt.Y("label:N", sort="x", title=None,
                    axis=alt.Axis(labelLimit=320, labelFontSize=13, labelOverlap=False)),
            x=alt.X("coef:Q", title="Effect on risk"),
            color=alt.Color("Effect:N", scale=alt.Scale(
                domain=["Raises risk", "Lowers risk"], range=[RASP, GRAY]),
                legend=alt.Legend(orient="top", title=None)),
            tooltip=["label", alt.Tooltip("coef:Q", format="+.2f"), "Effect"],
        ).properties(height=300), width="stretch")
    st.caption(":material/info: Limits: one shop and one year of data. Seasons shift "
               "the numbers, so re-check the score every quarter. The score says *who* "
               "is at risk, not *why* they leave - your conversation finds that out.")

# --------------------------------------------------------------- footer ----
st.space("medium")
st.caption(f"UCI Online Retail data · scored {score_date:%d %b %Y} with the model frozen "
           f"after August 2011 validation · refresh with `python run_all.py`",
           text_alignment="center")
