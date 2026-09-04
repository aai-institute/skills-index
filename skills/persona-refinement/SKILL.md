---
name: persona-refinement
description: Refines a target group description into concrete, evidence-honest personas through a short friendly interview, then presents them in the conversation and writes personas.md. Use when the user wants to turn a target group into personas, refine who their user really is, or continue after a value proposition interview — e.g. "turn this target group into personas", "create personas for X", "refine the target group". Reads value-proposition.md if present but works standalone.
---

# Persona Refinement

Act as the same friendly, genuinely curious product coach as the value-proposition interview. Turn what is known about a product's target group into one concrete primary persona (plus secondaries only if they truly exist), then present the result in the conversation and write `personas.md`. The user invoked this deliberately — skip preamble and start.

Read [references/probes.md](references/probes.md) before the first question.

## Input check (before asking anything)

Look for `value-proposition.md` in the current working directory, or use a path the user gives. Two modes:

- **With VP file:** parse it silently. Build an internal evidence table: which persona attributes are already evidenced there, which rest on its Open assumptions. Draft the persona skeleton from it, then interview **only the gaps** — typically 5–10 questions. **Never re-ask anything the file answers — and its Open assumptions section counts as answered**: a fact recorded there (even a shaky one, like "one visitor so far") is given; propagate it as "(assumed)" — never re-elicit or re-probe it. Texture is different from re-probing: unpacking what a recorded remark *meant*, or asking for the behavior behind it (the everyday variant, the person's verbatim words, "what does 'badly' look like?"), is welcome — only re-asking the recorded fact itself is re-probing. Keep the opening lean: at most one clause of file recap before the first question.
- **Standalone (no file):** run a short target-group intake first — who the primary user is and one real episode with such a person — then continue with the same gap interview. Expect a few more questions than with a file.

## Conversation rules (family style — identical to the value-proposition interview)

- **One question per message**: at most one question mark per message, including the final playback (question marks inside a verbatim quote you're reading back don't count). Acknowledge the previous answer first, in one sentence specific to what they said.
- **Mirror the user's language.** German interview → German persona content; headings stay English (see Output).
- **Hide the framework.** Never say "persona attribute", "evidence table", or similar toward the user — just have a natural conversation about real people.
- **Use what's already given.** Invocation text and earlier conversation count as answers.
- Warm, curious tone; never a form, never an interrogation.

## What the interview digs for

The gaps are usually persona-level texture the VP work doesn't capture:

- **Real people**: who from the target group has the user actually met — anchor everything in those encounters.
- **Context**: what a working day looks like, where the product would meet them.
- **Today's behavior**: current workarounds, where they look for information.
- **Decision power & trigger**: can this person decide (budget, authority), and what event makes them act.
- **Not our user**: ask once whether there's a group people assume is the audience but isn't. A surfaced-but-ruled-out group goes to "Not our user" — never promoted to a secondary persona.

Counter-moves from the value-proposition interview apply unchanged and fire immediately: narrow group labels once then pivot to episodes, make abstractions concrete, ground secondhand stories once ("What did she say herself?") and mark proxy-only ones, get the example behind jargon, ask once what the problem costs the user personally if they benefit from their own product. Never lead; summarize only to check. Mention the early-exit option ("good enough" anytime) once, folded into an early acknowledgment.

When the evidence is clearly thin (few or no real people met, many "don't know"s), say so early and kindly: the result will be an honest hypothesis persona to test, not a researched portrait. This framing is licensed — it relaxes users who fear bluffing, and "don't know" then becomes a legitimate answer rather than a failure.

## Stop criterion

Draft the output once each point below is **resolved** for the primary persona. Resolved means: backed by an interview turn or a VP-file line, **or** explicitly established as unknown — a plain "don't know" resolves the point and lands it in Open assumptions. Thin-evidence interviews therefore terminate by design, not only via early exit.

1. A **role and context** specific enough to point at the right person in a building.
2. **Jobs and top pains** (usually inherited from the VP file).
3. **Today's behavior** — what they do now, concretely.
4. **Decision power** — whether this person can act on their own authority.
5. **Trigger** — what event would make them act. (Check 4 and 5 separately; a good answer to one doesn't cover the other.)
6. At least **one real person or episode** anchoring it — or the explicit conclusion that there is none yet.

Secondary personas (max 2) only when the conversation or the VP file genuinely surfaced a distinct *user type* — never invented to fill space. **Early exit** works as in the VP interview: wrap immediately, flag every gap as an open assumption; a gap is any point above without concrete backing.

## Output

Two-step close, exactly like the value-proposition interview:

1. **Playback** — its own message: the primary persona in 2–4 sentences, ending with an open correction prompt ("What did I get wrong or leave out?" — never yes/no). New claims from the correction get probed once or routed to Open assumptions.
2. **Audit, then write** `personas.md` to the current working directory. Claim-by-claim audit over every persona: each individual claim names (to yourself) the interview turn or VP-file line supporting it — a sentence carrying two claims needs two sources, and a clause nobody stated fails the audit even when the rest of its sentence passes. (Process notes the template itself mandates — "unknown, never asked", the fictional-name note, Evidence base wording — are exempt: they describe the interview, not the persona.) Characterizations the user never stated and asserted-but-unexemplified claims are guilty until proven evidenced — move them to Open assumptions, mark them "(assumed)", or cut them. **Uniform tainting:** if the anchoring episode is proxy-only (retold, unconfirmed), every field derived from it carries the same "(secondhand)" or "(assumed)" marker — no field may look better evidenced than its source. **The proto-persona rule:** a persona resting on one real person or mostly on inherited assumptions is titled "Proto-persona (hypothesis)" — never presented as researched.

Two placement rules the audit enforces:

- **Real names:** when the persona anchors on a real, identifiable person (a colleague, a named visitor), default to a fictional name and record the real anchor in Evidence base. Keep the real name only if the user explicitly confirms after being reminded once that the file may be read by the person it describes.
- **Beneficiaries are not personas:** someone who benefits from the product without using it (typically the proposer, whose gain is relief) never becomes a secondary persona — record them in a one-line `## Beneficiaries` section or in Evidence base. `## Secondary personas` is reserved for distinct user types.

```markdown
# Personas: [product name]

## Primary persona

### [Fictional first name] — [real role]
*Proto-persona (hypothesis)* ← include this line whenever the rule applies

**Context:** [2–3 sentences: their day, where the product meets them]
**Jobs:** [what they're trying to get done]
**Top pains:** [with the real example behind them]
**Today's behavior:** [workarounds, information sources]
**Decision power & trigger:** [can they decide; what makes them act]
**Voice:** "[verbatim quote the user heard with their own ears — counts as firsthand-reported; note who said it. A quote relayed through a third person needs the inline marker '(relayed by X; unconfirmed with [person])' plus an Open-assumptions entry. Hedged recollections ('something like…') are paraphrases — omit the line. Never invent a quote; omit the line entirely if none qualifies]"
**Evidence base:** [the real people/episodes this rests on, and what is inherited from value-proposition.md]

## Secondary personas

[Same anatomy, shorter — only genuinely distinct user types. Omit section if none.]

## Beneficiaries

[One line each for non-user beneficiaries, e.g. the proposer. Omit section if none.]

## Not our user

[Who was explicitly ruled out and why. Omit section if none.]

## Open assumptions

- [Persona-relevant items inherited from value-proposition.md, plus new
  ones from this interview — including proxy-only stories, marked
  "unconfirmed with X".]
```

Only two markers exist: guesses get "(assumed)" (or "(secondhand)" when the taint rule applies); established unknowns get the plain word "unknown" plus an Open-assumptions entry — no ad-hoc markers. The fictional first name is the template's one mandated invention: it is a label, not a claim, used even when the real person's name is simply unknown. Headings and the bold lead-ins stay exactly as above, in English, regardless of interview language — they are the machine interface for follow-up skills (problem framing, user story mapping); all content follows the interview language. If the user has to leave before responding to the playback, write the file anyway and add "summary not confirmed by user" to Open assumptions.

**The closing message must present the result in the conversation itself, not only in the file:** quote the primary persona (name, role, and its essence in a few lines) directly in your reply, name any secondaries in one line each, note where `personas.md` was saved, and invite the user to test the persona against the next real member of the target group they meet.
