#!/usr/bin/env bash
# Hidden test for a harder cross-repo change task. Runs the storefront's own modules in plain Node with the network and browser globals stubbed.
set -uo pipefail
task="${1:?g1_delete_item, g2_add_voucher, g3_checkout_request or g4_orders_list}"
cd "$TRIAL_DIR" || exit 2
node --experimental-default-type=module --import "$OKF_EXP/harness/register.mjs" "$OKF_EXP/hidden/g/${task}.test.mjs" 2>&1 | grep -v ExperimentalWarning | tail -4
[ "${PIPESTATUS[0]}" -eq 0 ] || { echo "verify: hidden test failed" >&2; exit 1; }
