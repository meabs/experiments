#!/usr/bin/env bash
# Run the simulator: sim.sh <release|gate|ci> <S0..S5> --old DIR --new DIR --changed a,b [--plan FILE] --out FILE
E="$(cd "$(dirname "$0")/.." && pwd)"
exec java -cp "$E/sim/target/classes:$HOME/.m2/repository/com/h2database/h2/2.3.232/h2-2.3.232.jar" estate.sim.Cli "$@"
