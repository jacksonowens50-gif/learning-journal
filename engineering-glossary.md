# Engineering glossary

Terms I've heard in meetings, defined so I could say them out loud to a CFO.
Started Day 13 (Week 4). Living document — add to it all summer.

**Rule:** if a definition needs a second undefined term, it isn't finished.

---

## Environments and shipping

### Deploy
Taking code that works on someone's laptop and putting it where users can reach
it. It's an *event*, and events can go wrong — which is why `rollback` exists.
*Heard when:* "that fix is deployed." *First question back:* deployed **where** —
staging or prod?

### Prod (production)
The live environment real users touch, holding real data. The word carries a
tone: "is this prod?" means "can I break something that matters?"
*Heard when:* "don't run that against prod."

### Staging
**Two different meanings — know which room you're in.**

1. *Infrastructure sense (this week):* a full copy of production used to test a
   release before it goes live. Same code, same shape, fake or copied data, no
   real users. The dress rehearsal.
2. *Data-warehouse sense (Week 7):* the landing zone where raw data sits before
   it's transformed. A "staging table" is this one.

Same word, unrelated concepts. In a deploy conversation it means #1.

### Rollback
Reverting to the last known-good version after a bad deploy. **Code rolls back
easily; database migrations often don't** — once the data has changed shape,
going backward can lose information. That asymmetry is why migrations get
treated more carefully than code.

### CI/CD
*Continuous Integration / Continuous Delivery.* CI: every time someone commits,
automated tests run against the combined code, so you find out in minutes
instead of at the end of the project. CD: if the tests pass, it ships
automatically. The point of both is to make deploying **boring**.
*FP&A parallel:* CI is a control that runs on every journal entry, not a
quarterly review.

### Environment variable
A setting handed to the code from outside, by the environment it's running in —
so the same code runs in dev, staging, and prod with different values.
*I've used this:* `FRED_API_KEY` in `econ-report`. Two reasons it exists:
secrets stay out of the repo, and one codebase serves every environment.

### Container
An app packaged with everything it needs to run — libraries, dependencies,
config — as one unit that behaves identically on any machine. Kills "works on my
machine." Docker is the common one. Lighter than a virtual machine because it
shares the host's operating system rather than carrying its own.

---

## Speed and scale

### Latency
The **delay before** a response starts — not how much data moves, how long until
the first byte does. *Heard when:* "the dashboard has high latency."
*First question back:* latency **where**?

### Throughput
How much work actually gets **completed** per unit time — requests/sec, rows/sec.
Not the same as load (load is demand; throughput is completion rate).
Latency and throughput are independent: a nightly ETL job is high-throughput and
high-latency; a chat app is the reverse.

### Cache
A saved copy of an expensive answer, kept close, so the work isn't redone.
Exists at **four different layers** — browser, CDN, application, database — and
"we'll just cache it" means four different projects depending on which was meant.
The permanent problem isn't storing the copy, it's knowing when it's stale.

### CDN
Servers distributed geographically that hold copies of static files and serve
each user from the nearest one. Two wins: distance (a cross-country round trip
costs ~70ms and no code beats physics) and offload (the origin never sees those
requests). *Failure mode:* users see the old version after a fix shipped.

### Load balancer
The public front door — it holds the address DNS handed back, spreads requests
across a pool of servers, and health-checks them so traffic skips any that stop
answering.
*Heard when:* intermittent failures that a refresh fixes.

### Scale up vs. scale out
**Up:** make one machine bigger. **Out:** add more machines. Out is generally
preferred — up has a hard ceiling (the biggest server money can buy) and gives no
redundancy. But out only works if the app is **stateless**, which is why that
term matters.

---

## The request itself

### Endpoint
One specific address that does one specific thing. An **API** is the whole
interface; an **endpoint** is a single door within it.
*I've used this:* `fred.stlouisfed.org/fred/series/observations` is the endpoint
I hit for observations — `/fred/series` is a different one. Together they're the
FRED API.

### Payload
The actual content of a message, as opposed to the headers wrapping it. The
letter, not the envelope.

### Status code
The three-digit verdict on a request. 2xx worked, 3xx moved, 4xx **you** asked
wrong, 5xx **they** broke. *First question back:* 4xx or 5xx — that's which side
of the frontend/backend line to start looking on.

### Timeout
A limit **you set** on how long you'll wait before giving up. It's a choice, not
an event — without one, a hung request hangs forever.
*I've used this:* the `timeout=` argument in `extract.py`.

### Rate limit
A cap on how many requests you may make in a time window. Exceed it and you get
back a `429`. Exists to stop one client from monopolizing a service.
*Heard when:* a nightly job that worked for a year starts failing — usually the
data volume grew past the cap.

### Stateless
The server keeps no memory between requests; each request must carry everything
needed to handle it. That's why tokens and cookies exist — the client
re-presents its identity every time. It's also what makes scaling out possible:
if no server remembers you, any server can take your next request.

### Port
A numbered door on a machine. One IP address hosts many services; the port says
which one you want. 443 = HTTPS, 80 = HTTP, 5432 = Postgres. When something runs
at `localhost:8000`, 8000 is the port. *Coming up Day 15 with FastAPI.*

---

## Data side

### Schema
The **structure**, not the data: what tables exist, what columns they have, what
types those are, how they relate. The blueprint, not the building.
*Second meaning:* in Postgres, a schema is also a namespace that groups tables.
*Third:* for an API, the expected shape of a JSON payload.

### Migration
A versioned **change to the schema** — add a column, change a type, rename a
table — written as code and applied in order so every environment ends up
structurally identical. **Not moving data**; that's ETL. This is the thing that's
hard to roll back.

### Index
A separate lookup structure that lets the database find rows without scanning
every one — like the index at the back of a book. **The tradeoff:** faster reads,
slower writes (every insert must update the index too) and more storage.

### Replica
A copy of a database kept continuously in sync with the primary, used to serve
reads so the primary isn't hammered by them. **This is one of the standard
answers to "why not report off prod?"**

### ETL
Extract, Transform, Load — pull data from source systems, reshape it, write it
somewhere built for analysis. What `econ-report` does.

---

## Failure and operations

### Uptime
The **percentage** of a period a system was available. It's a number, which is
what makes it contractible. 99.9% = 8.8 hrs down per year. 99.99% = 53 minutes.

### Downtime
The inverse — time unavailable. Usually discussed as *planned* (a maintenance
window) vs. *unplanned* (an incident), and only the second one is a failure.

### SLA
*Service Level Agreement.* A contractual promise about uptime, latency, or
support response, usually with penalties — service credits — when missed.
*Heard when:* "what's your SLA on the nightly refresh?" That is a question about
what you'll commit to **in writing**, not what you hope happens.

### Logs
The running record the application writes as it works — what it did, when, and
what went wrong. When something breaks, this is the evidence. "Check the logs"
is the first move in any incident.

### Monitoring
Continuous automated observation of health metrics, with **alerts** when
something crosses a threshold. The difference from logs: logs tell you what
happened once you go look; monitoring tells you something is wrong **without**
you looking.
