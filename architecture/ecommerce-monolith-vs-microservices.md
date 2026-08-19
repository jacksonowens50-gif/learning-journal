# Cascade Gear Co. — two architectures, same company

**Cascade Gear Co.** — direct-to-consumer outdoor equipment, ~$180M revenue, sells on
their own site plus Amazon, one warehouse in Reno. FP&A team of four who want a daily
sales dashboard and a weekly margin report. Six people in IT, total.

Every pro and con below is judged against **that** company — not against Amazon, not
against a hyperscaler. Day 17.

---

## Diagram A — monolith + nightly batch ETL

Illustrated version: [`diagram-a-monolith-batch.png`](diagram-a-monolith-batch.png)

```
  +==================================================================+
  ||  THE BUSINESS RUNNING  (operational)                           ||
  ||                                                                ||
  ||   +--------------------------------------+                     ||
  ||   |  BROWSER / MOBILE APP                |                     ||
  ||   +--------------------------------------+                     ||
  ||          |                                                     ||
  ||          | HTTPS requests — all day, every day                 ||
  ||          v                                                     ||
  ||   +--------------------------------------+                     ||
  ||   |  CASCADE STORE  (the monolith)       |  ONE codebase.      ||
  ||   |                                      |  ONE deploy.        ||
  ||   |  catalog | cart | orders | payments  |                     ||
  ||   |  inventory | customers | shipping    |  <- these are       ||
  ||   |                                      |     MODULES, not    ||
  ||   |  they call each other as function    |     services. No    ||
  ||   |  calls: in-process, microseconds,    |     network between ||
  ||   |  no network, cannot fail separately  |     them.           ||
  ||   +--------------------------------------+                     ||
  ||          |                                                     ||
  ||          | reads / writes — milliseconds, all day              ||
  ||          v                                                     ||
  ||   +--------------------------------------+                     ||
  ||   |  PROD POSTGRES                       |  ONE database.      ||
  ||   |                                      |                     ||
  ||   |  customers, orders, order_items,     |  Foreign keys are   ||
  ||   |  products, inventory                 |  ENFORCED. An order ||
  ||   |                                      |  cannot point at a  ||
  ||   |  normalized — shaped for WRITING     |  customer that      ||
  ||   +--------------------------------------+  doesn't exist.     ||
  +==========|=======================================================+
             |
  ===========|============ THE BOUNDARY ==========================
             |
             | NIGHTLY, 2:00 - 2:40am
             | snapshot as of 23:59
             |
             |   ^^^ the ONLY arrow that crosses. Everything above
             |       is the business running; everything below is
             |       the business being described.
             v
  +==================================================================+
  ||  THE BUSINESS BEING DESCRIBED  (analytical)                    ||
  ||                                                                ||
  ||   +--------------------------------------+                     ||
  ||   |  ETL JOB                             |  extract            ||
  ||   |                                      |    -> transform     ||
  ||   |  owns the difference between how     |       -> load       ||
  ||   |  the app THINKS and how the          |                     ||
  ||   |  business ASKS                       |                     ||
  ||   +--------------------------------------+                     ||
  ||          |                                                     ||
  ||          | one load, once a night                              ||
  ||          v                                                     ||
  ||   +--------------------------------------+                     ||
  ||   |  WAREHOUSE  (Snowflake)              |  star schema        ||
  ||   |  denormalized — shaped for READING   |                     ||
  ||   +--------------------------------------+                     ||
  ||          |                                                     ||
  ||          | queries / extract refresh                           ||
  ||          v                                                     ||
  ||   +--------------------------------------+                     ||
  ||   |  TABLEAU / POWER BI                  |  FP&A opens this    ||
  ||   |                                      |  at 8am             ||
  ||   +--------------------------------------+                     ||
  +==================================================================+
```

### What to point at in a meeting

**1 — Every arrow has a cadence.** An unlabelled arrow is the number one lie in an
architecture diagram: it lets everyone in the room silently assume a different number.
Write the window down — *"2:00–2:40am, snapshot as of 23:59."* Not "nightly."

**2 — Modules are not services.** Every box inside the monolith is a folder, not a
server. They call each other as function calls: in-process, microseconds, no network,
no partial failure. The price is that they cannot be deployed separately — change one,
redeploy all of it. That is the entire trade, in one line, and it's the thing Diagram B
reverses.

**3 — The boundary is an asymmetry.** Prod goes down and Cascade stops taking money.
The warehouse goes down and four analysts are annoyed. That asymmetry is the whole
reason the ETL runs at 2am and not 2pm, and the reason the second database exists at
all. It's the Day 14 answer — *why not report off prod?* — drawn as a picture instead
of argued.

**4 — Shaped for writing vs. shaped for reading.** Postgres is normalized so the app
can write safely; Snowflake is denormalized so people can read fast. The ETL job is the
translation between them. Its real job description is not "move data" — it is *"own
the difference between how the app thinks and how the business asks."*

**5 — The defensible "as of."** Every number in the 8am report describes the same
frozen instant. That's what lets it tie to the GL: both are describing 23:59. A
continuously-updating dashboard has no such moment, which is why *"the number changed
while we were looking at it"* is a credibility event you do not recover from in a
board meeting.

---

## Diagram B — microservices + event streaming

Same company, same products, same customers. Only the plumbing changed.

Illustrated version: [`diagram-b-microservices-events.png`](diagram-b-microservices-events.png)

```
  +===================================================================================+
  ||  THE BUSINESS RUNNING  (operational)                                            ||
  ||                                                                                 ||
  ||                    +--------------------------------+                           ||
  ||                    |  BROWSER / MOBILE APP          |                           ||
  ||                    +--------------------------------+                           ||
  ||                                   |                                             ||
  ||                                   v                                             ||
  ||                    +--------------------------------+                           ||
  ||                    |  API GATEWAY                   |  one front door.          ||
  ||                    |  routes /orders -> order svc   |  routes by path.          ||
  ||                    +--------------------------------+                           ||
  ||                                   |                                             ||
  ||        +--------------+-----------+-----------+--------------+                  ||
  ||        |              |           |           |              |                  ||
  ||        v              v           v           v              v                  ||
  ||   +---------+   +-----------+ +----------+ +---------+  +----------+            ||
  ||   | ORDER   |<->| INVENTORY | | CUSTOMER | | PAYMENT |  | SHIPPING |            ||
  ||   +---------+ ^ +-----------+ +----------+ +---------+  +----------+            ||
  ||        |      |       |            |            |            |                  ||
  ||        v      |       v            v            v            v                  ||
  ||   +---------+ | +-----------+ +----------+ +---------+  +----------+            ||
  ||   | own DB  | | |  own DB   | |  own DB  | | own DB  |  |  own DB  |            ||
  ||   +---------+ | +-----------+ +----------+ +---------+  +----------+            ||
  ||        |      |       |    X       |    X      |    X       |                   ||
  ||        |      |       |            |           |            |                   ||
  ||        |      |       |   ^^^ NO FOREIGN KEYS ACROSS THESE LINES.               ||
  ||        |      |       |       Nothing stops the order service writing an        ||
  ||        |      |       |       order for a customer that does not exist.         ||
  ||        |      |       |                                                         ||
  ||        |      +------ this arrow used to be a FUNCTION CALL inside one           ||
  ||        |              process. It is now an HTTP request between two             ||
  ||        |              servers: it can time out, return stale data, be            ||
  ||        |              half-done, and it needs a retry policy.                    ||
  ||        |              |            |           |            |                   ||
  ||        +--------------+-----------+-----------+--------------+                  ||
  ||                                   |                                             ||
  ||        each SERVICE publishes events (past tense, immutable):                    ||
  ||        OrderPlaced · PaymentCaptured · OrderShipped · InventoryAdjusted          ||
  ||                                   |                                             ||
  ||                                   v                                             ||
  ||   +---------------------------------------------------------------------+       ||
  ||   |  KAFKA                                                              |       ||
  ||   |  topics: orders | inventory | customers | payments | shipments       |       ||
  ||   |                                                                     |       ||
  ||   |  an append-only LOG, not a queue — READING DOES NOT CONSUME.        |       ||
  ||   |  That is why analytics can be bolted on later without asking        |       ||
  ||   |  the order team's permission. You just start reading.               |       ||
  ||   |                                                                     |       ||
  ||   |  retention: 7 days   <-- how far back can you replay?               |       ||
  ||   +---------------------------------------------------------------------+       ||
  +============|=====================================|==============================+
               |                                     |
  =============|=====================================|=========== THE BOUNDARY ======
               |                                     |            (now always open)
               v                                     v
  +===================================================================================+
  ||  THE BUSINESS BEING DESCRIBED  (analytical)                                     ||
  ||                                                                                 ||
  ||   +------------------------+          +------------------------------+          ||
  ||   |  SINK CONNECTOR        |          |  OTHER CONSUMERS             |          ||
  ||   |  continuous — reads    |          |  fraud check · email ·       |          ||
  ||   |  the log, writes rows  |          |  search index                |          ||
  ||   +------------------------+          |  reading the SAME log,       |          ||
  ||        |                              |  independently, with no      |          ||
  ||        |                              |  load on any prod database   |          ||
  ||        v                              +------------------------------+          ||
  ||   +----------------------------------------+                                    ||
  ||   |  WAREHOUSE — RAW EVENT TABLES          |  one row per event.                ||
  ||   |                                        |  append-only. OUT OF ORDER.        ||
  ||   |                                        |  DUPLICATED (at-least-once).       ||
  ||   +----------------------------------------+                                    ||
  ||        |                                                                        ||
  ||        | dbt, every 15 min — dedupe, order, collapse events into current state   ||
  ||        v                                                                        ||
  ||   +----------------------------------------+                                    ||
  ||   |  WAREHOUSE — MODELLED MARTS            |                                    ||
  ||   +----------------------------------------+                                    ||
  ||        |                                                                        ||
  ||        v                                                                        ||
  ||   +----------------------------------------+                                    ||
  ||   |  TABLEAU / POWER BI                    |                                    ||
  ||   +----------------------------------------+                                    ||
  +===================================================================================+
```

### What to point at in a meeting

**1 — Five databases, no foreign keys.** Nothing stops the order service writing an
order for a customer the customer service has never heard of. In Diagram A the database
itself refused — that was the `IntegrityError` you deliberately let SQLite raise in
`mini-erp` so the rule lived in exactly one place. Here that mechanism does not exist.
The rule has to be re-implemented in application code, and **application code is not a
constraint, it is a promise.**

**2 — That line between two services is now a network call.** *"Do you have stock?"*
used to be a function call inside one process: microseconds, in-memory, either it ran or
the whole thing crashed. It is now an HTTP request between two servers. It can time out.
It can return stale data. It can succeed on one side and fail on the other. It needs a
retry policy, and the retry needs to be safe to run twice. **Every arrow between services
is a new way for the system to be half-done.**

**3 — Events are past tense.** `OrderPlaced`, not `PlaceOrder`. An event is a statement
that something *already happened* — immutable, timestamped, not refusable. That's
different from a command, which is a request that can be declined. It matters to you
because a stream of past-tense facts is an audit log you got for free: cycle times,
funnel analysis, and *"what did this look like at 3pm on the 14th"* without slowly-
changing-dimension gymnastics. This is the genuine reporting win in Diagram B.

**4 — Kafka is a log, not a queue, and retention is the question nobody asks.** Reading
does not consume. Ten consumers can read the same events independently, which is exactly
why analytics can be added later without asking a source team to build you an extract.
But write the retention number on the diagram and ask out loud: *if the sink connector
breaks on Friday and nobody notices until Wednesday, is the data still there?* At 7 days,
fine. At 24 hours, you have a permanent hole and the only recovery is asking five
different teams to re-emit history they probably didn't keep.

**5 — The JOIN didn't disappear. It moved, and it grew an owner.** *"Revenue by customer
segment by product category"* was one query in Diagram A. Here it happens in the
warehouse, after the fact, across five sources, on keys nobody guaranteed would match.
It is now a build — with an owner, a maintenance cost, and a place to be wrong. That
owner is the data consultant. This is the con to lead with.

**6 — Current state is derived now.** What lands is events, not rows: out of order,
at-least-once (so duplicated), ordered only *within* a partition. *"What is this order's
status"* used to be `SELECT status FROM orders`. It is now something you compute in dbt
— and getting the dedupe wrong double-counts revenue on a Tuesday.

## Comparison — from the data and reporting seat

One-page version to hand a client: [`comparison-reporting-seat.png`](comparison-reporting-seat.png)

Everything below is judged from the reporting seat. Engineering has its own list of pros
and cons for microservices and most of them are real — they're just not what a data
consultant is hired to have an opinion about.

### A — Monolith + nightly batch

**What helps you**

1. **One join answers the question.** "Revenue by customer segment by product category"
   is a query, not a project. Anyone who knows SQL can answer it today, without a meeting.
2. **The database enforces the rules, so your numbers tie.** An order can't point at a
   customer who doesn't exist — the database refuses to write it. You spend zero hours a
   month chasing orphaned records.
3. **Everything in the 8am report is from the same moment.** Every number describes 23:59
   last night. That's what lets it tie to the GL, and it's why nothing moves while you're
   presenting it.

**What hurts you**

1. **Yesterday is as fresh as it will ever get.** "Can we see today's orders?" has no
   answer that isn't a rebuild. Anything somebody acts on within the day — fulfillment,
   fraud, live promo tracking — is off the table by design.
2. **Reports and the live business share one machine.** A big query competes with
   customers checking out. That's why the load runs at 2am, and why the second database
   had to exist at all.
3. **The tables are built for the app, not for you.** A developer can rename a column in
   a sprint and break your pipeline without ever knowing your report exists. Nobody told
   them their schema was an interface. *(Worth saying out loud: microservices with a
   schema registry actually fix this one. Give the other side its win.)*

### B — Microservices + event streaming

**What helps you**

1. **Data lands all day, so freshness becomes a choice.** How current the dashboard is
   turns into a question about cost instead of a hard limit of the design. Same-day
   operational reporting becomes possible at all.
2. **You get the whole history, not just the current state.** A tells you the order's
   status is "shipped." B tells you it was placed 09:14, paid 09:14, picked 11:02,
   shipped 16:47. Cycle-time and funnel analysis come free, and they're genuinely hard to
   retrofit onto a nightly snapshot.
3. **New reports don't add load to the live systems.** You read the same stream everyone
   else reads. No asking a source team to build you an extract, and no extra queries
   hitting production.

**What hurts you**

1. **One source of truth becomes five.** "How many active customers do we have?" stops
   being a query and becomes a decision about which system is right. The join that was
   free in A now happens in the warehouse, after the fact, on keys nobody guaranteed
   would match.

   **The FP&A version, and use it out loud:** this is the difference between one
   consolidated GL and five subledgers in five systems with no elimination rules written
   yet. Nobody thinks the second one is free.

   **The control version, for an audit-minded client:** the foreign key in A is a
   *preventive* control — the transaction physically cannot commit. What B has instead is
   a *detective* control: a reconciliation that finds broken records after the fact and
   somebody repairs them. Detective controls are accepted all the time, and they're
   weaker, slower, and only work if someone actually runs them. That's the trade, in
   language a CFO already owns.

2. **The warehouse is briefly wrong on purpose.** Events arrive out of order and
   sometimes twice. Handle duplicates wrong and you double-count revenue. None of this is
   a bug — it's the documented behavior.

   The realistic failure is *timing*, not corruption: the customer genuinely was created,
   the event just hasn't landed yet. Order at 09:14:02, customer at 09:14:05. It heals
   itself. But if the dbt run fires at 09:14:03, that order shows on the dashboard with
   no customer segment. Not wrong forever — wrong *right now*, repeatedly, and nobody can
   reproduce it. **A wrong number gets fixed. A flickering one gets abandoned.**

3. **It takes a full-time person, and it fails quietly.** Kafka, a schema registry,
   connectors, dead-letter queues, replay procedures, monitoring on consumer lag. For six
   people in IT that's a platform engineer nobody budgeted for. And the failure mode is
   the bad kind: a failed nightly job is loud — the report is missing at 8am and someone
   calls you. A stalled stream is silent — the dashboard loads, looks right, and is four
   hours old.

### Why anyone would choose B at all

Not for the data. Almost never for the data.

The purchase is **teams not waiting on each other.** Picture 300 people working in one
giant Excel workbook: you can't send your tab until everyone else's tabs are finished and
working, and one broken formula on tab 40 blocks everybody. Split it into five files and
each team sends their own whenever they want.

Two smaller reasons come along with it: when one part breaks it doesn't kill the rest (a
crash in search doesn't take checkout down with it), and you only pay to scale the busy
part (40 more checkout servers on Black Friday, not 40 more copies of the admin reports
page).

**So the question to ask in a kickoff is not "is your system big."** It's *"how many
people work on this software, and do they wait on each other to release?"* Six people in
IT never wait on each other. They don't have the problem this solves, and they'd buy
every cost of B while collecting none of the benefit.

### The part almost nobody says out loud

It isn't a choice between these two.

- **Modular monolith** — one deploy, one database, but strict walls between the parts
  inside it. Most of the organisational benefit, none of the distributed cost. Usually
  the right answer for a company this size.
- **Strangler fig** — if you do split it up, you pull out one service at a time and route
  traffic through a façade in front. Nobody rewrites a working system all at once and
  survives it. Knowing the incremental path is worth more than knowing the tool names.
- **Distributed monolith** — services split apart that still have to be deployed together
  and can't run alone. Every cost of splitting, none of the benefit, and very common.
  This is what you're looking for when a client says they "moved to microservices."

**And the question that decides the streaming half of it, which is the FP&A question:**

> *What decision changes if this number is five minutes old instead of twelve hours old?*

If nobody acts before tomorrow morning, streaming bought latency nobody spends and bills
for it monthly. Most "we need real-time" requests mean "we need not-yesterday," and a
15-minute micro-batch covers that at a fraction of the cost. Asking that question *before*
the platform gets bought is the most valuable thing on this page.

## Where does a webhook fit?

One-pager: [`webhook-where-it-fits.png`](webhook-where-it-fits.png)

**What it is, in one line:** a reverse API call. Instead of you asking them, they tell you.

Without one, you poll. Your job calls Stripe every 15 minutes asking "anything new?" That's
96 calls a day and 95 of them come back with nothing. You're still up to 15 minutes behind,
you're burning their rate limit, and if their API is down you just collect errors. It works.
It's what you'd build first. It's just wasteful.

With one, Stripe POSTs to a URL you run, the moment the payment happens. One call per real
event, seconds later.

**You already built the receiving end.** A webhook receiver is a `POST` endpoint with a
shared secret — that's `POST /orders` from Day 15 plus `require_api_key` from Day 16, and
nothing else.

### Webhook vs. queue — not the same thing

| | Webhook | Queue / stream |
|---|---|---|
| Who starts it | they push | you pull |
| Buffer | none | yes — that's the point |
| You're down | retried a few times, then dropped | waits for you |
| Replay history | no | yes, from an offset |
| Many readers | each registers separately | all read the same log |

> **A webhook is a doorbell. A queue is a mailbox.** The doorbell does not remember that it rang.

Which is why the pattern that actually holds up in production is: **the receiver validates,
writes to a queue, and returns 200.** Do the real work behind it. If you process inline, a
slow database means you don't answer in time, they time out, they retry, and now you have
duplicates *and* an outage.

### Three places it fits at Cascade

1. **On Diagram A — and this is the answer a client actually needs.** Stripe and the Amazon
   channel are not inside Cascade's architecture and never will be. Stripe POSTs
   `payment.succeeded` to a small endpoint Cascade runs, which appends to a warehouse table.
   Result: near-real-time payments data with **no Kafka, no platform engineer, no migration.**
   Everything else still arrives nightly at 2am. One slice of the business goes fast and the
   rest keeps running exactly as it did.

   That's the 80/20 of event-driven for a mid-size company, and offering it is a much better
   consulting answer than "you should look at streaming."

2. **As a trigger instead of a schedule.** A `shipment.created` webhook kicks off the dbt run
   or a Tableau extract refresh instead of a fixed 2am cron. The pipeline runs when there's
   something to run for — which also means it stops quietly succeeding on days when nothing
   arrived.

3. **Between your own services, when there are only two of them.** Order service POSTs to
   shipping service. Fine and normal at small scale. Note the ceiling on the diagram though:
   it's point-to-point, so with N services you get N² integrations and no replay. The moment
   a third and fourth consumer want the same event, you've just discovered why the broker in
   Diagram B exists. That's the honest bridge between the two architectures.

### Four things any receiver must do — the client-conversation checklist

1. **Be reachable from the internet.** Someone else's server has to hit it. If the client's
   stack is entirely inside a corporate network, that's a firewall conversation before it's a
   code conversation — and it's the same conversation as Tableau Bridge in
   [`tableau-extract-lifecycle.md`](tableau-extract-lifecycle.md), arriving from the opposite
   direction. Bridge exists specifically so nothing has to reach *in*.
2. **Survive the same event twice.** Retries mean duplicates. Dedupe on their event ID or you
   will double-count revenue, and it will be a Tuesday.
3. **Check the signature.** Your `x-api-key` proves the caller knows a secret. A webhook
   signature (an HMAC over the body) proves the payload wasn't altered and really came from
   them. A public URL that accepts unsigned POSTs is a way for anyone on the internet to write
   rows into your warehouse.
4. **Answer 200 fast, do the work later.** The 200 means "received," not "processed." Same
   lesson as Day 16: a status code is a promise about what happened, and lying in it moves
   your problem into someone else's stack trace.

## Reading someone else's diagram

Reference card: [`reading-a-diagram.png`](reading-a-diagram.png)

The two diagrams above were mine to build. In October they'll be someone else's, already on
a screen when I walk in. This is the part that transfers.

### Seven questions to ask any diagram

1. **What's the cadence on each arrow?** Real-time, hourly, nightly, on demand? An
   unlabelled arrow is where everyone in the room is quietly assuming a different number.
2. **Is this arrow a request, or is it data moving?** They're drawn identically and they
   mean opposite things. "A calls B" and "data goes from A to B" can point in opposite
   directions on the same line.
3. **Where's the boundary?** What's inside their network, what's a SaaS product, what's ours
   to build. Usually not drawn, and it decides who needs to be in the room.
4. **Where does the data land, and is there a copy I'm allowed to report off?** If the answer
   is "report off prod," you already know how the next six months go.
5. **Where is each thing born?** Which box creates a customer? If two boxes do, you just
   found the reconciliation project nobody has mentioned yet.
6. **What's missing?** No monitoring box. No test environment. No box where transformation
   happens — so it's in a stored procedure somebody wrote in 2019. No auth boundary at all.
7. **Who owns each box — which team, not which tool?** The architecture ends up matching the
   org chart whether anyone wants that or not, so the diagram is also telling you about the
   people.

> **An architecture diagram is a claim about who has to be in the meeting.**

### When somebody says "orders flow through Kafka to the warehouse"

These are the follow-ups. Any three of them, asked in a kickoff, and you're not the reporting
person in the room any more.

- Is that the full row, or just what changed? *(state vs. CDC)*
- One topic per thing, or one firehose?
- What's the retention — and have you ever actually replayed it?
- At-least-once or exactly-once? Where does dedupe happen?
- Is there a schema registry? What happens today when a producer adds a field?
- What lands in the warehouse — raw JSON, or modelled tables? Who owns the modelling?
- What's the partition key? If it isn't `order_id`, status updates arrive out of order and
  whatever computes "current status" is sometimes wrong.

### Red flags — what makes you sit up

- **"We report straight off the production database."** The timeouts are already happening.
  Nobody has called it a problem yet.
- **"We moved to microservices."** Ask whether they can deploy one service without the
  others. Often the answer is no, which means it's a distributed monolith.
- **"It needs to be real-time."** Ask what decision it feeds. Usually nothing moves before
  tomorrow morning.
- **Two different boxes both create a customer.** That's the reconciliation project nobody
  has funded or mentioned.
- **No box on the diagram does transformation.** It's in a stored procedure from 2019 and
  exactly one person knows it.

### And the one nobody else asks

> *"How many people work on this software, and do they wait on each other to release?"*

That answer — not data volume, not revenue — is what says whether any of this was ever
warranted. Splitting a system up buys teams the ability to ship without waiting on each
other. Six people in IT never wait on each other. They don't have the problem, so there's
nothing here for them to fix.
