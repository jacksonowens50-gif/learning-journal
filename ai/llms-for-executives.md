# How LLMs work, for executives

> Written for a finance or operations executive evaluating an AI proposal. No prior technical background assumed. Fifteen-minute read.

## What you're actually paying for

Language models don't read words, they read **tokens** — chunks of text roughly four characters long, or about three-quarters of a word. Common words are a single token; unusual ones split into several. Every model is priced per token, and the text you send in and the text it sends back are billed at different rates, with output costing meaningfully more than input.

Two consequences are worth knowing before you approve a budget.

**Financial documents are expensive relative to their page count.** Ordinary prose tokenizes efficiently — the model has seen those words a great many times. A figure like `1,247,893` does not; it fragments into several tokens, as do account codes, dates, and table formatting. A page of a budget file costs more to process than a page of a memo. Page count is the wrong unit for estimating this work.

**The cost is a usage curve, not a license.** This is the part most proposals leave vague. AI spend is not a seat count negotiated once a year. It is cost-per-call multiplied by volume, and the cost per call is driven by how much text moves through the model, not by how difficult the question is. A simple question asked against a large document costs more than a hard question asked against a small one.

Concretely: pasting a forty-page budget deck into a prompt is not a rounding error, it is a line item — and it recurs every time you ask a follow-up question about that deck.

## Why it forgets, and why the twentieth question costs more than the first

The **context window** is the maximum amount of text a model can consider at once. It holds everything: your instructions, any documents you've supplied, the conversation so far, and the model's own answer as it writes it.

Here is the counterintuitive part. **The model has no memory.** It does not recall your previous message. What actually happens is that the entire conversation is re-sent, from the beginning, on every single turn. The continuity you experience is the software re-reading the whole transcript aloud each time you speak.

Put plainly: you are not talking to an assistant who remembers you. You are re-briefing a consultant who has never met you, from scratch, before every question — and you pay for the re-briefing each time.

Two consequences follow, and both are business consequences rather than technical ones.

**Cost grows with conversation length, not with question difficulty.** The twentieth question in a thread costs more than the first, even when it's shorter, because everything above it is sent again.

**When the window fills, something has to be dropped.** Whatever the software chooses to drop is where "it forgot what I told it earlier" comes from. That choice is a design decision somebody made — it is not a property of the model.

A larger window is not automatically better, either. It costs more to fill, and material buried in the middle of a very long context tends to carry less weight than material at either end.

The practical version: a month-end close assistant that has been fed twelve tabs and forty turns of back-and-forth is both expensive and getting forgetful. Neither is the model being poor. Both are context management — and *"how do you manage context?"* is a fair question to put to any vendor, with a real answer behind it.

## What "training" means, and the question your counsel should actually ask

Two different things happen, and conflating them causes most of the confusion in these conversations.

**Training** happened once, before you ever touched the product. It consumed an enormous body of text and produced a fixed set of numbers — the model's weights. That process is finished. It is why every model has a **knowledge cutoff**: a date after which it simply has no information.

**Inference** is what happens when you use it. Text goes in, a prediction comes out, the weights are not touched. Nothing is learned. Nothing is retained by the model itself.

So when someone asks *"will it train on our data?"*, the mechanical answer is that an ordinary call does not modify the model — that is not what a call does. The contractual answer is a separate matter and depends entirely on the provider's terms. Anthropic's commercial terms state that inputs and outputs from commercial products are not used to train their models by default. Other providers differ, and the consumer tier of a product frequently differs from the commercial tier of the same product.

That question is usually the wrong one to spend the meeting on, and the most useful thing you can do is redirect it. **The real issue is not whether the model learns from your data. It is where your data goes and who keeps it.** Four questions with concrete contractual answers:

1. How long are prompts and outputs retained, and by whom?
2. In what region are they stored and processed?
3. Which subprocessors have access?
4. What actions by an employee change the answer?

That fourth one is the sleeper. With several providers, a user clicking thumbs-up or thumbs-down on a response submits that entire conversation to the vendor — an opt-in any employee can trigger without realising it, and one that is typically governed by an administrative setting somebody has to think to turn off.

**One last consequence of the cutoff.** The model does not know your company. It has never seen your chart of accounts, your contracts, or last quarter's results — and no amount of it being impressive changes that. That gap is what the rest of this document is about.

## Why it makes things up

Here is the mechanism, in four steps.

1. The model predicts the most plausible next chunk of text. Then it does it again, and again.
2. Plausible and true usually coincide, because most of the text it learned from was written by people being accurate.
3. When they come apart, nothing in the process prefers the true one. There is no step at which it checks.
4. It has no internal signal for *I have never seen this*. A well-founded answer and an invented one are produced by identical machinery and arrive in identical prose.

Stated at its strongest: **it is not looking anything up.** A spreadsheet lookup either finds the value or returns an error. This never returns an error. It returns the most plausible-looking text, every time, without exception.

What that looks like in practice:

> Ask it for the Q3 travel variance without giving it the file, and it will not tell you it doesn't have the file. It will give you a number — in the right units, with the right sign, phrased exactly like the twenty variance write-ups it learned from. It is not lying and it is not broken. You asked what words plausibly come next, and those were the words.

It's worth knowing why it doesn't simply say "I don't know." That sentence is rare in the material it learned from — variance write-ups almost never contain it. Refusal is low-probability text, so it loses to a confident figure, which is high-probability text. The model isn't being evasive. It's being ordinary.

The uncomfortable implication: **fluency is not evidence.** In every other professional setting, a well-structured, confident, correctly formatted answer is at least weak evidence that the person knows what they're talking about. That heuristic has served you your whole career, and it is precisely the heuristic this technology defeats. Saying that out loud to your teams is worth more than any policy document.

A workable rule that fits on a sticky note: **never ask it for a number — give it the numbers and ask it to work with them.**

## Does it learn from us?

Two different things get called "the model," and keeping them apart answers most of the governance questions.

**Training** happened once, before you ever touched it, at enormous cost. It produced a fixed set of internal weights. That is why every model has a knowledge cutoff — a date after which it simply knows nothing. It also never knew anything about your company.

**Inference** is what happens when you use it: text goes in, a prediction comes out, the weights are untouched. The model learns nothing from your question and retains nothing after answering it.

So when someone asks *"will it train on our data?"* — the mechanical answer is that an ordinary call does not modify the model, and the contractual answer, for the major vendors' commercial products, is no by default. Anthropic's terms state that inputs and outputs from commercial products such as the API and Claude for Work are not used to train their models unless you opt in.

Two caveats are worth carrying into the meeting.

**The opt-in is easier to trigger than people expect.** With Anthropic, submitting feedback via the thumbs up/down button shares that conversation, and feedback data can be retained for up to five years. It's a control an administrator can disable organisation-wide — but it is on by default, and it is one click by one employee.

**Consumer and commercial terms are not the same document.** The free or personal version your staff are already using in a browser is governed differently from the enterprise agreement your vendor is quoting. Most real exposure sits there, not in the system under procurement review.

And the redirect worth making: training is rarely the question that matters. The ones that do are *where is this data logged, for how long, in which region, which subprocessors touch it, and who at the vendor can read it.* Those are contractual, they differ by product and tier, and they are what your counsel should be asking about.

## What to do when the output is wrong

There are three levers. Almost every problem has a right one, and they differ by an order of magnitude in cost, time and staffing.

**Prompting** — change the instructions. What you ask for, how you structure it, what examples you provide.

**Retrieval (often called RAG)** — put the right documents in front of the model at the moment the question is asked, so the answer is grounded in your material rather than its general knowledge. It is the sticky-note rule above, built properly.

**Fine-tuning** — retrain part of the model on your own examples, altering its weights.

| | **Prompting** | **Retrieval / RAG** | **Fine-tuning** |
|---|---|---|---|
| What changes | The instructions | What's in front of it at question time | The model itself |
| Fixes | Format, tone, reasoning approach, consistency | "It doesn't know our data," staleness, sourcing | Consistent output shape at high volume |
| Does **not** fix | It not knowing your data | A task the model fundamentally can't do | Knowledge — this is the common misconception |
| Who does it | One capable person, in an afternoon | A data team — sourcing, structuring, access control, a pipeline | ML engineers, labelled examples, ongoing MLOps |
| Realistic lead time | Hours | Weeks to a few months | Months, and it must be maintained |
| Cost shape | Free | Build cost, plus an ongoing pipeline and per-query retrieval | Large upfront, and a rebuild each time the base model moves |

Three rules follow from that table.

**1. Try them in that order.** Nearly every request that arrives phrased as *"we need to train it on our data"* is solved by prompting or retrieval. Fine-tuning is where AI budgets go to disappear, and reaching for it first is the most expensive reflex in this field.

**2. Fine-tuning teaches a shape, not a fact.** If the goal is for the model to know your product catalogue, fine-tuning is the wrong tool — the catalogue changes on Tuesday and the weights do not. Retrieval is the tool, and it keeps working when the catalogue changes. Fine-tuning is for when you need the same *kind* of output, in the same format, a hundred thousand times.

**3. Retrieval is a data project, not an AI project.** This is the most useful line in this document for planning purposes. The quality of a retrieval system is determined entirely by whether the right document reaches the model — which is a question of where your documents live, how current they are, how they are structured, and who is permitted to see them. No model fixes scattered, undocumented, inconsistently governed data. That is a data problem wearing an AI hat, and it should be staffed and budgeted as one.

## Five questions before approving an AI project

None of these are technical. All of them are answerable by whoever is proposing the work, and an inability to answer one is itself the finding.

**1. What does this do when it's wrong, and who finds out?**
Wrong-with-a-human-reviewing and wrong-straight-into-a-report are different projects with different budgets. Every system described so far will be confidently wrong some of the time; the design question is where that lands and whether anyone notices.

**2. Where does the data it reads live today, and who is allowed to see it?**
If the answer involves five systems and a shared drive, you have a data project ahead of the AI project. And permissions must survive the move — an assistant that answers questions its user isn't cleared to ask is a compliance incident with a chat interface on the front.

**3. What is the cost per use, multiplied by realistic volume, per month?**
Not the licence. The usage curve. If nobody has done this arithmetic, the business case doesn't exist yet.

**4. What is it replacing, and what does that cost today?**
Hours, error rates, turnaround time — any of them. Without a baseline there is no way to tell success from enthusiasm.

**5. Who owns this in six months, when the model version changes?**
Models are deprecated and replaced on the vendor's timetable, not yours, and behaviour shifts when they are. Something that works today needs an owner and a retest budget. "Nobody" is the usual honest answer, and it is worth surfacing before signature rather than after.

---

*The single most useful posture: treat these systems as extremely fluent, extremely fast, and entirely unable to tell you when they don't know something. Every good design decision downstream follows from taking that seriously.*