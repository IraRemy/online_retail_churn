# Customer Follow-up in Online Retail

Final-year data science course project. **Question: which regular customers may
stop buying in the next 60 days?** The retailer has limited follow-up time, so
the system scores each regular customer from their last 90 days of purchases
and puts the top 10% most at-risk on a review list.

Data: [UCI Online Retail dataset](https://archive.ics.uci.edu/dataset/352/online+retail)
(UK online retailer, 1 Dec 2010 - 9 Dec 2011).

## How to run

```bash
pip install -r requirements.txt
python run_all.py
```

`run_all.py` downloads the dataset and runs every step. Each step is also an
independent script in `src/`, in this order:

| Step | Script | What it does |
|---|---|---|
| 0 | `download_data.py` | Download the UCI zip, convert xlsx to csv |
| 1 | `clean_data.py` | The 5 frozen cleaning rules (Week 3) |
| 2 | `explore.py` | Monthly activity + cohort retention charts (Week 3) |
| 3 | `snapshots.py` | Time-split snapshots, eligibility, features, target (Week 4) |
| 4 | `evaluate_validation.py` | Recency vs RFM vs RFM+timing on 1 Aug validation (Weeks 4-5) |
| 5 | `final_test.py` | Frozen model, run ONCE on the locked 1 Oct test; writes the follow-up list |
| 6 | `eda_risk.py` | Business-risk EDA: revenue concentration, new vs returning revenue, who stops buying |
| 7 | `score_latest.py` | Scores every regular at the latest date (10 Dec 2011) with the frozen model: the live follow-up list |

## Method (as presented in the Week 3+4 progress deck)

**Cleaning (5 rules):** remove missing CustomerID, exact duplicates,
cancellations (C-invoices), non-positive prices, and administrative codes
(POST, M, C2, DOT, BANK CHARGES). PADS is a real product and is kept.
Result: **391,153 invoice lines, 4,334 customers, 18,402 invoices**.

**Who we study:** at a cutoff date, customers with at least 3 purchase dates in
the previous 90 days and at least 1 purchase in the last 30 days. Target: no
purchase in the next 60 days (about 12% of eligible customers).

**Fair time split:** features use only the 90 days before each cutoff.
Train = 1 Apr / 1 May / 1 Jun 2011 (776 customer-snapshots), validation =
1 Aug 2011 (311), final test = 1 Oct 2011 (334, locked until the model is chosen).

**Models:** recency ranking; RFM logistic regression (recency, log frequency,
log spending, standardized); Week 5 adds timing features (usual gap, gap
spread, delay ratio). Main measure: precision in the top 10% shortlist,
reported next to the base rate because the test window is peak season.

## Results

Validation (1 Aug 2011, top 32 of 311, base rate 11.9%):

| Model | Correct | Precision | Lift | AP |
|---|---|---|---|---|
| Random pick | ~4 | 11.9% | 1.0 | - |
| Recency ranking | 9 | 28.1% | 2.4 | 0.19 |
| RFM model | 8 | 25.0% | 2.1 | 0.23 |
| RFM + timing (Week 5) | 10 | 31.2% | 2.6 | 0.27 |

The bootstrap 95% CI for the AP difference between RFM and recency is
[-0.11, +0.19]: includes zero, no clear winner between the baselines. The
timing features beat both baselines on validation, so RFM+timing was frozen
as the final model.

Final test (1 Oct 2011, used once, top 34 of 334, base rate 9.9%):
**7 of 34 correct (20.6%), lift 2.1x** over random follow-up.

## Business-risk EDA (eda_risk.py)

* Top 10% of customers hold **61%** of revenue (top 20% hold 75%): losing a
  few good customers hurts a lot.
* Returning customers bring **74%** of all revenue, yet **36%** of customers
  never buy a second time.
* Among eligible regulars, risk of stopping rises from 10% (bought this week)
  to 19% (3-4 weeks quiet), and falls from 20% (only 3 purchase dates) to 0%
  (9+ dates). Being "late" vs your own rhythm is not a signal on its own,
  which matches the Week 3 finding about the delay ratio.
* The final follow-up list covers about 22.5k GBP of 90-day customer spend
  (average 663 GBP per flagged customer).

## Deliverable

`outputs/followup_list.csv` - the top 10% most at-risk regular customers at
the final cutoff, ranked by risk score, with the features behind each score.
`outputs/test_scores_all.csv` has scores for every eligible customer.

## Final report deck

`report/Online_Retail_Final_Report_v2.pptx` - 12 projector-ready slides. Each
evidence slide pairs an EDA or result chart with "what the data says" and
"how this keeps customers". Rebuild:

```bash
python report/make_figures.py          # projector-size charts -> report/assets/
cd report && npm install && node make_deck.js
```

## Dashboard for business owners

```bash
streamlit run dashboard/app.py         # run from the project folder
```

Four plain-English tabs: **Who to contact** (adjustable list size, suggested
action per customer, CSV download), **Why customers leave** (EDA charts with
actions), **Look up a customer**, and **How reliable is this?** (locked-test
proof). It only reads `outputs/`; run `python run_all.py` first.
