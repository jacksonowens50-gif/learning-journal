# API Authentication — Cheat Sheet

*When to use which, what it costs in time, and what to ask the client's IT team.*

*v2 — Day 16. Added "How people log in" and row-level security; v1 covered machine-to-machine only.*

---

## Quick decision

| | **API key** | **Bearer token** | **OAuth 2.0** | **Service account** |
|---|---|---|---|---|
| **Acting as** | The application | Whoever holds it | A specific person, with their consent | The organization, not a person |
| **Travels in** | Query string (older APIs) or header | `Authorization` header | Header, after a token exchange | Header, after a token exchange |
| **Expires** | Rarely — often never | Yes, minutes to hours | Access token yes; refresh token long-lived | Yes, renewed automatically |
| **Typical use** | Public or read-only data services | Almost any modern API call | Apps acting on behalf of a signed-in user | Scheduled pipelines, server-to-server |
| **What breaks it** | Key leaked, or manually rotated | Token expired — must be refreshed | User leaves, revokes consent, or resets password | An admin changes its permissions |
| **Who sets it up** | Anyone with an account | Whoever issues the credential | User approves; IT registers the app first | IT / security team |
| **Realistic lead time** | Minutes | Minutes | **Days to weeks** — app registration + scope approval | **Days to weeks** — security review |

---

## The one-line versions

- **API key** — "Here's my password, every time."
- **Bearer token** — "Here's a badge that expires." Whoever bears it gets the access; the server doesn't check that it's you.
- **OAuth 2.0** — the process by which a user grants an app access *without ever handing over their password*. A limited power of attorney: specific permissions, revocable, verified by the provider rather than trusted to the app.
- **Service account** — a login that belongs to the company rather than to an employee. What a nightly pipeline should run as.

---

## How people log in

*Everything above is one machine proving itself to another. This section is humans — which is the half that decides whether a BI deployment can do per-user security at all.*

**Cookies.** A cookie is not authentication. It's the envelope authentication rides in: a small piece of data the server hands the browser, which the browser then sends back automatically on every subsequent request to that site. That automatic part is the whole value and the whole risk. Three attributes come up in client conversations and are worth knowing by name — `HttpOnly` means JavaScript on the page can't read the cookie, which blunts an entire category of attack where injected script steals the login; `Secure` means it's only ever sent over HTTPS; and `SameSite` controls whether some *other* site can trigger a request that carries it. When a security review asks "are your cookies hardened," these three are the answer.

**Sessions — the server remembers you.** You log in, the server writes down who you are in its own store, and hands your browser a meaningless ID in a cookie. The ID is a coat-check ticket: worthless by itself, because the list is behind the counter. Every subsequent request costs a lookup against that list. In exchange, revocation is instant — delete the row and the person is out on their very next click. The cost is that the server is now holding state, which is a real constraint when there are twenty servers behind a load balancer and the coat-check list has to be shared between them.

**JWT — you carry a signed badge.** Instead of a ticket pointing at a list, the server hands you a statement — *this is Jackson, in the finance group, expires at 4:15* — signed so that any of the company's systems can verify the server issued it and nobody edited it. There is no list. That's the appeal: any number of services can check the badge without a shared database and without calling home. And it's the drawback, because there's nothing to delete. Fire someone at 4:00 and, with sessions, they're locked out immediately; with JWTs, they keep working until the badge expires. That's why real JWT systems use short expiry plus a refresh token — the short window is the substitute for revocation. When someone says "we're stateless," this is what they mean, and "how fast can you actually cut someone off" is the fair follow-up.

**OAuth 2.0 — you let one app act for you on another.** The user grants an application scoped, revocable access to their data somewhere else *without handing over a password* — a limited power of attorney, verified by the provider rather than trusted to the app. The critical clarification, because it is misused constantly: **OAuth is an authorization protocol, not a login protocol.** It answers "may this app read that person's files," not "who is this person." The layer bolted on top that does answer the identity question is **OIDC** (OpenID Connect). "Sign in with Google" is OIDC riding on OAuth, and people call the whole thing OAuth.

**SSO / SAML / OIDC — log in once, and the company vouches for you everywhere.** The employee doesn't have a password for your tool at all. They authenticate once against the organization's identity provider — Entra ID, Okta, Ping — and each application trusts a signed assertion from that IdP saying who the user is and, usually, which groups they belong to. **SAML** is the older XML-based standard and is still ubiquitous in enterprise software; **OIDC** is the modern JSON-based equivalent built on OAuth 2.0. Functionally, for a client conversation, they do the same job and the choice is usually dictated by what the vendor supports. This is what a client means by "does it support our SSO," and the answer decides whether their users get accounts in your tool at all — plus whether IT will approve it, because SSO is how they turn off access for a departing employee in one place instead of eleven.

### What I built, and what it isn't

`mini-erp` requires an `x-api-key` header on every data endpoint; `/health` is deliberately left open so monitoring can reach it without holding a secret. That key identifies **the calling application**, not a person. There is no user, so there is nothing to filter by, so per-user row restrictions are impossible by construction rather than by omission. Worth stating plainly to a client, because "the API is secured" and "users only see their own data" sound like the same sentence and are not.

---

## "Can a user only see their own rows?"

*This is the question underneath most BI auth conversations. It gets asked as an SSO question and answered as a data modeling one.*

**How Power BI actually does it.** You define **roles** in Power BI Desktop (Modeling → Manage Roles). Each role carries a **DAX filter expression** evaluated against every row — rows returning TRUE survive, the rest are removed before the user ever sees them. You publish the semantic model, then assign members to those roles in the Power BI service.

- **Static RLS** hardcodes the value: `[Region] = "West"`. Simple, and you maintain one role per region forever.
- **Dynamic RLS** filters against the signed-in identity: `[UserEmail] = USERPRINCIPALNAME()`. One role, driven by an **entitlement table** mapping each person to what they're allowed to see. This is the pattern that scales — and it converts access control into a maintained dataset, which means somebody owns it, somebody updates it when people change jobs, and nobody does either unless it's named in the statement of work.
- **The identity has to arrive for any of it to work.** `USERPRINCIPALNAME()` returns something real only because the user signed in as themselves — which is the SSO conversation, arriving from the other direction. Service principals get no RLS applied at all, so an application connecting as itself sees everything and has to do its own filtering.

**Three things to check that most people don't:**

1. **RLS only filters Viewers.** Workspace **Admin**, **Member**, and **Contributor** roles bypass it entirely. "We have RLS enabled" plus "everyone's a Member so they can refresh datasets" equals no row security at all. This is common, and it's a permissions problem wearing a modeling problem's clothes — check it first, before touching any DAX.
2. **RLS filters rows, not columns.** Hiding a salary *column* is object-level security, a separate mechanism. A client asking "can we hide comp from regional managers" is asking a different question than they think they are.
3. **External/guest users are where dynamic RLS quietly breaks.** A B2B guest's UPN can arrive as `user_partner.com#EXT#@tenant.onmicrosoft.com` rather than `user@partner.com`, stop matching the entitlement table, and produce an empty report instead of an error — which nobody reports as a bug, they just stop opening the dashboard. Test with a real guest account; "Test as role" uses your identity, not theirs. Also: publish-to-web is incompatible with RLS outright.

**Tableau, same idea, different spelling.** An entitlement table joined to the data and filtered by `USERNAME()` or `ISMEMBEROF()`, or a data policy on a virtual connection to centralize the rule instead of rebuilding it per workbook.

**The sentence worth keeping:** row-level security is a data modeling problem wearing a security costume. It needs an entitlement table someone owns, a real identity flowing in through SSO, and nobody sitting in an elevated workspace role. Miss any one of the three and you have the *appearance* of access control — which is worse than none, because everyone stops checking.

---

## Reading the error

| Code | Means | Goes to |
|---|---|---|
| **401** | "I don't know who you are" — credential missing, expired, or invalid | Whoever issues and rotates credentials |
| **403** | "I know who you are, and no" — identity fine, permissions insufficient | Whoever administers access and approves scopes |

Sending a 403 to the credentials team produces three days of "we regenerated it, try again." Nothing was ever wrong with the credential.

**The one I got wrong from the other side:** when *building* an API, there's a third case that isn't either of these — the server itself has no credential configured. That's a **500**, not a 401. Returning 401 sends the caller hunting for a credential problem that doesn't exist on their end. Whoever owns the deployment needs to hear about it, not whoever owns the key.

---

## What to ask a client's IT team

1. Which authentication methods does the system support — key, token, OAuth, or SAML/SSO only?
2. Can we get a **service account** rather than tying the pipeline to an employee's login?
3. What scopes or permissions exist, and what's the **minimum** needed for read-only access?
4. Who owns credential rotation, and how often does it happen? Will the pipeline be told before it does?
5. Is there a **non-production environment** we can build against?
6. What's the rate limit, and is it counted per key or per organization?
7. If OAuth: who approves scope requests internally, and what's the typical turnaround?
8. What's the process to get a credential reissued at 2am if the nightly job fails?
9. Which identity provider holds your logins, and is every reporting user in it — including contractors, plant staff, and anyone at a partner company?
10. If we need row-level restrictions: **does a table already exist that says which person can see which rows?** If not, who decides, and who maintains it after we leave?

---

## Red flags — the estimate goes up

- **"Just use my login."** The pipeline breaks the day that person changes their password, changes roles, or leaves.
- **A token with no expiry.** Convenient now, an open door forever, and usually a sign nobody owns the security review.
- **No sandbox environment.** Every test is a production test.
- **Credentials arriving by email or chat.** They're now permanently in a mailbox and a backup of that mailbox.
- **No documentation, "but I can send you a Postman collection."** Means the API's behavior is undocumented tribal knowledge, and the person who has it is one resignation away.
- **"We'll just give everyone Contributor so they can refresh it."** Every row-level rule in the model is now decorative.
- **The entitlement mapping lives in a spreadsheet someone updates by hand.** It will be wrong within a quarter, and the failure is silent — people see too much, or see nothing, and neither generates a ticket.

---

## The line for a CFO

The two-week estimate for OAuth or a service account is usually real, and it isn't engineering time — it's **approval** time. Someone has to register the application, decide which permissions it gets, and sign off that a system rather than a person will hold access to company data. What's worth pushing back on is a two-week estimate for an **API key**, which is a ten-minute task.

And when the question is "can each manager see only their region," the honest answer is that the dashboard work is the easy part. The schedule risk is the list of who's allowed to see what — whether it exists, whether it's accurate, and who owns it once we're gone.
