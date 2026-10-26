## Part 3: administrator question APIs

Read `TASK.md` first, then this file. Own the protected admin HTTP surface: `GET /api/v1/private/questions`, `PUT /api/v1/private/questions/{id}/answer`, and `PUT /api/v1/private/questions/{id}/reject`. Match existing private-controller authorization and `?store=` merchant resolution. Validate status and answer lengths/trimming; map unknown ids to 404, invalid status/input to 400, rejected-answer attempts to 409, and successful mutations to the required 200 JSON question shape.

Files owned (create or edit only these, plus narrowly required package-local test files):
- `sm-shop/src/main/java/com/salesmanager/shop/store/api/v1/question/**` (new admin controller; use another clearly named package-local controller only if necessary)
- `sm-shop/src/main/java/com/salesmanager/shop/model/catalog/product/question/**` only for admin-specific request/response DTO additions not created by Part 2 (coordinate by inspecting existing files; avoid conflicting edits)

Use the Part 1 question service methods/status representation and existing `UserFacade`/private API authorization conventions. Admin responses use the full question shape including customer billing first name and timestamps. Do not edit customer/public controllers or core persistence files.
