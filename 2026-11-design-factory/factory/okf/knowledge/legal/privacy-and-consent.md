---
type: Playbook
title: Privacy, consent and cookies (UK)
description: The UK GDPR and PECR points that change what a screen shows - privacy information at collection, consent that is a real choice, marketing permissions, cookies, data minimisation.
tags: [legal, privacy, uk]
status: draft
sources:
  - title: ICO guidance on UK GDPR (right to be informed, consent) and on PECR (cookies, electronic marketing)
    resource: https://ico.org.uk/for-organisations/
    checked: not fetched when this file was written; points below are well-established principles written from the author's knowledge. Check current ICO guidance, including changes made by the Data (Use and Access) Act 2025, before relying on any point
---

# Privacy, consent and cookies

Design guidance, not legal advice. Each point says what it changes on a screen. Raise anything unclear in the legal
register.

## When personal data is collected

- **Tell people at the point of collection** who is collecting it, what for, and where to find the full privacy
  notice. A short "just in time" line next to the field ("We use your mobile number to send security codes") plus a
  link is better than a link alone.
- **Ask for less.** Every field needs a purpose in this journey. Do not ask for date of birth, gender or address
  "for later".
- **Explain sensitive or surprising requests** (location, contacts, camera, identity documents) before the system
  prompt appears, and give a way to carry on without them where possible.
- **Do not show more than needed.** Mask account and card numbers except the part needed to recognise them.

## Consent

Consent is one of several lawful bases. Where the design asks for it (typically marketing and non-essential cookies):

- an active choice: unticked box or two equal buttons. Never pre-ticked, never implied by carrying on;
- separate from accepting terms, and separate for each purpose and channel (email, text, phone, post);
- says in plain words what the person is agreeing to and who will contact them;
- saying no is as easy and as visible as saying yes, and has no penalty in the journey;
- can be changed later as easily as it was given: say where ("You can change this in Settings").

Do not ask for consent for things that are simply necessary to provide the service (sending a payment, security
messages). Asking for consent you do not need is itself misleading.

## Marketing

Service messages (security codes, payment notices) are not marketing and need no opt-in. Promotional messages by
email or text generally need opt-in consent, with a narrow exception for existing customers and similar products
where an opt-out was offered at collection and in every message (check current rule with legal before using it).

## Cookies and similar storage

- Non-essential cookies and tracking (analytics, advertising, personalisation) need consent before they are set
  (check current rule: some low-risk purposes were given exemptions in 2025).
- The banner offers "Accept" and "Reject" with equal prominence on the first layer, plus settings. No "Accept"
  button next to a small "manage" link.
- The product works after rejecting.

## In the prototype

Use fictional data only. Simulate consent choices; do not add real tracking. Mark privacy wording as draft.
