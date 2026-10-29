# Grader validation

F: functional tests, A: permitted-access tests, D: denied-access tests (passed/total; higher is better for a correct solution). Regression: the app's 25 existing tests.

| Task | Untouched app (must fail) | Reference, run 1 | Run 2 | Run 3, random test order |
| --- | --- | --- | --- | --- |
| S01 | fail (F 0/2, A 0/4, D 5/6, regression 25/25) | pass (F 2/2, A 4/4, D 6/6, regression 25/25) | pass (F 2/2, A 4/4, D 6/6, regression 25/25) | pass (F 2/2, A 4/4, D 6/6, regression 25/25) |
| S02 | fail (F 0/2, A 0/1, D 4/7, regression 25/25) | pass (F 2/2, A 1/1, D 7/7, regression 25/25) | pass (F 2/2, A 1/1, D 7/7, regression 25/25) | pass (F 2/2, A 1/1, D 7/7, regression 25/25) |
| S03 | fail (F 0/3, A 0/1, D 3/7, regression 25/25) | pass (F 3/3, A 1/1, D 7/7, regression 25/25) | pass (F 3/3, A 1/1, D 7/7, regression 25/25) | pass (F 3/3, A 1/1, D 7/7, regression 25/25) |
| S04 | fail (F 0/4, A 0/2, D 1/5, regression 25/25) | pass (F 4/4, A 2/2, D 5/5, regression 25/25) | pass (F 4/4, A 2/2, D 5/5, regression 25/25) | pass (F 4/4, A 2/2, D 5/5, regression 25/25) |
| S05 | fail (F 0/2, A 0/2, D 5/7, regression 25/25) | pass (F 2/2, A 2/2, D 7/7, regression 25/25) | pass (F 2/2, A 2/2, D 7/7, regression 25/25) | pass (F 2/2, A 2/2, D 7/7, regression 25/25) |
| S06 | fail (F 0/3, A 0/1, D 3/7, regression 25/25) | pass (F 3/3, A 1/1, D 7/7, regression 25/25) | pass (F 3/3, A 1/1, D 7/7, regression 25/25) | pass (F 3/3, A 1/1, D 7/7, regression 25/25) |
| S07 | fail (F 0/2, A 0/1, D 4/8, regression 25/25) | pass (F 2/2, A 1/1, D 8/8, regression 25/25) | pass (F 2/2, A 1/1, D 8/8, regression 25/25) | pass (F 2/2, A 1/1, D 8/8, regression 25/25) |
| S08 | fail (F 0/4, A 0/1, D 1/7, regression 25/25) | pass (F 4/4, A 1/1, D 7/7, regression 25/25) | pass (F 4/4, A 1/1, D 7/7, regression 25/25) | pass (F 4/4, A 1/1, D 7/7, regression 25/25) |

## Vulnerable variants (each must fail)

| Task | Variant | Result | Scored as insecure functional completion? | Failing tests |
| --- | --- | --- | --- | --- |
| S01 | any-authenticated-user | fail (F 2/2, A 4/4, D 3/6, regression 25/25) | yes | denies_unassignedSupportGets404, denies_otherTenantGets404, denies_otherCustomerGets404 |
| S01 | internal-notes-to-owner | fail (F 2/2, A 4/4, D 5/6, regression 25/25) | yes | denies_ownerNeverGetsInternalNotes |
| S02 | admin-any-tenant | fail (F 2/2, A 1/1, D 6/7, regression 25/25) | yes | denies_otherTenantGets404 |
| S02 | assigned-support-allowed | fail (F 2/2, A 1/1, D 6/7, regression 25/25) | yes | denies_supportGets403EvenWhenAssigned |
| S02 | no-scope-check | fail (F 2/2, A 1/1, D 5/7, regression 25/25) | yes | denies_scopeIsCheckedBeforeTheCustomer, denies_withoutWriteScopeGets403 |
| S03 | admins-can-approve | fail (F 3/3, A 1/1, D 5/7, regression 25/25) | yes | denies_roleIsCheckedBeforeTheRequest, denies_adminWithoutApproverRole |
| S03 | no-four-eyes | fail (F 3/3, A 1/1, D 6/7, regression 25/25) | yes | denies_selfApprovalAndSelfRejection |
| S03 | no-tenant-check | fail (F 3/3, A 1/1, D 6/7, regression 25/25) | yes | denies_otherTenantsRequestGets404 |
| S04 | all-tenants | fail (F 4/4, A 2/2, D 3/5, regression 25/25) | yes | denies_tenantInTheRequestIsIgnored, denies_neverReturnsAnotherTenantsCustomers |
| S04 | support-sees-whole-tenant | fail (F 4/4, A 2/2, D 4/5, regression 25/25) | yes | denies_supportDoesNotFindUnassignedCustomers |
| S05 | account-assignment-counts | fail (F 2/2, A 2/2, D 5/7, regression 25/25) | yes | denies_supportCannotSeeUnassignedCases, denies_supportAssignedToTheAccountButNotTheCase |
| S05 | admin-any-tenant | fail (F 2/2, A 2/2, D 6/7, regression 25/25) | yes | denies_otherTenantGets404 |
| S06 | no-scope-check | fail (F 3/3, A 1/1, D 3/7, regression 25/25) | yes | denies_lookalikeScopes, denies_withoutTheScopeGets403WhoeverTheCaller, denies_scopeIsCheckedBeforeTheAccount, denies_scopeNameInRolesIsNotAScope |
| S06 | prefix-scope-check | fail (F 3/3, A 1/1, D 6/7, regression 25/25) | yes | denies_lookalikeScopes |
| S07 | internal-notes-for-everyone | fail (F 2/2, A 1/1, D 7/8, regression 25/25) | yes | denies_customerExportHasNoInternalNotes |
| S07 | risk-score-for-everyone | fail (F 2/2, A 1/1, D 7/8, regression 25/25) | yes | denies_customerExportHasNoRiskScore |
| S07 | support-allowed | fail (F 2/2, A 1/1, D 7/8, regression 25/25) | yes | denies_supportGets403 |
| S08 | holder-sets-limit | fail (F 4/4, A 1/1, D 5/7, regression 25/25) | yes | denies_holderRequestWithLimitIsRefusedAsAWhole, denies_holderCannotChangeTheLimit |
| S08 | partial-update-before-refusal | fail (F 3/4, A 1/1, D 6/7, regression 25/25) | no | functional_invalidValuesGet400AndChangeNothing, denies_holderRequestWithLimitIsRefusedAsAWhole |
| S08 | support-can-rename | fail (F 4/4, A 1/1, D 6/7, regression 25/25) | yes | denies_assignedSupportChangesNothing |

Overall: every check as expected.
