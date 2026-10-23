"""Runs a HumanEval answer against its tests (README, "Grading"). The code runs in bubblewrap: read-only system, no
network, no home folder, an empty /tmp, a 20 s limit. Pass means `check(<entry point>)` returned without error.
"""
import os, subprocess, tempfile

BWRAP = ["bwrap", "--ro-bind", "/usr", "/usr", "--symlink", "usr/lib", "/lib", "--symlink", "usr/lib64", "/lib64",
         "--symlink", "usr/bin", "/bin", "--proc", "/proc", "--dev", "/dev", "--tmpfs", "/tmp", "--unshare-all",
         "--die-with-parent", "--new-session", "--clearenv", "--setenv", "PATH", "/usr/bin"]


def run_tests(code, test, entry, timeout=20):
    """Returns (passed, detail)."""
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "t.py")
        open(p, "w").write(f"{code}\n\n{test}\n\ncheck({entry})\n")
        try:
            r = subprocess.run(BWRAP + ["--ro-bind", d, "/w", "python3", "-I", "/w/t.py"], capture_output=True, text=True,
                               timeout=timeout, stdin=subprocess.DEVNULL)
        except subprocess.TimeoutExpired:
            return False, "timeout"
        return r.returncode == 0, (r.stderr or "")[-500:]
