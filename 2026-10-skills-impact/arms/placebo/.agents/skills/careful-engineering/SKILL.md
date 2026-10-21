---
name: careful-engineering
description: Use when working on any task in a codebase - general habits for reading, changing and explaining code
---

# Careful engineering

These are general working habits. They apply to any language and any kind of task.

## Before you start

Read the request twice. Note which words in it name things that exist in the code, and which describe behaviour. Names are good search terms; behaviour descriptions usually are not.

Get a rough map of the area before reading closely. Look at the folder layout, the module or package names, and the main entry points. A minute spent on the map saves reading files that turn out not to matter.

When the code base has its own conventions, follow them even when you would choose differently in a new project. Consistency inside one code base is worth more than local improvements to style.

## Reading code

Read the code that is actually used, not the code that looks relevant. Follow references from the entry point rather than guessing from file names. When two classes have similar names, check which one the call site imports.

Keep a short list of what you have learned as you go: which class owns which decision, where data is converted from one shape to another, and where configuration is read. Most changes touch one of these three places.

Be wary of comments. They describe what the code did when the comment was written. When a comment and the code disagree, the code is what runs.

## Making changes

Prefer the smallest change that fully does what was asked. Do not rename, reformat or reorganise code you are not otherwise changing; it makes the change harder to review.

Put new code where a reader would look for it: next to similar code, in the layer that already owns that kind of decision. Avoid adding a new layer or helper when an existing one fits.

Name things after what they mean in the domain, not after how they are implemented. A good name makes a comment unnecessary.

Handle the inputs the code will really receive. Think about empty values, missing values and values at the edges of a range, and decide what should happen for each.

Keep related changes together and unrelated changes out. If you notice a separate problem, mention it rather than fixing it in the same change.

## Explaining your work

When you finish, describe what you changed and why in a few sentences. Name the files you changed. If you made an assumption about something the request did not say, state the assumption plainly so a reviewer can check it.

Write for a reader who knows the code base but has not seen the request. Avoid jargon that only makes sense inside your own reasoning.

If something did not go as planned, say so. A clear account of a problem is more useful than a confident summary that hides it.

## General

Stay calm and methodical. Work in small steps. When you are unsure, look at the code again rather than guessing.
