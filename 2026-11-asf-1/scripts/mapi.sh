#!/usr/bin/env bash
# Calls the sandboxed Machinist API with the worker token. Usage: mapi.sh METHOD PATH [JSON]
T="$(cat "${HOME}/.machinist/server/worker.token")"
curl -s -X "$1" "http://127.0.0.1:7331$2" -H "Authorization: Bearer $T" -H 'Content-Type: application/json' ${3:+-d "$3"}
