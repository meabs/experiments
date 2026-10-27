#!/usr/bin/env bash
# Builds the workspaces and guides for okf-local in $OKF_WORK (default ~/code/benchmark/okf-local), as OKF test G did:
# the storefront at 455b4bc, the Shopizer backend at 6a4a0a6 with OKF's renames (base, then --extra), and the guides
# from kgen (AgentGraphWorkTree aa98666, preset recommended). Needs git, python3, uv; SHOPIZER = a clone with 6a4a0a6.
set -euo pipefail
W="${OKF_WORK:-$HOME/code/benchmark/okf-local}"; SHOPIZER="${SHOPIZER:-$HOME/code/benchmark/skills-impact-work/shopizer}"
mkdir -p "$W" && cd "$W"
[ -d OKFExperiment ] || git clone -q https://github.com/meabs/OKFExperiment && git -C OKFExperiment checkout -q 5a09027
[ -d AgentGraphWorkTree ] || git clone -q https://github.com/meabs/AgentGraphWorkTree && git -C AgentGraphWorkTree checkout -q aa98666
[ -d fe-src ] || git clone -q https://github.com/shopizer-ecommerce/shopizer-shop-reactjs fe-src && git -C fe-src checkout -q 455b4bc
[ -d kvenv ] || { uv venv -q kvenv && uv pip install -q --python kvenv/bin/python tree-sitter tree-sitter-java tree-sitter-javascript tree-sitter-typescript tree-sitter-python; }
K="kvenv/bin/python AgentGraphWorkTree/.apm/skills/agent-graph/tool/kgen.py"
commit() { (cd "$1" && git init -q && git add -A && git -c user.name=okf-local -c user.email=okf-local@localhost commit -qm "$2"); }
rm -rf pr2 fe bundles kg && mkdir pr2 kg
git -C "$SHOPIZER" archive 6a4a0a6 | tar -x -C pr2
python3 OKFExperiment/scripts/privatize.py pr2 && python3 OKFExperiment/scripts/privatize.py pr2 --extra
commit pr2 "shopizer 6a4a0a6 with OKF's renames (base + extra)"
cp -r fe-src fe && rm -rf fe/.git && commit fe "storefront 455b4bc"
$K sync --repo pr2 && $K okf --repo pr2 --out bundles/backend --preset recommended --source-url '{path}'
$K sync --repo fe && $K okf --repo fe --out bundles/ref --preset recommended --reference backend=bundles/backend
mv pr2/.agent-knowledge kg/pr2 && mv fe/.agent-knowledge kg/fe     # no arm sees a code graph
python3 OKFExperiment/scripts/check_okf.py bundles/ref
