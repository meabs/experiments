"""Regression tests for the grading and analysis code. Run: python3 -m pytest -q tests (from the experiment folder)."""
import json, os, subprocess, sys, textwrap

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
S = os.path.join(HERE, "..", "scripts")
sys.path.insert(0, S)
import audit, mutation, process, stats  # noqa: E402


# ---------- summarize.py: the pass/fail decision ----------

def report(d, module, suite, tests=1, failures=0, errors=0, skipped=0):
    p = os.path.join(d, module, "target/surefire-reports")
    os.makedirs(p, exist_ok=True)
    with open(os.path.join(p, f"TEST-{suite}.xml"), "w") as f:
        f.write(f'<testsuite name="{suite}" tests="{tests}" failures="{failures}" errors="{errors}" skipped="{skipped}"/>')


def summarize(d, rc, expected=None):
    out = os.path.join(d, "out")
    os.makedirs(out, exist_ok=True)
    args = [sys.executable, "-I", os.path.join(S, "summarize.py"), out, str(rc)] + ([str(expected)] if expected else [])
    p = subprocess.run(args, cwd=d, capture_output=True, text=True)
    return p.returncode, json.load(open(os.path.join(out, "verify-summary.json")))


H = "com.salesmanager.test.shop.hidden.HiddenX"


def test_all_green_passes(tmp_path):
    report(tmp_path, "sm-shop", H, tests=5)
    report(tmp_path, "sm-core", "com.x.ExistingTest", tests=3)
    rc, s = summarize(tmp_path, 0, 5)
    assert rc == 0 and s["pass"]


def test_missing_hidden_tests_fail(tmp_path):
    report(tmp_path, "sm-core", "com.x.ExistingTest", tests=3)
    rc, s = summarize(tmp_path, 0, 5)
    assert rc == 1 and not s["pass"] and s["hidden_tests"] == 0


def test_compilation_failure_fails(tmp_path):
    # A compile error stops Maven before any report is written, and Maven exits non-zero.
    rc, s = summarize(tmp_path, 1, 5)
    assert not s["pass"]


def test_compile_failure_after_hidden_ran_still_fails(tmp_path):
    report(tmp_path, "sm-shop", H, tests=5)
    rc, s = summarize(tmp_path, 1, 5)
    assert not s["pass"]


def test_unrelated_failure_fails(tmp_path):
    report(tmp_path, "sm-shop", H, tests=5)
    report(tmp_path, "sm-shop", "com.x.CategoryIT", tests=4, failures=1)
    rc, s = summarize(tmp_path, 0, 5)
    assert not s["pass"] and s["other_failures"] == 1 and s["hidden_pass"]


def test_hidden_failure_fails(tmp_path):
    report(tmp_path, "sm-shop", H, tests=5, errors=1)
    rc, s = summarize(tmp_path, 0, 5)
    assert not s["pass"] and not s["hidden_pass"]


def test_skipped_hidden_test_fails(tmp_path):
    report(tmp_path, "sm-shop", H, tests=5, skipped=2)
    rc, s = summarize(tmp_path, 0, 5)
    assert not s["pass"]


def test_fewer_hidden_tests_than_expected_fails(tmp_path):
    report(tmp_path, "sm-shop", H, tests=3)
    rc, s = summarize(tmp_path, 0, 5)
    assert not s["pass"]


def test_unreadable_report_fails(tmp_path):
    report(tmp_path, "sm-shop", H, tests=5)
    p = os.path.join(tmp_path, "sm-shop/target/surefire-reports/TEST-broken.xml")
    open(p, "w").write("<testsuite")
    rc, s = summarize(tmp_path, 0, 5)
    assert not s["pass"] and s["unreadable_reports"]


# ---------- audit.py: the independent log regrade ----------

LOG_OK = textwrap.dedent("""\
    [INFO] Tests run: 3, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 1 s - in com.x.ExistingTest
    [INFO] Tests run: 5, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 9 s - in com.salesmanager.test.shop.hidden.HiddenX
    [INFO] BUILD SUCCESS
    """)


def test_regrade_pass():
    assert audit.regrade_log(LOG_OK, 5)["pass"]


def test_regrade_ansi_and_unrelated_failure():
    log = LOG_OK.replace("Tests run: 3, Failures: 0", "\x1b[1;31mTests run: 3, Failures: 1")
    r = audit.regrade_log(log, 5)
    assert not r["pass"] and r["bad_suites"] == ["com.x.ExistingTest"]


def test_regrade_short_hidden_suite():
    assert not audit.regrade_log(LOG_OK, 7)["pass"]


def test_regrade_compilation_error():
    assert not audit.regrade_log("[ERROR] COMPILATION ERROR\n[INFO] BUILD FAILURE", 5)["pass"]


# ---------- mutation.classify: per-defect detection ----------

def st(compiled=True, **cases):
    return {"compiled": compiled, "cases": cases}


def test_detects_both_defects_independently():
    v, _ = mutation.classify({"both": st(a="fail", b="fail"), "price": st(a="fail", b="pass"),
                              "mapper": st(a="pass", b="error"), "fixed": st(a="pass", b="pass")})
    assert v == "both"


def test_detects_one_defect():
    v, _ = mutation.classify({"both": st(a="fail"), "price": st(a="fail"), "mapper": st(a="pass"), "fixed": st(a="pass")})
    assert v == "price-only"


def test_passes_despite_defects():
    v, _ = mutation.classify({s: st(a="pass") for s in mutation.STATES})
    assert v == "none"


def test_needs_both_defects_to_fail():
    v, _ = mutation.classify({"both": st(a="fail"), "price": st(a="pass"), "mapper": st(a="pass"), "fixed": st(a="pass")})
    assert v == "combined-only"


def test_compile_error_is_not_detection():
    v, _ = mutation.classify({"both": st(compiled=False), "price": st(compiled=False),
                              "mapper": st(compiled=False), "fixed": st(a="pass")})
    assert v == "not-executable"


def test_compile_error_in_one_state_is_not_executable():
    v, _ = mutation.classify({"both": st(a="fail"), "price": st(compiled=False), "mapper": st(a="fail"), "fixed": st(a="pass")})
    assert v == "not-executable"


def test_failure_that_also_fails_on_fixed_code_is_not_detection():
    # Ambiguous outcome: case a fails everywhere (unrelated), case b never fails.
    v, d = mutation.classify({"both": st(a="fail", b="pass"), "price": st(a="fail", b="pass"),
                              "mapper": st(a="error", b="pass"), "fixed": st(a="fail", b="pass")})
    assert v == "none" and d["red_on_fixed"] == ["a"]


def test_all_cases_red_on_fixed():
    v, _ = mutation.classify({s: st(a="fail") for s in mutation.STATES})
    assert v == "fails-on-fixed"


def test_no_cases_ran():
    v, _ = mutation.classify({s: st() for s in mutation.STATES})
    assert v == "not-executable"


def test_skipped_case_is_not_valid():
    v, _ = mutation.classify({"both": st(a="fail"), "price": st(a="fail"), "mapper": st(a="fail"), "fixed": st(a="skipped")})
    assert v == "fails-on-fixed"


# ---------- process.py: test outcomes and TDD evidence ----------

def test_outcome_red_with_ansi_and_dtest_attribution():
    out = "\x1b[1;31mERROR\x1b[m] There are test failures.\n"
    assert process.test_outcome(1, out, "mvn -pl sm-core -Dtest=FooTest test") == ("red", ["FooTest"])


def test_outcome_red_from_surefire_line():
    out = "[ERROR] Tests run: 3, Failures: 1, Errors: 0, Skipped: 0, Time elapsed: 0.1 s <<< FAILURE! - in com.x.FooTest"
    assert process.test_outcome(1, out) == ("red", ["FooTest"])


def test_outcome_compile_error_is_not_red():
    assert process.test_outcome(1, "[ERROR] COMPILATION ERROR :\n cannot find symbol")[0] == "compile-error"


def test_outcome_unknown_without_evidence():
    assert process.test_outcome(1, "something went wrong") == ("unknown", [])


def test_is_test_run():
    assert process.is_test_run("/bin/zsh -lc 'mvn -pl sm-shop -Dtest=X test'")
    assert process.is_test_run("./mvnw verify")
    assert not process.is_test_run("mvn -DskipTests install")
    assert not process.is_test_run("mvn compile")


def test_shell_edit_detection():
    assert process.shell_edits("cat > sm-core/src/test/java/FooTest.java <<'EOF'")[0] == ["sm-core/src/test/java/FooTest.java"]
    assert process.shell_edits("sed -i '' 's/a/b/' sm-core/src/main/java/Foo.java")[0] == ["sm-core/src/main/java/Foo.java"]
    assert process.shell_edits("sed -n '1,80p' sm-core/src/main/java/Foo.java")[0] == []
    assert process.shell_edits("python3 -c \"open('sm-core/src/main/java/Foo.java','w')\"")[1]


E_T = {"k": "edit", "path": "m/src/test/java/FooTest.java", "via": "tool"}
E_M = {"k": "edit", "path": "m/src/main/java/Foo.java", "via": "tool"}
RED = {"k": "test", "outcome": "red", "failing": ["FooTest"]}
GREEN = {"k": "test", "outcome": "green", "failing": []}


def test_tdd_confirmed():
    assert process.classify_tdd([E_T, RED, E_M, GREEN], {"FooTest"})[0] == "tdd-confirmed"


def test_edit_order_alone_is_not_tdd():
    assert process.classify_tdd([E_T, E_M, GREEN], {"FooTest"}) == ("test-file-first", "no test run before the fix")


def test_compile_error_red_is_not_tdd():
    ce = {"k": "test", "outcome": "compile-error", "failing": []}
    assert process.classify_tdd([E_T, ce, E_M, GREEN], {"FooTest"}) == ("test-file-first", "compile error only")


def test_red_in_other_class_is_not_tdd():
    other = {"k": "test", "outcome": "red", "failing": ["BarTest"]}
    assert process.classify_tdd([E_T, other, E_M, GREEN], {"FooTest"})[1] == "only other classes failed"


def test_no_green_after_fix():
    assert process.classify_tdd([E_T, RED, E_M], {"FooTest"})[1] == "no passing test run after the fix"


def test_impl_first():
    assert process.classify_tdd([E_M, E_T, RED, GREEN], {"FooTest"})[0] == "impl-first"


def test_subagent_makes_it_unknown():
    assert process.classify_tdd([E_T, RED, {"k": "subagent"}, E_M, GREEN], {"FooTest"})[0] == "unknown"


def test_unattributed_red_is_unknown():
    red = {"k": "test", "outcome": "red", "failing": []}
    assert process.classify_tdd([E_T, red, E_M, GREEN], {"FooTest"})[0] == "unknown"


def test_shell_edit_counts_in_order():
    sh_main = {"k": "edit", "path": "m/src/main/java/Foo.java", "via": "shell"}
    assert process.classify_tdd([sh_main, E_T, RED, GREEN], {"FooTest"})[0] == "impl-first"
    assert process.test_file_first([sh_main, E_T, E_M]) is True  # the preregistered measure ignores shell edits


# ---------- stats.py ----------

def test_fisher_matches_known_values():
    assert stats.fisher_greater(24, 24, 22, 24) == pytest.approx(0.2447, abs=1e-4)
    assert stats.fisher_greater(12, 12, 8, 12) == pytest.approx(0.0466, abs=1e-4)
    assert stats.fisher_two_sided(3, 3, 0, 3) == pytest.approx(0.1, abs=1e-9)


def test_holm():
    assert stats.holm([0.01, 0.04, 0.03]) == pytest.approx([0.03, 0.06, 0.06])


def test_wilson_and_newcombe():
    lo, hi = stats.wilson(0, 10)
    assert lo == 0 and hi == pytest.approx(0.2775, abs=1e-3)
    d, lo, hi = stats.newcombe(24, 24, 22, 24)
    assert d == pytest.approx(2 / 24) and lo < 0 < hi


def test_preregistered_fisher_unchanged():
    # analyse.py has its own copy of the test; both must agree.
    src = open(os.path.join(S, "analyse.py")).read()
    ns = {}
    exec(src[src.index("def fisher_greater"):src.index("def sel")], {"math": __import__("math")}, ns)
    for args in [(24, 24, 22, 24), (19, 24, 22, 24), (31, 36, 0, 36), (5, 6, 8, 12)]:
        assert ns["fisher_greater"](*args) == pytest.approx(stats.fisher_greater(*args))
