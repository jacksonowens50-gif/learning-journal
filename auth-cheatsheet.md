# API Authentication — Cheat Sheet

*When to use which, what it costs in time, and what to ask the client's IT team.*

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

## Reading the error

| Code | Means | Goes to |
|---|---|---|
| **401** | "I don't know who you are" — credential missing, expired, or invalid | Whoever issues and rotates credentials |
| **403** | "I know who you are, and no" — identity fine, permissions insufficient | Whoever administers access and approves scopes |

Sending a 403 to the credentials team produces three days of "we regenerated it, try again." Nothing was ever wrong with the credential.

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

---

## Red flags — the estimate goes up

- **"Just use my login."** The pipeline breaks the day that person changes their password, changes roles, or leaves.
- **A token with no expiry.** Convenient now, an open door forever, and usually a sign nobody owns the security review.
- **No sandbox environment.** Every test is a production test.
- **Credentials arriving by email or chat.** They're now permanently in a mailbox and a backup of that mailbox.
- **No documentation, "but I can send you a Postman collection."** Means the API's behavior is undocumented tribal knowledge, and the person who has it is one resignation away.

---

## The line for a CFO

The two-week estimate for OAuth or a service account is usually real, and it isn't engineering time — it's **approval** time. Someone has to register the application, decide which permissions it gets, and sign off that a system rather than a person will hold access to company data. What's worth pushing back on is a two-week estimate for an **API key**, which is a ten-minute task.
