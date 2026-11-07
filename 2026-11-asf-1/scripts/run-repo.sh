#!/usr/bin/env bash
# One fresh private repository per Machinist run (amendment-log item 3: no run can see another run's commits, PRs
# or checkout). Usage:
#   run-repo.sh create NAME   create meabs/NAME, push the base (one commit with 6a4a0a6's tree, as main), switch off Dependabot, add it to
#                             the Machinist App installation and register it as a Machinist project (own checkout)
#   run-repo.sh detach NAME   remove meabs/NAME from the App installation after grading (the repo stays, private)
# Order: create the next run's repo before detaching the last one (GitHub refuses to empty an installation, 422).
# NAME must be asf-run-NNN (or asf-shopizer for detach). Only the current run's repo is on the installation, so the
# token Machinist hands its agents reaches no other run.
set -euo pipefail
X="$(cd "$(dirname "$0")" && pwd)"
# The base is one commit, "shopizer" by trial <trial@example.com>, holding 6a4a0a6's tree: the same single-commit
# checkout ELC's setup.sh gives arm A, so no arm sees Shopizer's upstream history. Built once in base.git (commit
# 61a2a6f, tree 125f828).
BASEREPO="$HOME/code/benchmark/asf-runtime/base.git"
BASE=61a2a6fdcdf633eb00b33f64e68e0cddd29aa338
INSTALL=179554848
# GitHub accepts only a classic personal access token (repo scope) for adding or removing a repository on an App
# installation; the App's own user token and gh's OAuth token get 403. Kept in this file, never printed.
PAT_FILE="$HOME/.config/asf-install.pat"
inst() {  # inst METHOD REPO_ID -> HTTP status
  [ -s "$PAT_FILE" ] || { echo "missing $PAT_FILE" >&2; exit 1; }
  curl -s -o /dev/null -w '%{http_code}' -X "$1" "https://api.github.com/user/installations/$INSTALL/repositories/$2" \
    -H "Authorization: Bearer $(cat "$PAT_FILE")" -H 'Accept: application/vnd.github+json'
}
cmd=$1 name=$2
[[ "$name" =~ ^asf-run-[0-9]{3}$ || ( "$cmd" = detach && "$name" = asf-shopizer ) ]] || { echo "bad name: $name" >&2; exit 2; }
repo="meabs/$name"

case "$cmd" in
  create)
    gh repo view "$repo" >/dev/null 2>&1 || gh repo create "$repo" --private --description "ASF-1 run repository (to be deleted)" >/dev/null
    [ "$(git -C "$BASEREPO" rev-parse main)" = "$BASE" ] || { echo "base.git main is not $BASE" >&2; exit 1; }
    git -C "$BASEREPO" push -q "https://github.com/$repo.git" "+$BASE:refs/heads/main" 2>&1 | grep -v -i 'warning\|lfs' || true
    gh api -X DELETE "repos/$repo/automated-security-fixes" >/dev/null 2>&1 || true
    gh api -X DELETE "repos/$repo/vulnerability-alerts" >/dev/null
    rid="$(gh api "repos/$repo" -q .id)"
    [ "$(inst PUT "$rid")" = 204 ] \
      || { echo "could not add $repo to the App installation" >&2; exit 1; }
    out="$(bash "$X/mapi.sh" POST /api/v1/projects "{\"repository\":\"$repo\"}")"
    echo "$out" | grep -q "\"repository\":\"$repo\"" || { echo "Machinist project add failed: $out" >&2; exit 1; }
    echo "$repo ready (id $rid)"
    ;;
  detach)
    rid="$(gh api "repos/$repo" -q .id)"
    code="$(inst DELETE "$rid")"; [ "$code" = 204 ] || { echo "detach failed: HTTP $code" >&2; exit 1; }
    echo "$repo detached"
    ;;
  *) echo "unknown command: $cmd" >&2; exit 2 ;;
esac
