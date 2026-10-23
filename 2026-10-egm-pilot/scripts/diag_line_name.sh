#!/usr/bin/env bash
# Diagnostic, not a score: reruns the DISCOUNT hidden tests on a run's diff with one change to the test, so that a
# cart totals line named "order.total.discount" (shopizer's existing constant) counts as the "discount" line the task
# asks for. It shows how much of the feature works apart from that one naming miss.
#
# Usage: diag_line_name.sh <agent.diff> <out dir>     (writes <out dir>/diag-mvn.log and <out dir>/diag.json)
set -euo pipefail
E="$(cd "$(dirname "$0")/.." && pwd)"
W="${EGM_WORK:-$HOME/code/benchmark/skills-impact-work}"
DIFF="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"; OUT="$2"; mkdir -p "$OUT"; OUT="$(cd "$OUT" && pwd)"
export JAVA_HOME=/opt/homebrew/opt/openjdk@21 PATH="/opt/homebrew/opt/openjdk@21/bin:$PATH"
C="$OUT/clone"; rm -rf "$C"
git clone -q "$W/shopizer" "$C"; git -C "$C" checkout -q 6a4a0a6
( cd "$C" && TRIAL_QUESTION=DISCOUNT bash "$E/scripts/setup.sh" > /dev/null )
git -C "$C" apply --exclude='sm-shop/files/*' --exclude='sm-shop/src/test/java/com/salesmanager/test/shop/hidden/*' "$DIFF"
D="$C/sm-shop/src/test/java/com/salesmanager/test/shop/hidden"; mkdir -p "$D"
sed 's/if ("discount".equals(t.get("code"))) {/if ("discount".equals(t.get("code")) || "order.total.discount".equals(t.get("code"))) {/' \
  "$E/hidden/DISCOUNT/HiddenDiscountCodesTest.java" > "$D/HiddenDiscountCodesTest.java"
grep -q 'order.total.discount' "$D/HiddenDiscountCodesTest.java"
( cd "$C" && mvn -o -B -Dmaven.repo.local="$HOME/.m2/repository" -pl sm-shop -am -Dtest=HiddenDiscountCodesTest \
    -Dsurefire.failIfNoSpecifiedTests=false -Dmaven.test.failure.ignore=true test > "$OUT/diag-mvn.log" 2>&1 ) || true
python3 -I - "$C/sm-shop/target/surefire-reports" "$OUT/diag.json" <<'PY'
import glob, json, sys, xml.etree.ElementTree as ET
cases = {}
for f in glob.glob(sys.argv[1] + "/TEST-*HiddenDiscountCodesTest.xml"):
    for tc in ET.parse(f).getroot().iter("testcase"):
        cases[tc.get("name")] = "fail" if tc.find("failure") is not None or tc.find("error") is not None else "pass"
r = {"passed": sum(v == "pass" for v in cases.values()), "run": len(cases), "cases": cases}
json.dump(r, open(sys.argv[2], "w"), indent=1); print(r["passed"], "/", r["run"])
PY
rm -rf "$C"
