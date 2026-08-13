# Request lifecycle — espn.com

What happens between typing `espn.com` and seeing scores on the page.
Client = my laptop (Chrome). Server = ESPN.

---

## Round 1 — get the page

```
        (1) DNS — a LOOKUP, not a hop. Nothing travels "through" DNS.
            browser cache -> OS cache -> resolver -> root -> .com -> authoritative
            answer: "espn.com = 23.55.x.x", cached for TTL seconds
            (this is why the 2nd visit of the day skips this whole step)
                                |
                                v
  +----------------------------------+
  |  CLIENT                          |
  |  my laptop - Chrome              |
  +----------------------------------+
       |                          ^
       | (2) TCP connect,         | (9) 200 OK
       |     TLS handshake,       |     + HTML document
       |     then GET /           |
       v                          |
  +----------------------------------+
  |  LOAD BALANCER                   |
  +----------------------------------+
       |                          ^
       | (3) pick one healthy     | (8)
       |     server out of many   |
       v                          |
  +----------------------------------+
  |  WEB SERVER                      |
  +----------------------------------+
       |                          ^
       | (4) not a static file -  | (7) built page
       |     this page must be    |
       |     built per request    |
       v                          |
  +----------------------------------+
  |  APP SERVER                      |
  |  (the code - business logic)     |
  +----------------------------------+
       |                          ^
       | (5) query                | (6) rows
       v                          |
  +----------------------------------+
  |  DATABASE                        |
  +----------------------------------+
```

## Round 2 — get the data

The HTML arrives and the page renders, but it's a shell. The JavaScript that
came with it now makes its own requests. **The scores arrive here, not above.**

```
  +----------------------------------+
  |  CLIENT                          |
  |  page rendered, JS now running   |
  +----------------------------------+
       |                    |
       |                    | (11) GET /logo.png, /styles.css, images
       |                    v
       |            +--------------------------+
       |            |  CDN EDGE                |  <- static assets, served
       |            |  (a copy near me)        |     from a datacenter near
       |            +--------------------------+     me. Never reaches ESPN's
       |                                             app server at all.
       | (10) GET /api/scores?league=nfl
       v
   ... same chain as Round 1: LOAD BALANCER -> APP SERVER -> DATABASE ...
       |
       | (12) 200 OK + JSON  { "games": [ ... ] }
       v
   JS writes the scores into the page. No reload.
```

This is the round that matters for dashboards: **the page loading and the data
arriving are two different trips, and they fail differently.**

---

## Frontend / backend

```
   CLIENT  |  CDN     ||   LOAD BALANCER   APP SERVER   DATABASE
           |          ||
    ---- FRONTEND ----||---------- BACKEND -----------------------
                      ||
    runs on MY machine||   runs on THEIR machines
    I can see it,     ||   I can't see it, can't change it,
    change it, break  ||   can't trust anything the frontend
    it, lie to it     ||   tells it without checking
```

The line sits at the network boundary: everything left of it executes on a
machine the user controls. That's why anything that *matters* — permissions,
prices, who sees what — has to be enforced right of the line.

(Where does the CDN belong? Arguably neither — it's their machine serving their
files, but it holds nothing private and runs no logic. Worth being able to
argue either way.)

---

## Annotations

Three things per box: what it does, what breaks without it, what it looks like
to a user when *this* box is the bottleneck.

### DNS
- **Does:** Translates a name into an address. `espn.com` -> `23.55.x.x`.
- **Without it:** You could still reach every site — by typing IP addresses. The
  real loss is the *indirection*: names are decoupled from machines, so ESPN can
  change hosting, add servers, or fail over to another datacenter without a
  single link on the internet breaking.
- **When it's the problem:** No page at all, and a **fast** failure — "server not
  found," `DNS_PROBE_FINISHED_NXDOMAIN`. Browser-level error, not a website
  error. Fast-error vs. spinner is the diagnostic: DNS fails instantly, an
  overloaded backend hangs first.

### Client / browser
- **Does:** More than send requests. It renders HTML/CSS, executes JavaScript,
  stores cookies and cache, and enforces the security rules that keep one site
  from reading another's data. It is a full runtime, not a viewer.
- **Without it:** Nothing to render into. (The real question is what a *degraded*
  client costs you, below.)
- **When it's the problem:** Page loads but behaves wrong — an extension blocking
  scripts, a stale cache serving yesterday's version, an old browser missing a
  feature. And the one that matters in BI: **a heavy dashboard rendering 50,000
  marks on an underpowered laptop.** Server responded in 200ms; the user waited
  eight seconds. "The dashboard is slow" sometimes means "your machine is slow,"
  and you cannot fix that in the backend.

### Load balancer
- **Does:** It *is* the address DNS handed back — the public front door. It holds
  the public IP and forwards each request to one machine in a private pool.
  Second job, equally important: **health checks.** It keeps asking each server
  "are you alive?" and stops sending traffic to ones that stop answering.
- **Without it:** One machine takes all traffic (overload), and — the bigger
  loss — **no redundancy.** One server dies and the site is down, with no way to
  deploy an update without downtime.
- **When it's the problem:** Slow, but characteristically **inconsistent**. Some
  requests fine, some fail; refresh and it works. That pattern — intermittent,
  not universal — usually means one bad server still in the pool. Also 502/503.

### Web server
- **Does:** Accepts the HTTP connection, hands back files that already exist
  (images, CSS, JS), and passes anything requiring computation to the app server.
- **Without it:** Nothing terminating the connection — no front door to knock on.
- **When it's the problem:** 502 (app server unreachable) or 504 (it waited too
  long). The visual tell: the page loads but arrives **unstyled** — raw text, no
  layout — because the HTML came through and the static files didn't.

### App server
- **Does:** Runs the actual code. Business logic, permissions, building the
  response. This is where "the software" lives.
- **Without it:** You'd get an HTML shell and no data filling it. ✅
- **When it's the problem:** 500 errors, or slowness — **and most real slowness
  lives here**, because it's the only box that runs your code. A missing loop
  optimization, an N+1 query, a third-party API called on every page load.

### Database
- **Does:** Holds the data — and more precisely, it's **the only box that
  remembers anything.** Every other box can be restarted or replaced from scratch;
  this one is the state.
- **Without it:** Nothing persists. The site could still serve pages, but no
  scores, no accounts, no history.
- **When it's the problem:** The page loads, one section spins forever, then
  times out. Slow queries, missing indexes, or — tomorrow's lesson — **too many
  people reading and writing the same tables at once.**

### CDN
- **Does:** Keeps copies of static files in datacenters around the world and
  serves each user from the nearest one. Two separate wins: **distance** (a round
  trip Seattle->Virginia costs ~70ms and no code can beat physics) and
  **offload** (ESPN's own servers never see those requests at all).
- **Without it:** Every image and stylesheet crosses the country and hits the
  origin servers. Slower for users, and far more load on the backend.
- **When it's the problem:** Page loads but unstyled or imageless. And the classic:
  **stale content** — you shipped a fix, but users keep seeing the old version
  because the edge is still serving its cached copy. "Have you tried a hard
  refresh?" exists because of this box.

---

## Three questions I will actually be asked

### 1. "Can we do row-level security so each regional manager only sees their region?"

**Backend. Always.** Two reasons, and the second is the one that changes how you
build it.

**Frontend filtering isn't security.** If the browser receives all regions and
hides the ones you shouldn't see, the data *is already on your machine* — sitting
in the network response, readable in devtools in about four seconds. Hiding is
not the same as not sending. This is precisely the difference between a Tableau
filter and row-level security, and it's worth saying out loud to a client who
thinks they're the same thing.

**The client cannot be trusted to say what it's allowed to see.** Sending
`region: WEST` in a request header doesn't work, because anyone can change a
header — curl, Postman, devtools, ten seconds. The rule:

> The client proves **who it is**. The server decides **what that means.**

So the request carries an identity token that the server issued and signed (and
therefore can't be forged); the backend looks up which regions that identity is
entitled to, and appends the filter itself. The user never states their own
permissions.

*Enforcement can live in the app server (it builds the WHERE clause) or in the
database itself (Postgres RLS, Power BI RLS). Both are real. What matters is
that it happens somewhere the user cannot reach.*

### 2. "The dashboard is slow."

First question back: **slow to load, or slow to filter?** Different rounds,
different boxes. (Then: everyone or one user? Always or at 9am?)

| Symptom | Likely box |
|---|---|
| Slow first visit only, fast after | DNS + TLS handshake (one-time, then cached) |
| Slow to load, everyone | App server building the page, or CDN missing/cold |
| Slow to load, one user | **Their machine** rendering a heavy dashboard |
| Page loads, charts spin | Round 2 — app server or database |
| Slow to filter | Depends entirely on live vs. extract — see below |
| Slow at 9am, fine at 2pm | Contention — load, not structure |
| Intermittent, refresh fixes it | Load balancer with a sick server in the pool |

**The live-vs-extract question is the one that matters and it's mine to know.**
On a live connection, every filter click is a brand-new query to the production
database — so slow filtering is a database problem (indexes, volume, locks). On
an extract, the data already sits in the BI tool's own engine — so slow filtering
is a data-volume or client-rendering problem and the database is innocent.
**Same symptom, opposite diagnosis.** Ask which one it is before anything else.

### 3. "We want the dashboard embedded in our customer portal."

Frontend piece: the portal's page holds an iframe or embed component that loads
the dashboard and renders it. Straightforward.

**Backend piece, and it's the one that surprises people:** the portal knows who
is logged in. The BI service does not. Something has to prove it — and it can't
be the browser, for exactly the reason in question 1. So:

```
  portal BACKEND  --(service credential + "this is user X")-->  BI service
  portal BACKEND  <--------(embed token, scoped to X)---------  BI service
  portal backend  ----------(token only)---------------------->  browser
```

Server-to-server, invisible to the user. If the browser could request its own
embed token, any user could request one for any other user — the same flaw as
question 1, wearing different clothes. Same shape as the OAuth flow from Day 10.

And this is where the two answers meet: **the identity in that embed token is
what drives the row-level filter.** Embedding and RLS are one problem.

---

## Status codes — "if accepted"

| Range | Means | Whose fault |
|-------|-------|-------------|
| 2xx | worked | — |
| 3xx | it moved, go here instead | — |
| 4xx | you asked wrong (404 gone, 401/403 not allowed) | the client's |
| 5xx | we broke (500 crashed, 503 overloaded, 504 too slow) | the server's |

4xx vs 5xx is the first triage question in any outage. It tells you which side
of the frontend/backend line to start looking on.
