---
name: self-review
description: Use before you finish: read your own diff as a reviewer would and fix what you find.
---

# Self-review

Read the full diff of your change (for example `git diff`, including new files) and check:

1. **Requirements:** does the diff do everything the ticket asks? Anything missing or only half done?
2. **Edge cases:** empty and null input, zero and negative numbers, duplicates, the first and last item, values at a
   limit, and the same action done twice.
3. **Errors:** does bad input get the error the ticket asks for, and nothing is saved when a request is rejected?
4. **Consistency:** do totals, counts and related records stay in step after every operation?
5. **Unintended changes:** leftover debugging, unrelated edits, changed behaviour elsewhere.
6. **Tests:** do your tests check the behaviour the ticket describes, and would they fail without your change?

Fix what you find, then build and run the tests again.
