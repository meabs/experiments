package estate.sim;

import estate.api.Context;
import estate.api.Service;
import estate.api.ServiceException;

import java.net.URL;
import java.net.URLClassLoader;
import java.nio.file.Path;
import java.sql.Connection;
import java.sql.DriverManager;
import java.util.*;

/** The platform: versioned service instances, shared per-service databases, sync calls, delayed events, injected faults. */
public class Engine {
    public static final String[] SERVICES = {"customer", "decision", "ledger", "notifier"};
    public static final int INSTANCES = 2;
    static final int DELAY = 3;
    static final Map<String, String> SUBS = Map.of("payment.posted", "customer", "offer.queued", "notifier");

    public static class Inst implements Context {
        final Engine e; public final String svc; public final int idx; public final String label;
        Service impl; Connection conn; public boolean up; public String err = "";
        Inst(Engine e, String svc, int idx, String label) { this.e = e; this.svc = svc; this.idx = idx; this.label = label; }
        public Connection db() { return conn; }
        public Map<String, String> call(String s, String op, Map<String, String> r) throws ServiceException { return e.call(svc, s, op, r); }
        public void publish(String topic, Map<String, String> ev) { e.publish(topic, ev); }
        public long now() { return e.tick; }
    }

    static class Ev { long at, seq; String topic; Map<String, String> body; }

    final String runId; final Path oldDir, newDir;
    final Map<String, Inst[]> insts = new LinkedHashMap<>();
    final Map<String, Integer> rr = new HashMap<>();
    public long tick = 0;
    long seq = 0;
    final List<Ev> queue = new ArrayList<>();
    public final List<String> eventLog = new ArrayList<>();
    public final List<Map<String, String>> published = new ArrayList<>();
    public int deadLetters = 0;
    public final List<String> deadDetail = new ArrayList<>();
    public int lossEvery = 0, postCalls = 0;
    public boolean loseNextPost = false;
    public long customerRuleTick = -1;
    public final List<String> timeline = new ArrayList<>();
    public int violationsSoFar = 0, failedSoFar = 0;

    public Engine(String runId, Path oldDir, Path newDir) {
        this.runId = runId; this.oldDir = oldDir; this.newDir = newDir;
        for (String s : SERVICES) insts.put(s, new Inst[INSTANCES]);
    }

    Path jar(String label, String svc) { return (label.equals("old") ? oldDir : newDir).resolve(svc + ".jar"); }

    public String dbUrl(String svc) { return "jdbc:h2:mem:" + runId + "_" + svc + ";DB_CLOSE_DELAY=-1"; }

    public Connection openDb(String svc) throws Exception { return DriverManager.getConnection(dbUrl(svc)); }

    public boolean start(String svc, int idx, String label) {
        Inst i = new Inst(this, svc, idx, label);
        try {
            i.conn = openDb(svc);
            URLClassLoader cl = new URLClassLoader(new URL[]{jar(label, svc).toUri().toURL()}, Engine.class.getClassLoader());
            i.impl = (Service) cl.loadClass("estate.svc.Main").getDeclaredConstructor().newInstance();
            i.impl.start(i);
            i.impl.handle("health", new HashMap<>());
            i.up = true;
        } catch (Throwable t) {
            Throwable c = t; while (c.getCause() != null) c = c.getCause();
            i.up = false; i.err = c.toString();
        }
        Inst old = insts.get(svc)[idx];
        if (old != null && old.conn != null) try { old.conn.close(); } catch (Exception ignored) {}
        insts.get(svc)[idx] = i;
        updateRule();
        log("instance", svc + "#" + idx + " " + label + (i.up ? " up" : " DOWN: " + i.err));
        return i.up;
    }

    void updateRule() {
        boolean all = true;
        for (Inst i : insts.get("customer")) if (i == null || !i.up || !i.label.equals("new")) all = false;
        if (all) { if (customerRuleTick < 0) customerRuleTick = tick; } else customerRuleTick = -1;
    }

    public String versions() {
        StringBuilder sb = new StringBuilder("{");
        int n = 0;
        for (String s : SERVICES) {
            if (n++ > 0) sb.append(',');
            sb.append('"').append(s).append("\":[");
            Inst[] a = insts.get(s);
            for (int k = 0; k < a.length; k++) {
                if (k > 0) sb.append(',');
                sb.append('"').append(a[k] == null ? "none" : a[k].label + (a[k].up ? "" : "!")).append('"');
            }
            sb.append(']');
        }
        return sb.append('}').toString();
    }

    public void log(String kind, String detail) {
        timeline.add("{\"t\":" + tick + ",\"kind\":" + Json.q(kind) + ",\"detail\":" + Json.q(detail) + ",\"versions\":" + versions()
                + ",\"violations\":" + violationsSoFar + ",\"failed\":" + failedSoFar + "}");
    }

    Inst pick(String svc, boolean advanceCounter) {
        Inst[] a = insts.get(svc);
        int start = rr.getOrDefault(svc, 0);
        for (int k = 0; k < a.length; k++) {
            Inst i = a[(start + k) % a.length];
            if (i != null && i.up) { if (advanceCounter) rr.put(svc, (start + k + 1) % a.length); return i; }
        }
        return null;
    }

    public Map<String, String> call(String from, String svc, String op, Map<String, String> req) throws ServiceException {
        boolean lose = false;
        if (svc.equals("ledger") && op.equals("post")) {
            postCalls++;
            if (loseNextPost) { lose = true; loseNextPost = false; }
            else if (lossEvery > 0 && postCalls % lossEvery == 0) lose = true;
        }
        Inst i = pick(svc, true);
        if (i == null) throw new ServiceException("unavailable", svc + " has no healthy instance");
        return invoke(i, op, req, lose);
    }

    /** Call a specific instance (used by recovery probes). */
    public Map<String, String> callInstance(Inst i, String op, Map<String, String> req) throws ServiceException {
        return invoke(i, op, req, false);
    }

    private Map<String, String> invoke(Inst i, String op, Map<String, String> req, boolean lose) throws ServiceException {
        Map<String, String> r;
        try {
            r = i.impl.handle(op, new HashMap<>(req));
        } catch (ServiceException x) {
            throw x;
        } catch (Throwable t) {
            throw new ServiceException("error", t.toString());
        }
        if (lose) throw new ServiceException("timeout", "response lost");
        return r == null ? new HashMap<>() : new HashMap<>(r);
    }

    void publish(String topic, Map<String, String> body) {
        Ev ev = new Ev(); ev.at = tick + DELAY; ev.seq = seq++; ev.topic = topic; ev.body = new HashMap<>(body);
        queue.add(ev);
        Map<String, String> rec = new HashMap<>(body); rec.put("_topic", topic); rec.put("_tick", String.valueOf(tick));
        published.add(rec);
    }

    /** Inject an event as if a producer had published it (used by acceptance checks). */
    public void inject(String topic, Map<String, String> body) { publish(topic, body); }

    public void advance() {
        tick++;
        deliverDue();
    }

    void deliverDue() {
        List<Ev> due = new ArrayList<>();
        for (Ev ev : queue) if (ev.at <= tick) due.add(ev);
        due.sort(Comparator.comparingLong((Ev x) -> x.at).thenComparingLong(x -> x.seq));
        for (Ev ev : due) {
            String target = SUBS.get(ev.topic);
            Inst i = target == null ? null : pick(target, true);
            if (target == null) { queue.remove(ev); continue; }
            if (i == null) continue; // keep it queued until an instance is up
            queue.remove(ev);
            try {
                i.impl.onEvent(ev.topic, new HashMap<>(ev.body));
            } catch (Throwable t) {
                deadLetters++;
                Throwable c = t; while (c.getCause() != null) c = c.getCause();
                deadDetail.add(ev.topic + " on " + i.svc + "#" + i.idx + " " + i.label + ": " + c);
            }
        }
    }

    public void drain() {
        for (int k = 0; k < 40 && !queue.isEmpty(); k++) advance();
    }
}
