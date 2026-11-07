#!/usr/bin/env bash
# GitHub API call with Machinist's GitHub App user token (read from its private credentials file, never printed).
# Used only to add and remove the per-run repositories on the App installation. Usage: appapi.sh METHOD PATH
T="$(python3 -I -c "import json,os;print(json.load(open(os.path.expanduser('~/.machinist/server/onboarding/github/credentials.json')))['access_token'])")"
curl -s -X "$1" "https://api.github.com$2" -H "Authorization: Bearer $T" -H 'Accept: application/vnd.github+json' -w '\nHTTP %{http_code}\n'
