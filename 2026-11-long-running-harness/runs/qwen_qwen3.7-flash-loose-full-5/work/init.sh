#!/bin/sh
# Basic end-to-end check, run at the start of every session.
if [ -d tests ]; then python3 -m unittest discover -s tests 2>&1 | tail -5; fi
d=$(mktemp -d); cp tasks.py "$d"/ 2>/dev/null || { echo "tasks.py missing"; exit 1; }
(cd "$d" && python3 tasks.py add smoke && python3 tasks.py list) && echo "smoke: ok" || echo "smoke: BROKEN"
