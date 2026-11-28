package estate.sim;

import java.nio.file.*;
import java.util.*;

/**
 * java -cp classes:h2.jar estate.sim.Cli <release|gate|ci> <S0..S5> --old DIR --new DIR --changed a,b [--plan FILE] --out FILE
 * DIR holds one <service>.jar per service. A plan file has lines `stage svc[,svc] [drain]`; without one the changed
 * services deploy one at a time in alphabetical order.
 */
public class Cli {
    public static void main(String[] a) throws Exception {
        String mode = a[0], scen = a[1];
        Map<String, String> o = new HashMap<>();
        for (int i = 2; i + 1 < a.length; i += 2) o.put(a[i], a[i + 1]);
        Path oldDir = Paths.get(o.getOrDefault("--old", o.get("--new"))), newDir = Paths.get(o.get("--new"));
        Set<String> changed = new TreeSet<>();
        for (String s : o.getOrDefault("--changed", "").split(",")) if (!s.isEmpty()) changed.add(s);
        List<Run.Stage> stages = new ArrayList<>();
        if (o.containsKey("--plan") && Files.exists(Paths.get(o.get("--plan")))) {
            for (String line : Files.readAllLines(Paths.get(o.get("--plan")))) {
                String[] p = line.trim().split("\\s+");
                if (p.length < 2 || !p[0].equals("stage")) continue;
                Run.Stage st = new Run.Stage();
                for (String s : p[1].split(",")) if (changed.contains(s)) st.services.add(s);
                st.drain = p.length > 2 && p[2].equals("drain");
                if (!st.services.isEmpty()) stages.add(st);
            }
        } else {
            for (String s : changed) { Run.Stage st = new Run.Stage(); st.services.add(s); stages.add(st); }
        }
        String out = o.get("--out");
        String id = mode + "_" + scen + "_" + System.nanoTime();
        if (mode.equals("ci")) {
            Engine e = new Engine(id, newDir, newDir);
            Run r = new Run(e, scen, true, null, stages, changed);
            for (int i = 0; i < 4; i++) {} // no loss, no faults: the estate smoke test
            r.execute(true);
            Files.writeString(Paths.get(out), r.toJson("ci"));
        } else if (mode.equals("gate")) {
            List<String[]> all = new ArrayList<>();
            StringBuilder sb = new StringBuilder("{\"mode\":\"gate\",\"runs\":[");
            int n = 0; boolean reject = false;
            for (String f : changed) {
                Engine e = new Engine(id + "_" + f, oldDir, newDir);
                e.lossEvery = 3;
                Run r = new Run(e, scen, true, f, stages, changed);
                r.execute(false);
                if (n++ > 0) sb.append(',');
                sb.append(r.toJson("gate"));
                if (!r.violations.isEmpty()) reject = true;
            }
            sb.append("],\"verdict\":").append(Json.q(reject ? "reject" : "admit")).append("}\n");
            Files.writeString(Paths.get(out), sb.toString());
        } else {
            Engine e = new Engine(id, oldDir, newDir);
            if (scen.equals("S3")) e.lossEvery = 3;
            Run r = new Run(e, scen, false, Run.FAULT.get(scen), stages, changed);
            r.execute(false);
            Files.writeString(Paths.get(out), r.toJson("release"));
        }
    }
}
