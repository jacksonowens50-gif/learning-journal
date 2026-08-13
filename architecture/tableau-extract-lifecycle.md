# A real one — Tableau dashboard, extract via Bridge

My last employer's reporting stack, mapped onto the generic request lifecycle in
[request-lifecycle.md](request-lifecycle.md). Drawn from memory, Day 13.

**The thing the generic diagram doesn't show:** this system has **two separate
flows** that run at different times for different reasons. The user request never
touches the production database. That's the whole design, and it's the answer to
a question I get asked tomorrow.

---

## Flow A — the refresh (scheduled, no user involved)

```
  +--------------------------------------+
  |  PROD SQL SERVER                     |  the system running the business.
  |  inside the corporate network        |  Also the only copy of the truth.
  +--------------------------------------+
          ^                    |
          | (2) query          | (3) rows
          |                    v
  +--------------------------------------+
  |  TABLEAU BRIDGE                      |  (1) polls Cloud: "any jobs?"
  |  running on a Windows EC2 instance,  |
  |  RDP session left open 24/7          |  <-- the whole thing rests here
  +--------------------------------------+
                     |
                     | (4) pushes the extract UP — outbound only.
                     |     Bridge exists so Cloud never has to reach
                     |     *into* the network. No inbound firewall hole.
                     v
  +--------------------------------------+
  |  TABLEAU CLOUD                       |
  |  stores the extract (its own copy)   |
  +--------------------------------------+
```

## Flow B — someone opens the dashboard

```
  +--------------------------------------+
  |  BROWSER                             |  the frontend. Renders the viz,
  |  a manager's laptop                  |  and can be the bottleneck by itself.
  +--------------------------------------+
       |                          ^
       | (1) GET dashboard        | (6) HTML shell, then the viz data
       v                          |
  +--------------------------------------+
  |  LOAD BALANCER + WEB SERVER          |  exist, but Salesforce's problem.
  |  (Salesforce runs these, I never     |  Not a box I could ever intervene in.
  |   saw them)                          |
  +--------------------------------------+
       |                          ^
       | (2) render this viz      | (5) rendered marks
       v                          |
  +--------------------------------------+
  |  TABLEAU CLOUD  (app server)         |  VizQL, permissions, extract engine.
  +--------------------------------------+
       |                          ^
       | (3) query the extract    | (4) rows
       v                          |
  +--------------------------------------+
  |  THE EXTRACT                         |  <-- a copy, sitting in Cloud.
  |  (Tableau's own columnar store)      |      NOT the prod database.
  +--------------------------------------+


        PROD SQL SERVER does not appear in this flow at all.
        Every filter click a user makes is answered by the copy.
```

---

## Mapping to the generic boxes

| Generic box | What it actually was | Whose problem |
|---|---|---|
| Frontend | The browser on the user's laptop | Mine, sort of |
| CDN | Tableau's static assets | Salesforce's |
| Load balancer | Tableau Cloud's, unseen | Salesforce's |
| Web server | Tableau Cloud's, unseen | Salesforce's |
| App server | Tableau Cloud — VizQL, permissions, extract engine | Vendor's, config mine |
| Database (read) | **The extract** — a copy | Mine |
| Database (source) | **Prod SQL Server** — only touched in Flow A | IT's, and sacred |
| The undrawn box | **Tableau Bridge on an EC2 Windows instance** | Nobody's |

---

## Where it broke, and how I found out

**The seam:** two systems that needed to talk couldn't — Tableau Cloud is on the
public internet, prod SQL Server was behind a firewall — and a person bridged the
gap with a machine that was in nobody's architecture diagram.

Failure modes, roughly in order of how quietly they fail:

1. **The RDP session drops.** Bridge in application mode needs a live Windows
   session, which is *why* a remote desktop sat open 24/7. Windows Update
   reboots the instance and the refresh silently stops. Dashboards keep serving
   yesterday's numbers, looking completely normal.
2. **The credentials rotate.** Bridge ran under an account. Accounts expire and
   people leave.
3. **The instance is a snowflake.** Configured by hand, once, by someone. If it
   died, rebuilding it means remembering what was clicked. Nothing declarative,
   nothing version-controlled.
4. **The query itself fails** — a schema change upstream, a timeout on a table
   that grew.

**How I'd find out:** Tableau emails on a failed refresh. That's monitoring by
exception, and it's better than most places (most places find out because a
person says "these numbers look wrong").

**The hole in it:** a failure email only fires when a job *runs and fails*. If
Bridge is offline, there's no job to fail — so the loudest failure mode produces
the quietest signal. The alert catches breakage, not **absence**.

**What I'd build instead:** a heartbeat. Alert when a *success* hasn't arrived by
7am, rather than when a failure arrives. Same logic as a bank rec — you're not
checking that what you see is right, you're checking that what you expected
showed up at all.

And the email said *that* it failed, never *why*. Diagnosis was: RDP in, look
around. A runbook that lived in one person's head.

---

## The question this generalizes to

> "Where does your extract refresh actually run, and what happens when that
> machine reboots?"

Most people can answer the first half.
