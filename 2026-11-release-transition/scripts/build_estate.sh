#!/usr/bin/env bash
# Build the four services of an estate checkout (unit tests included) and copy the jars to <jars dir>.
# Usage: build_estate.sh <estate dir> <jars dir>  -> prints "unit ok" or "unit FAILED <service>..." ; exit 0 always
set -uo pipefail
E="$(cd "$1" && pwd)"; J="$(mkdir -p "$2" && cd "$2" && pwd)"; bad=""
for s in customer decision ledger notifier; do
  if ( cd "$E/$s" && mvn -o -q verify > "$J/$s.build.log" 2>&1 ) && [ -f "$E/$s/target/svc-$s-1.0.jar" ]; then cp "$E/$s/target/svc-$s-1.0.jar" "$J/$s.jar"; else bad="$bad $s"; fi
done
if [ -z "$bad" ]; then echo "unit ok"; else echo "unit FAILED$bad"; fi
