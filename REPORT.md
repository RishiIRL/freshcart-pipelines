# From Git to Gold: End-to-End Data Engineering Pipelines

**Roll No:** 23BCS067  
**Name:** RishiIRL  
**Date:** 2026-11-15  

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Part A — Git, CI/CD, and Testing](#2-part-a--git-cicd-and-testing)
   - [A1. Create the Repository](#a1-create-the-repository)
   - [A2. Where does each command act?](#a2-where-does-each-command-act)
   - [A3. A small CI workflow](#a3-a-small-ci-workflow)
3. [Part B — FreshCart ELT on Snowflake](#3-part-b--freshcart-elt-on-snowflake)
4. [Part C — Mage ML Pipeline](#4-part-c--mage-ml-pipeline)
5. [Part D — RabbitMQ Event Streaming](#5-part-d--rabbitmq-event-streaming)
6. [Part E — Report Summary](#6-part-e--report-summary)
7. [Bonus](#7-bonus)
8. [Conclusion](#8-conclusion)

---

## 1. Introduction

This report documents the design, implementation, and validation of an end-to-end data engineering pipeline for a fictional e-commerce company called **FreshCart**. The assignment is divided into five parts:

- **Part A:** Version control with Git, CI/CD with GitHub Actions, and automated testing with pytest.
- **Part B:** Extract-Load-Transform (ELT) on Snowflake.
- **Part C:** Machine learning pipeline with Mage.
- **Part D:** Event streaming with RabbitMQ.
- **Part E:** Formal report.

---

## 2. Part A — Git, CI/CD, and Testing (15 marks)

### A1. Create the Repository (5 marks)

The repository was created on GitHub as `RishiIRL/freshcart-pipelines` (public, default branch `main`).

**Directory Structure:**
```text
freshcart-pipelines/
├── .github/workflows/ci.yml
├── .gitignore
├── requirements.txt
├── README.md
├── elt/
│   └── freshcart_elt.ipynb
├── iris_project/
│   ├── __init__.py
│   ├── README.md
│   └── transformers/
│       ├── __init__.py
│       └── prepare_data.py
├── stream/
│   └── README.md
└── tests/
    └── test_prepare_data.py
```

**Git Log (`git log --oneline`):**
```text
bc1de37 fix: restore test_size=0.2 to make CI green again
b136e43 chore: temporarily break test_size to 0.3 for red CI run demo
6571b01 fix: set PYTHONPATH=. in CI workflow for module resolution
6b5d014 fix: add transformers __init__.py for package resolution
50e70cd fix: drop mage-ai from requirements so CI pip install passes; extend .gitignore
59d79c8 feat: initial project structure, requirements, CI workflow and test
```

---

### A2. Where does each command act? (4 marks)

| Command | Where the change happens | What exactly happens? |
| :---- | :---- | :---- |
| `git init` | Local machine (working directory) | Initializes a new hidden `.git` directory, turning the folder into a local Git repository. |
| `git add train.py` | Working directory → Staging area | Stages the changes of `train.py` so they are marked to be included in the next commit. |
| `git commit -m "msg"` | Staging area → Local repository | Records a snapshot of the staged changes permanently in the local repository history with a commit message. |
| `git remote add origin URL` | Local repository configuration | Links the local repository to a remote repository URL so local commits can be synced. |
| `git push -u origin main` | Local repository → Remote repository (GitHub) | Uploads local commits from the `main` branch to the remote repository (`origin`). |
| `git pull origin main` | Remote repository → Local repository (working directory) | Fetches changes from the remote `main` branch and merges them into the local working copy. |

**Question:** After running `git commit`, can your teammate see your code on GitHub? Why or why not?  
**Answer:** No, because `git commit` only saves the snapshot to your **local** repository on your machine. To make it visible to teammates on GitHub, you must subsequently run `git push` to transfer those commits to the remote repository.

---

### A3. A small CI workflow (6 marks)

- **CI Workflow (`.github/workflows/ci.yml`):** Automatically triggers on every push to check out code, set up Python 3.12, install dependencies, and run `pytest`.
- **Test (`tests/test_prepare_data.py`):** Asserts 120 train and 30 test samples from `load_iris()`.
- **Red/Green Demonstration:**

  **Red Run** (`test_size=0.3` → 84/36 split, test fails on `assert 84 == 120`):

  ![A3 Red Run — CI failure](screenshots/A3-red_run.png)

  **Green Run** (`test_size=0.2` restored → 120/30 split, test passes):

  ![A3 Green Run — CI success](screenshots/A3-green_run.png)

---

## 3. Part B — FreshCart ELT on Snowflake (30 marks)

The pipeline runs in a Colab notebook (`elt/freshcart_elt.ipynb`). It **extracts** mock API data (or calls the real APIs) into gzipped JSON files in `landing/`, **loads** them into Snowflake with `PUT` + `COPY INTO` into `bronze.orders_raw`, **transforms** with SQL files (`00_setup`, `10_silver_orders_clean`, `20_silver_orders_dedup`, `30_dim_customers_scd2`, `31_ref_fx_daily`, `32_ref_pincode_geo`, `40_gold_fct_orders`), and **checks** with `quality_checks()` plus `ops.run_log`.

Two notebook versions exist for the graded edits:

| File | Purpose |
| :--- | :--- |
| `elt/freshcart_elt.ipynb` | **Baseline** — the original notebook, run top-to-bottom for B1/B2. |
| `elt/freshcart_elt_edited.ipynb` | **Edited** — same notebook with the B3 validation rule, the B4 CRM event, and the B5 quality check added. |

---

### B1. Baseline run (5 marks)

Notebook executed top-to-bottom with my own Snowflake account (`SE21223`, role `ACCOUNTADMIN`, warehouse `FRESHCART_WH`, database `FRESHCART`). One `--mock --run-date 2026-09-30` run produces exactly the expected numbers:

| Check | Expected | Actual |
| :---- | :--------: | :-----: |
| Raw order rows in bronze after one run | 8 (6 web + 2 mobile) | **8** |
| Rows that pass cleaning (`silver.orders_clean`) | 6 | **6** |
| Rows in quarantine | 2 (ORD-1004, ORD-1006) | **2** |
| Orders after deduplication | 4 | **4** |
| Final gold line | 4 orders, revenue ₹7,785.00, 126 loyalty points | **4 orders, revenue ₹7,785.00, 126 loyalty points** |
| Share of rows rejected | 25% | **25%** (2/8) |

Re-running the notebook 4 times (run_ids 115156, 115231, 115236, 115939) grew bronze by 8 rows per run (32 total) while gold stayed at 4 orders / ₹7,785.00 / 126 points — idempotency confirmed.

*Screenshots: to be inserted from the Colab run (run log + gold totals).*

---

### B2. Hand-trace of ORD-1003 and ORD-1005 (6 marks)

**ORD-1003 — two raw records, one survivor:**

1. **Bronze (`bronze.orders_raw`)** — the web API sends flat snake_case JSON; the mobile API sends nested camelCase JSON. That is why the two records look different:
   - Web row: `{"order_id": "ORD-1003", "cust_email": "meera@outlook.com", "cust_name": "MEERA S", "order_date": "2026-09-02", "amount": null, "currency": "INR", "pincode": "400050", "updated_at": "2026-09-02 09:10:00"}`
   - Mobile row: `{"orderId": "ORD-1003", "customer": {"email": "Meera@Outlook.com", "name": "Meera S"}, "orderDate": "02/09/2026", "total": {"value": "2,100.00", "currency": "INR"}, "deliveryPin": "400050", "updatedAt": "2026-09-02T18:40:00"}`

2. **Into `silver.orders_checked`** — the `unified` CTE maps both shapes with a `UNION ALL`: web uses `raw:order_id`, `raw:cust_email`, `raw:order_date`, `raw:amount`, `raw:currency`, `raw:pincode`, `raw:updated_at`; mobile uses `raw:orderId`, `raw:customer.email`, `raw:orderDate`, `raw:total.value`, `raw:total.currency`, `raw:deliveryPin`, `raw:updatedAt`. The `typed` CTE then normalises both: `LOWER(TRIM(email))`, `INITCap(name)`, `TRY_TO_DATE` over three formats, and `TRY_TO_DECIMAL(REGEXP_REPLACE(amount, '[^0-9.-]', ''))`. Both rows now share one column set; the web row has `amount = NULL` (allowed, flagged later via `amount_missing`), the mobile row has `amount = 2100.00`.

3. **Dedup (`sql/20_silver_orders_dedup.sql`)** keeps the **mobile** copy because of `QUALIFY ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY updated_at DESC, ingest_seq DESC) = 1` — the later-updated mobile row (updated_at 2026-09-02 18:40) wins over the web row (09:10). Note the web null-amount row is *not* quarantined (NULL amount is allowed); it is simply out-ranked.

4. **Gold arithmetic** — the surviving row joins `dim.customers_scd2` (Meera = Platinum), `ref.tier_multiplier` (Platinum = 3), `ref.fx_daily` (INR→INR rate 1.0) and `ref.pincode_geo` (400050 = Mumbai):
   - `amount_inr = ROUND(2100.00 × 1.0, 2) = 2100.00`
   - `loyalty_points = FLOOR(2100.00 / 100) × 3 = 21 × 3 = 63`
   - `is_high_value = (2100.00 >= 2000) = TRUE`

**ORD-1005 vs ORD-1001 (Priya, two tiers):** Priya's CRM history has two periods — Silver from 2023-04-10, Gold from 2026-09-03. ORD-1001 was placed 2026-09-01 (Silver period), ORD-1005 on 2026-09-03 (Gold period). The responsible table is **`dim.customers_scd2`** and the join condition is **`o.order_date BETWEEN c.valid_from AND c.valid_to`** in `sql/40_gold_fct_orders.sql` (point-in-time lookup). So ORD-1001 earns `FLOOR(1250/100) × 1 = 12` points at the Silver multiplier, while ORD-1005 earns `FLOOR(899/100) × 2 = 8 × 2 = 16` points at the Gold multiplier.

---

### B3. Add a validation rule (6 marks)

**Change made** in `elt/freshcart_elt_edited.ipynb` cell 11 (`sql/10_silver_orders_clean.sql`), inside `ARRAY_CONSTRUCT_COMPACT(...)`:

```sql
IFF(currency NOT IN ('INR', 'USD'), 'unsupported_currency', NULL),
```

- **ORD-1006 reasons before:** `['bad_email', 'bad_pincode']`
- **ORD-1006 reasons after:** `['bad_email', 'bad_pincode', 'unsupported_currency']` *(from Colab re-run)*
- **Gold total change:** **No.** ORD-1006 was already quarantined before the change (bad email + bad pincode), so it never reached `silver.orders_clean`, the dedup layer, or the gold MERGE. Adding a third reason only enriches the quarantine record; the 4 gold rows / ₹7,785.00 / 126 points are untouched.
- **Second quarantine row?** **No.** The deciding SQL is the `NOT EXISTS` guard in the quarantine `INSERT` in `sql/10_silver_orders_clean.sql`:
  ```sql
  AND NOT EXISTS (
        SELECT 1 FROM quarantine.orders q
        WHERE q.source = c.source
          AND EQUAL_NULL(q.order_id, c.order_id)
          AND EQUAL_NULL(q.row_data:updated_at::TIMESTAMP_NTZ, c.updated_at))
  ```
  ORD-1006 is already in `quarantine.orders` with the same `(source, order_id, updated_at)`, so the second run skips it.

---

### B4. Change history and idempotency (7 marks)

**Change made** in `elt/freshcart_elt_edited.ipynb` cell 6 (`mock_data.py`), appended to `CRM_TIER_EVENTS`:

```python
{"cust_id": "CUST-02", "email": "arjun.k@yahoo.in", "tier": "Gold", "effective_from": "2026-08-15"},
```

**Prediction before running** (written before execution):

| Quantity | Prediction |
| :---- | :---- |
| Rows for CUST-02 in `dim.customers_scd2` | 2 (Silver 2024-01-15 → 2026-08-14; Gold 2026-08-15 → 9999-12-31) |
| Tier used for ORD-1002 | Gold |
| Loyalty points for ORD-1002 | 70 (`FLOOR(3536.00 / 100) × 2 = 35 × 2`) |
| Total loyalty points in gold | 161 (12 + 70 + 63 + 16) |
| Number of gold rows whose `published_at` changed | 1 (only ORD-1002's row_hash changes) |

**Actual after run** *(to be filled from Colab output)*:

| Quantity | Actual |
| :---- | :---- |
| Rows for CUST-02 in `dim.customers_scd2` |  |
| Tier used for ORD-1002 |  |
| Loyalty points for ORD-1002 |  |
| Total loyalty points in gold |  |
| Number of gold rows whose `published_at` changed |  |

**Why gold is safe to re-run but bronze grows:** the gold `MERGE` in `sql/40_gold_fct_orders.sql` keys on `order_id` and compares a `row_hash` built from every output column (`HASH(order_date, cust_id, email, tier, multiplier, amount, currency, fx_rate, amount_inr, loyalty_points, is_high_value, city, state, region, updated_at)`). A re-run that produces identical rows leaves `row_hash` equal, so neither `WHEN MATCHED AND t.row_hash <> s.row_hash` nor `WHEN NOT MATCHED` fires — nothing doubles. Bronze, by contrast, is a raw landing table loaded with `COPY INTO ... OVERWRITE=FALSE`, which intentionally appends every extracted file (Snowflake remembers each file for 64 days, so re-extracting the same sample adds 8 fresh rows each run). Bronze is meant to be an append-only history; silver/gold are where deduplication and idempotent MERGE keep the business truth stable.

---

### B5. Add one data-quality check (6 marks)

**Chosen check** (option b): *gold orders with `loyalty_points < 0`.* Added to `quality_checks()` in `elt/freshcart_elt_edited.ipynb` cell 9 (`run_pipeline.py`) as the sixth entry:

```python
("gold orders with negative loyalty points",
 "SELECT COUNT_IF(loyalty_points < 0) FROM gold.fct_orders", lambda v: v == 0, "fail"),
```

It is severity `fail`, so any negative value stops the pipeline, not just a WARN.

**Forced-fail probe** *(from Colab: mock order inserted, PROBLEM output shown, then removed)*:
- Mock order used: *(to be inserted)*
- PROBLEM output: *(to be pasted)*
- After removal: check returns to 0 / OK.

**ELT vs ETL (3–4 sentences):** For FreshCart, ELT wins because the raw JSON from two differently-shaped APIs must land somewhere untouched before we know which rules will change — the currency list, tier multipliers and pincode lookups all evolved during this assignment, and re-running the SQL against bronze is far cheaper than re-writing an external transform each time. Snowflake also does the heavy cleansing, dedup and SCD2 joins at scale inside the warehouse, so there is no separate transform engine to operate or pay for. ETL would still win in one situation: when a downstream system cannot tolerate even briefly-exposed bad data — e.g. pushing orders straight into a payment/ledger system where a negative amount or a bad email would cause a real-world failure before any SQL check could catch it; there the transform must happen *before* the load.

---

## 4. Part C — Mage ML Pipeline (25 marks)

*Pending — requires Mage installation.*

---

## 5. Part D — RabbitMQ Event Streaming (20 marks)

*Pending — requires RabbitMQ broker.*

---

## 6. Part E — Report Summary (10 marks)

*To be completed after all parts are validated.*

---

## 7. Bonus (10 marks)

*Optional.*

---

## 8. Conclusion

Part A is fully implemented and validated with CI/CD and pytest. Ready for Part B.
