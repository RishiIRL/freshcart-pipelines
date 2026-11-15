Data Engineering · Pipeline Orchestration

**Assignment: From Git to Gold**

*Version control, ELT, ML pipelines and event streaming, end to end*

| Item | Details |
| :---- | :---- |
| Course | Data Engineering |
| Total marks | 100 (+10 bonus) |
| Mode | Individual (or pairs, if permitted by the instructor) |
| Platform | Google Colab, a Snowflake trial account, a GitHub account |
| Release date | \_\_\_\_\_\_\_\_\_\_\_\_ |
| Due date | \_\_\_\_\_\_\_\_\_\_\_\_ |

# **1\. Overview**

In class you saw four separate pieces of a modern data platform: **Git and CI/CD** (how code moves from your laptop to a server), the **FreshCart ELT pipeline** (raw API data → Snowflake bronze → silver → gold), the **Mage ML pipeline** (an Iris classifier built from blocks with quality tests between them), and the **Zomato-style food-order stream** (a dispatcher publishing orders to drivers through a RabbitMQ topic exchange).

In this assignment you will run each piece, change it, break it on purpose, and explain what happened. The final part asks you to connect them into one story.

## **Learning outcomes**

After completing this assignment you should be able to:

1. Explain where Git stores your work at each step (working folder, staging area, local repository, remote) and set up a basic CI workflow.

2. Explain the difference between ETL and ELT, and trace a record through bronze, silver, quarantine and gold layers.

3. Write validation rules, deduplication logic and data-quality checks in SQL, and show that a pipeline is safe to re-run (idempotent).

4. Build an ML pipeline from orchestrated blocks, pass parameters at run time, and use tests to stop bad results from being saved.

5. Design topic-based message routing with binding patterns, and explain why acknowledgements (ACK/NACK) matter.

# **Part A: Git and CI/CD (15 marks)**

Reference: the four-box flow from the CI/CD slides: **Working folder → Local Git → Remote Git → CI/CD**.

## **A1. Create the repository (5 marks)**

Create a GitHub repository named freshcart-pipelines with this structure:

freshcart-pipelines/  
├── README.md  
├── .gitignore              \<- must ignore .env, \*.pkl, \*.csv, mage.log, \_\_pycache\_\_/  
├── requirements.txt  
├── elt/                    \<- your FreshCart notebook (Part B)  
├── iris\_project/           \<- your Mage project (Part C)  
├── stream/                 \<- your dispatcher and driver scripts (Part D)  
├── tests/  
│   └── test\_prepare\_data.py  
└── .github/workflows/ci.yml

Make at least **five meaningful commits** over the course of the assignment (not one big commit at the end). Paste the output of git log \--oneline into your report.

## **A2. Where does each command act? (4 marks)**

Copy and complete this table in your report. For the last column, write one sentence in your own words.

| Command | Where the change happens | What exactly happens? |
| :---- | :---- | :---- |
| git init |  |  |
| git add train.py |  |  |
| git commit \-m "msg" |  |  |
| git remote add origin URL |  |  |
| git push \-u origin main |  |  |
| git pull origin main |  |  |

Then answer: after running git commit, **can your teammate see your code on GitHub? Why or why not?**

## **A3. A small CI workflow (6 marks)**

Write one pytest test for the Mage prepare\_data block from Part C. The block file can be imported outside Mage (that is why it imports the decorators only if they are missing).

\# tests/test\_prepare\_data.py  
from sklearn.datasets import load\_iris  
from iris\_project.transformers.prepare\_data import transform  
   
def test\_split\_is\_80\_20():  
    df \= load\_iris(as\_frame=True).frame  
    out \= transform(df)  
    assert (out\["split"\] \== "train").sum() \== 120  
    assert (out\["split"\] \== "test").sum() \== 30

Add .github/workflows/ci.yml that runs on every push: check out the code, set up Python 3.12, install requirements.txt, run pytest. Submit:

* a screenshot of a **green** (passing) run in the GitHub Actions tab;

* a screenshot of a **red** (failing) run, made by temporarily changing test\_size in prepare\_data.py to 0.3, followed by the commit that fixes it.

# **Part B: FreshCart ELT on Snowflake (30 marks)**

Reference: the FreshCart notebook and flow chart. The pipeline is **Extract** (sample API data → raw files), **Load** (PUT \+ COPY INTO → bronze), **Transform** (SQL → silver, dim, ref, gold) and **Check** (quality\_checks()).

## **B1. Run the baseline (5 marks)**

Run the notebook top to bottom with your own Snowflake account. Confirm these numbers and include screenshots of the outputs:

| Check | Expected |
| :---- | :---- |
| Raw order rows in bronze after one run | 8 (6 web \+ 2 mobile) |
| Rows that pass cleaning (silver.orders\_clean) | 6 |
| Rows in quarantine | 2 (ORD-1004, ORD-1006) |
| Orders after deduplication | 4 |
| Final gold line | 4 orders, revenue ₹7,785.00, 126 loyalty points |
| Share of rows rejected | 25% |

## **B2. Trace one record by hand (6 marks)**

Pick **ORD-1003** (it arrives twice: once from the website with no amount, once from the mobile app with ₹2,100.00 and a later updated\_at). Write a short trace that shows:

1. what the two raw records look like in bronze.orders\_raw, and why the field names differ;

2. which SQL expressions turn each one into the same columns in silver.orders\_checked;

3. which copy survives SQL\_20\_ORDERS\_DEDUP and why (refer to the QUALIFY ROW\_NUMBER() line);

4. how its amount\_inr and loyalty\_points in gold are calculated. Show the arithmetic.

Do the same, more briefly, for **ORD-1005**: explain why Priya earns points at the **Gold** multiplier for this order but at **Silver** for ORD-1001. Name the table and the join condition responsible.

## **B3. Add a validation rule (6 marks)**

FreshCart only accepts orders in INR and USD. In SQL\_10\_ORDERS\_CLEAN, add one more line inside ARRAY\_CONSTRUCT\_COMPACT(...) that adds the reason unsupported\_currency when the currency is anything else.

* Re-run the pipeline. Show the reasons array for ORD-1006 before and after your change.

* Does the gold total change? Explain why or why not.

* ORD-1006 is already in quarantine from the earlier run. Does your new run add a second quarantine row for it? Point to the part of the SQL that decides this.

## **B4. Change history and idempotency (7 marks)**

Add one new event to MOCK\_CRM\_TIER\_EVENTS: Arjun (CUST-02, arjun.k@yahoo.in) moves to **Gold** with effective\_from \= **2026-08-15**. Before running, **predict** the new values, then run and compare.

| Quantity | Your prediction | Actual after run |
| :---- | :---- | :---- |
| Rows for CUST-02 in dim.customers\_scd2 |  |  |
| Tier used for ORD-1002 |  |  |
| Loyalty points for ORD-1002 |  |  |
| Total loyalty points in gold |  |  |
| Number of gold rows whose published\_at changed |  |  |

Explain in 4–6 sentences how row\_hash and the MERGE statement make the gold table safe to re-run, and why bronze still grows by 8 rows on every run.

## **B5. Add one data-quality check (6 marks)**

Add a sixth check to quality\_checks() that should also be 0\. Choose one of:

* gold orders whose amount\_inr is NULL but amount is not NULL;

* gold orders with loyalty\_points \< 0;

* orders in silver.orders\_dedup whose order\_date is in the future.

Then **make your check fail on purpose** by adding a suitable mock order, show the PROBLEM output, and remove the mock order again. Finally, answer in 3–4 sentences: **for FreshCart, why is ELT a better choice than ETL, and in which one situation from the lecture would ETL still win?**

# **Part C: ML pipeline with Mage (20 marks)**

Reference: the Mage Iris notebook. The pipeline is load\_iris → prepare\_data → train\_model → save\_results, wired together in metadata.yaml, with a @test function after each block.

## **C1. Draw and run the pipeline (4 marks)**

Draw the block graph (by hand or in any tool) showing every block, its type (data\_loader / transformer / data\_exporter) and the test attached to it. Run mage run iris\_project iris\_classifier \--test and include the output.

## **C2. Tests as a gate (6 marks)**

Run the pipeline for max\_depth \= 1, 2, 3, 4 and 5 using \--runtime-vars. Before each run, delete iris\_predictions.csv. Fill in:

| max\_depth | Test accuracy | test\_accuracy passed? | iris\_predictions.csv created? |
| :---- | :---- | :---- | :---- |
| 1 |  |  |  |
| 2 |  |  |  |
| 3 |  |  |  |
| 4 |  |  |  |
| 5 |  |  |  |

Explain in your own words how a failing @test in train\_model stops save\_results from running. Why is this better than saving the file and checking it afterwards?

## **C3. Add the evaluation branch (5 marks)**

Add the evaluate\_model block from the notebook so that train\_model has **two** downstream blocks (save\_results and evaluate\_model). Show your edited metadata.yaml, the confusion matrix and the metrics table. Open the pipeline in the Mage UI (through the Cloudflare tunnel) and include a screenshot of the graph showing the branch.

## **C4. Your own block (5 marks)**

Add one new block of your choice, with its own @test. Keep it simple. Examples:

* a transformer after load\_iris that checks there are no missing values and exactly 3 classes;

* an exporter that writes the metrics table to iris\_metrics.csv;

* a second model (for example KNeighborsClassifier) as a parallel branch, with its accuracy printed next to the decision tree.

Commit the new block to your repository and make sure the CI from Part A still passes.

# **Part D: Food-order stream with RabbitMQ (20 marks)**

Reference: the Zomato stream slides. A dispatcher creates a request every few seconds with a routing key city.zone.type, publishes it to a **topic exchange**, and each driver receives it in a private queue if the key matches the driver’s binding pattern. \* matches exactly one word; \# matches zero or more words.

## **D1. Routing on paper (6 marks)**

The drivers and their binding patterns are:

| Driver | Binding pattern |
| :---- | :---- |
| Ravi | bangalore.koramangala.\* |
| Priya | bangalore.indiranagar.\* |
| Arjun | bangalore.\*.ride |
| Meena | bangalore.\*.food |
| Karthik | chennai.tnagar.food |
| Control | bangalore.\# |

For each routing key below, list every queue that receives the message, or write “dropped”.

| \# | Routing key | Receiving queues |
| :---- | :---- | :---- |
| 1 | bangalore.koramangala.food |  |
| 2 | bangalore.indiranagar.ride |  |
| 3 | bangalore.whitefield.ride |  |
| 4 | chennai.tnagar.food |  |
| 5 | chennai.whitefield.ride |  |
| 6 | bangalore.koramangala |  |

Question 6 has only two words. Explain carefully which patterns can and cannot match it.

## **D2. Build it (8 marks)**

Using Python and the pika library, write two scripts in stream/:

* dispatcher.py: every 2 seconds picks a random city (Bangalore or Chennai), zone and type (ride or food), builds the routing key and publishes a JSON message {"id", "city", "zone", "type", "ts"} to a topic exchange called rapido-dispatch.

* driver.py NAME PATTERN: declares a private queue, binds it with PATTERN, prints each request it receives and sends an ACK.

Run the dispatcher and at least three drivers for two minutes. Show console output proving that a key from D1 reached exactly the queues you predicted.

**Tip:** In Colab you can install a local broker with \!apt-get install \-y rabbitmq-server and start it with \!service rabbitmq-server start. A free hosted broker (for example a CloudAMQP free plan) also works; keep its URL out of Git.

## **D3. ACK and NACK (6 marks)**

Change driver.py so that a message missing the zone field is rejected with basic\_nack(requeue=False), and every other message is acknowledged with basic\_ack. Make the dispatcher send one bad message every 10 messages.

* Show that the bad messages are discarded and the good ones are processed.

* Answer: what happens to a message if the driver crashes **before** sending an ACK? What would happen with requeue=True for a message that is always bad?

# **Part E: Report and viva (15 marks)**

Submit a report of **no more than 8 pages** (excluding screenshots in the appendix) that contains:

1. Your answers to every question in Parts A–D, numbered as in this document.

2. One diagram showing how the four pieces fit together: code in Git, CI testing it, the ELT pipeline producing gold data, the ML pipeline training on data, and a stream feeding events.

3. A half-page reflection: one thing that broke, how you found the cause, and how you fixed it.

# **Bonus: Stream into the lakehouse (+10 marks)**

Connect Part D to Part B. Write a small consumer that receives FreshCart-style order messages from RabbitMQ, collects them for one minute, and writes them with write\_landing() as a raw file. Then call load\_file() and the transform SQL so the streamed orders reach gold.fct\_orders. Show that running the batch twice does not double the gold totals.

# **Submission**

| Item | Format |
| :---- | :---- |
| GitHub repository link (public, or shared with the instructor) | URL in the report |
| FreshCart notebook with all outputs visible | .ipynb in elt/ |
| Mage project and notebook with outputs | iris\_project/ and .ipynb |
| Stream scripts | stream/dispatcher.py, stream/driver.py |
| Report | PDF, named RollNo\_Name\_Pipelines.pdf |

# **Marking scheme**

| Part | Component | Marks |
| :---- | :---- | :---- |
| A | Repository structure and commit history | 5 |
| A | Git command table and explanation | 4 |
| A | Working CI workflow (green and red runs) | 6 |
| B | Baseline run with correct numbers | 5 |
| B | Record trace (ORD-1003, ORD-1005) | 6 |
| B | New validation rule | 6 |
| B | SCD2 change, predictions and idempotency explanation | 7 |
| B | New quality check and ETL vs ELT answer | 6 |
| C | Pipeline graph and run | 4 |
| C | Test-gate experiment table and explanation | 6 |
| C | Evaluation branch | 5 |
| C | Own block with test | 5 |
| D | Routing table on paper | 6 |
| D | Working dispatcher and drivers | 8 |
| D | ACK / NACK handling and answers | 6 |
| E | Report, integration diagram, reflection and viva | 15 |
|  | **Total** | **100** |
| Bonus | Stream into the lakehouse | \+10 |

**Academic integrity:** You may discuss ideas with classmates, but code, predictions and explanations must be your own. Predictions in B4 and D1 must be written **before** you run the code; the viva will check this.