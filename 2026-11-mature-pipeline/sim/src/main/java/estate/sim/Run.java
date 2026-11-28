package estate.sim;

import estate.api.ServiceException;

import java.math.BigDecimal;
import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.Statement;
import java.util.*;

/**
 * One release trajectory on the simulated estate: boot the old versions, seed, run traffic, roll the plan out (with the
 * scenario's fault and a rollback), then check invariants and acceptance. `generic` switches to the gate's rehearsal
 * traffic and rules (the same for every scenario); otherwise the oracle's scenario traffic and invariants are used.
 */
public class Run {
    public static class Stage { public List<String> services = new ArrayList<>(); public boolean drain; }
    static class Pay { String acct; BigDecimal amt; String status; }

    static final int[][] CASES = {{1000, 100}, {1000, 300}, {1000, 500}, {1000, 550}, {1000, 800}, {2000, 200}, {2000, 1000}, {500, 50}};
    static final Map<String, String> FAULT = Map.of("S0", "decision", "S1", "ledger", "S2", "ledger", "S3", "ledger", "S4", "notifier", "S5", "decision");

    final Engine e; final String scen; final boolean generic; final String fault; final List<Stage> stages; final Set<String> changed;
    public final List<String[]> violations = new ArrayList<>();
    final Set<String> seen = new HashSet<>();
    public boolean aborted; public String abortReason = "";
    public Boolean recovered = null;
    public int failed = 0, payFailed = 0, j = 0, probeN = 0;
    final List<Pay> pays = new ArrayList<>();
    public Map<String, Boolean> delivered = new LinkedHashMap<>();
    boolean faultDone = false;

    public Run(Engine e, String scen, boolean generic, String fault, List<Stage> stages, Set<String> changed) {
        this.e = e; this.scen = scen; this.generic = generic; this.fault = fault; this.stages = stages; this.changed = changed;
    }

    static Map<String, String> m(String... kv) {
        Map<String, String> r = new HashMap<>();
        for (int i = 0; i < kv.length; i += 2) r.put(kv[i], kv[i + 1]);
        return r;
    }

    void viol(String inv, String key, String detail, String at) {
        if (!seen.add(inv + ":" + key)) return;
        violations.add(new String[]{inv, key + " " + detail, at});
        e.violationsSoFar++;
        e.log("violation", inv + " " + key + " " + detail);
    }

    Map<String, String> cl(String svc, String op, Map<String, String> req) {
        try { return e.call(null, svc, op, req); }
        catch (ServiceException x) { failed++; e.failedSoFar++; return null; }
    }

    static String refDecision(int income, int amount) {
        long score = Math.max(0, Math.min(100, 100 - (amount * 100L) / income));
        return score >= 60 ? "APPROVE" : score >= 40 ? "REFER" : "DECLINE";
    }

    // ------------------------------------------------------------------ traffic

    String mix(int n) {
        if (generic) return new String[]{"pay", "apply", "offer"}[n % 3];
        switch (scen) {
            case "S4": return "offer";
            case "S5": case "S0": return "apply";
            default: return "pay";
        }
    }

    void journey(int n) {
        switch (mix(n)) {
            case "pay": {
                Pay p = new Pay();
                p.acct = "acct-" + n;
                p.amt = new BigDecimal((10 + n % 7) + "." + (n % 4 == 0 ? "00" : n % 4 == 1 ? "25" : n % 4 == 2 ? "50" : "75"));
                Map<String, String> r = cl("customer", "pay", m("customerId", "c" + (n % 9), "account", p.acct, "amount", p.amt.toPlainString(), "ref", "ref-" + n));
                p.status = r == null ? "ERROR" : r.getOrDefault("status", "ERROR");
                if (!p.status.equals("OK")) payFailed++;
                pays.add(p);
                break;
            }
            case "apply": {
                int[] c = CASES[n % 8];
                Map<String, String> r = cl("customer", "apply", m("customerId", "c" + (n % 9), "income", "" + c[0], "amount", "" + c[1]));
                if (r != null && !refDecision(c[0], c[1]).equals(r.get("decision")))
                    viol(generic ? "P3-wrong-decision" : "wrong-decision", "j" + n, "got " + r.get("decision") + " want " + refDecision(c[0], c[1]), "journey");
                break;
            }
            default: {
                int cust = generic ? (n / 3) % 9 : n % 9;
                cl("customer", "offer", m("customerId", "c" + cust, "offerId", "o" + n));
            }
        }
    }

    void traffic(int k) {
        for (int i = 0; i < k; i++) { journey(j++); e.advance(); }
    }

    // ------------------------------------------------------------------ checks

    void payChecks(String at, boolean withStatement) {
        for (Pay p : pays) {
            Set<BigDecimal> t = new HashSet<>();
            t.add(p.amt.setScale(2));
            if (!p.status.equals("OK")) t.add(new BigDecimal("0.00"));
            BigDecimal first = null;
            for (int k = 0; k < Engine.INSTANCES; k++) {
                Map<String, String> r = cl("ledger", "balance", m("account", p.acct));
                if (r == null) continue;
                BigDecimal b = new BigDecimal(r.get("balance")).setScale(2);
                if (first == null) first = b;
                if (!t.contains(b)) viol(generic ? "P6-ledger-balance-wrong" : "ledger-balance-wrong", p.acct, "balance " + b + " want " + t, at);
            }
            Map<String, String> pc = cl("ledger", "postings", m("account", p.acct));
            if (pc != null && Integer.parseInt(pc.get("count")) > 1) viol(generic ? "P2-duplicate-posting" : "duplicate-posting", p.acct, "postings " + pc.get("count"), at);
            if (withStatement && first != null) {
                for (int k = 0; k < Engine.INSTANCES; k++) {
                    Map<String, String> s = cl("customer", "statement", m("account", p.acct));
                    if (s != null && new BigDecimal(s.get("balance")).setScale(2).compareTo(first) != 0)
                        viol(generic ? "P1-statement-diverges" : "statement-diverges", p.acct, "statement " + s.get("balance") + " ledger " + first, at);
                }
            }
        }
    }

    boolean probe(String svc) {
        boolean ok = true;
        for (Engine.Inst i : e.insts.get(svc)) {
            if (i == null || !i.up) { ok = false; continue; }
            try {
                switch (svc) {
                    case "ledger":
                        e.callInstance(i, "post", m("account", "probe", "amount", "1.00", "requestId", "probe-" + (probeN++)));
                        if (!pays.isEmpty()) {
                            Pay p = pays.get(0);
                            Map<String, String> r = e.callInstance(i, "balance", m("account", p.acct));
                            Set<BigDecimal> t = new HashSet<>(List.of(p.amt.setScale(2), new BigDecimal("0.00")));
                            if (!t.contains(new BigDecimal(r.get("balance")).setScale(2))) ok = false;
                        }
                        break;
                    case "customer": e.callInstance(i, "statement", m("account", "acct-0")); break;
                    case "decision": e.callInstance(i, "score", m("income", "1000", "amount", "100")); break;
                    default: e.callInstance(i, "sent", m("customerId", "c0"));
                }
            } catch (Exception x) { ok = false; }
        }
        return ok;
    }

    // ------------------------------------------------------------------ rollout

    boolean up(String svc, int idx) {
        if (!e.start(svc, idx, "new")) { aborted = true; abortReason = svc + "#" + idx + " new version failed to start: " + e.insts.get(svc)[idx].err; return false; }
        return true;
    }

    void rollback(List<String> svcs) {
        e.log("rollback", "health check failed after upgrading " + svcs + "; rolling back");
        for (String s : svcs) for (int i = 0; i < Engine.INSTANCES; i++) if (e.insts.get(s)[i].label.equals("new")) e.start(s, i, "old");
        boolean ok = true;
        for (String s : svcs) ok &= probe(s);
        recovered = (recovered == null ? true : recovered) && ok;
        e.log("recovery", ok ? "rolled back, probes pass" : "ROLLBACK FAILED: old version cannot serve the persisted data");
        payChecks("after-rollback", false);
    }

    boolean rollout(Stage st) {
        if (st.drain) { e.drain(); e.log("drain", "queues drained before " + st.services); }
        boolean faultHere = fault != null && st.services.contains(fault) && !faultDone;
        e.log("stage", "deploying " + st.services);
        if (st.services.size() > 1) {
            for (String s : st.services) for (int i = 0; i < Engine.INSTANCES; i++) if (!up(s, i)) return false;
            if (faultHere) {
                faultDone = true;
                rollback(st.services);
                traffic(8);
                for (String s : st.services) for (int i = 0; i < Engine.INSTANCES; i++) if (!up(s, i)) return false;
            }
            traffic(8);
            return true;
        }
        String s = st.services.get(0);
        for (int i = 0; i < Engine.INSTANCES; i++) {
            if (!up(s, i)) return false;
            traffic(8);
            if (faultHere && i == 0 && !faultDone) {
                faultDone = true;
                rollback(List.of(s));
                traffic(8);
                i = -1;
            }
        }
        return true;
    }

    public void execute(boolean allNew) {
        for (String s : Engine.SERVICES) for (int i = 0; i < Engine.INSTANCES; i++) e.start(s, i, allNew ? "new" : "old");
        for (int i = 0; i < 9; i++) cl("customer", "create", m("customerId", "c" + i, "consent", i % 3 != 2 ? "implied" : "explicit"));
        e.log("boot", allNew ? "all new" : "all old");
        traffic(10);
        if (!allNew) {
            for (Stage st : stages) { if (!rollout(st)) break; }
        }
        traffic(8);
        e.drain();
        e.log("settled", "release finished" + (aborted ? " (aborted)" : ""));
        try { finalChecks(); } catch (Exception x) { viol("oracle-error", "final", x.toString(), "final"); }
        if (aborted) viol(generic ? "P8-deploy-aborted" : "deploy-aborted", "release", abortReason, "stage");
        if (recovered != null && !recovered) viol(generic ? "P5-rollback-unrecoverable" : "rollback-unrecoverable", "release", "old version could not serve after rollback", "after-rollback");
        if (!generic && !aborted) { try { acceptance(); } catch (Exception x) { delivered.put("error", false); } }
    }

    void finalChecks() throws Exception {
        payChecks("final", true);
        if (e.deadLetters > 0) viol(generic ? "P7-dead-letter" : "dead-letter", "events", e.deadLetters + " events failed: " + String.join("; ", e.deadDetail.subList(0, Math.min(3, e.deadDetail.size()))), "final");
        if (generic) {
            if (e.customerRuleTick >= 0) {
                for (int i = 0; i < 9; i++) {
                    Map<String, String> c = cl("customer", "consent.check", m("customerId", "c" + i, "purpose", "marketing"));
                    Map<String, String> s = cl("notifier", "sent", m("customerId", "c" + i));
                    if (c == null || s == null || c.get("allowed").equals("true")) continue;
                    int late = 0;
                    for (String t : s.get("ticks").split(",")) if (!t.isEmpty() && Long.parseLong(t) > e.customerRuleTick) late++;
                    if (late > 0) viol("P4-effect-after-rollout", "c" + i, late + " sends after the customer rule changed", "final");
                }
            }
        } else if (scen.equals("S4") && e.customerRuleTick >= 0) {
            for (int i = 0; i < 9; i++) {
                if (i % 3 == 2) continue;
                Map<String, String> s = cl("notifier", "sent", m("customerId", "c" + i));
                if (s == null) continue;
                int late = 0;
                for (String t : s.get("ticks").split(",")) if (!t.isEmpty() && Long.parseLong(t) > e.customerRuleTick) late++;
                if (late > 0) viol("sent-without-consent", "c" + i, late + " offers sent after explicit consent became required", "final");
            }
        }
    }

    // ------------------------------------------------------------------ acceptance (the new requirements work in the final estate)

    long count(String svc, String sql) throws Exception {
        try (Connection c = e.openDb(svc); Statement s = c.createStatement(); ResultSet rs = s.executeQuery(sql)) { rs.next(); return rs.getLong(1); }
    }

    void acceptance() throws Exception {
        Map<String, String> r;
        switch (scen) {
            case "S1": {
                int before = e.published.size();
                cl("customer", "pay", m("customerId", "c1", "account", "acc-l", "amount", "12.34", "ref", "acc-ref"));
                e.drain();
                boolean ok = false;
                for (int k = before; k < e.published.size(); k++) {
                    Map<String, String> ev = e.published.get(k);
                    if ("payment.posted".equals(ev.get("_topic")) && "acc-l".equals(ev.get("account"))) ok = "1234".equals(ev.get("amountMinor"));
                }
                delivered.put("ledger", ok);
                e.inject("payment.posted", m("account", "acc-c", "amountMinor", "1234", "requestId", "acc-x"));
                e.drain();
                r = cl("customer", "statement", m("account", "acc-c"));
                delivered.put("customer", r != null && "12.34".equals(r.get("balance")));
                break;
            }
            case "S2": {
                cl("customer", "pay", m("customerId", "c1", "account", "acc-b", "amount", "7.25", "ref", "acc-ref"));
                e.drain();
                r = cl("ledger", "balance", m("account", "acc-b"));
                long col = count("ledger", "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='POSTINGS' AND COLUMN_NAME='AMOUNT_CENTS'");
                delivered.put("ledger", r != null && "725".equals(r.get("balanceCents")) && col == 1);
                r = cl("customer", "statement", m("account", "acc-b"));
                delivered.put("customer", r != null && "725".equals(r.get("availableCents")));
                break;
            }
            case "S3": {
                cl("ledger", "post", m("account", "acc-i", "amount", "4.00", "requestId", "ra", "idempotencyKey", "ik1"));
                Map<String, String> r2 = cl("ledger", "post", m("account", "acc-i", "amount", "4.00", "requestId", "rb", "idempotencyKey", "ik1"));
                Map<String, String> pc = cl("ledger", "postings", m("account", "acc-i"));
                delivered.put("ledger", r2 != null && "true".equals(r2.get("dup")) && pc != null && "1".equals(pc.get("count")));
                e.loseNextPost = true;
                r = cl("customer", "pay", m("customerId", "c1", "account", "acc-r", "amount", "3.00", "ref", "ref-r"));
                pc = cl("ledger", "postings", m("account", "acc-r"));
                delivered.put("customer", r != null && "OK".equals(r.get("status")) && pc != null && "1".equals(pc.get("count")));
                break;
            }
            case "S4": {
                Map<String, String> a = cl("customer", "consent.check", m("customerId", "c0", "purpose", "marketing"));
                Map<String, String> b = cl("customer", "consent.check", m("customerId", "c2", "purpose", "marketing"));
                delivered.put("customer", a != null && b != null && "false".equals(a.get("allowed")) && "true".equals(b.get("allowed")));
                e.drain();
                e.tick = ((e.tick / 100) + 1) * 100;
                Map<String, String> before = cl("notifier", "sent", m("customerId", "c2"));
                for (int k = 1; k <= 3; k++) { cl("customer", "offer", m("customerId", "c2", "offerId", "ac" + k)); e.advance(); }
                e.drain();
                Map<String, String> after = cl("notifier", "sent", m("customerId", "c2"));
                boolean ok = before != null && after != null && Integer.parseInt(after.get("count")) - Integer.parseInt(before.get("count")) == 2 && after.get("capped") != null && before.get("capped") != null && Integer.parseInt(after.get("capped")) - Integer.parseInt(before.get("capped")) == 1;
                delivered.put("notifier", ok);
                break;
            }
            case "S5": {
                r = cl("decision", "score", m("income", "1000", "amount", "250"));
                delivered.put("decision", r != null && "750".equals(r.get("score")));
                boolean ok = true;
                for (int[] c : CASES) {
                    Map<String, String> ap = cl("customer", "apply", m("customerId", "c1", "income", "" + c[0], "amount", "" + c[1]));
                    ok &= ap != null && refDecision(c[0], c[1]).equals(ap.get("decision"));
                }
                delivered.put("customer", ok);
                break;
            }
            default: { // S0
                r = cl("decision", "score", m("income", "1000", "amount", "100"));
                String reason = r == null ? null : r.get("reason");
                delivered.put("decision", reason != null && !reason.isEmpty());
                Map<String, String> ap = cl("customer", "apply", m("customerId", "c1", "income", "1000", "amount", "100"));
                delivered.put("customer", ap != null && reason != null && reason.equals(ap.get("reason")));
            }
        }
    }

    // ------------------------------------------------------------------ output

    public String toJson(String mode) {
        StringBuilder b = new StringBuilder("{\n");
        b.append("\"mode\":").append(Json.q(mode)).append(",\"scenario\":").append(Json.q(scen)).append(",\"fault\":").append(Json.q(fault));
        b.append(",\"aborted\":").append(aborted).append(",\"abortReason\":").append(Json.q(abortReason));
        b.append(",\"recovered\":").append(recovered == null ? "null" : recovered.toString());
        b.append(",\"failedJourneys\":").append(failed).append(",\"paymentsNotOk\":").append(payFailed).append(",\"deadLetters\":").append(e.deadLetters);
        b.append(",\"customerRuleTick\":").append(e.customerRuleTick);
        b.append(",\n\"violations\":[");
        for (int i = 0; i < violations.size(); i++) {
            String[] v = violations.get(i);
            if (i > 0) b.append(',');
            b.append("{\"inv\":").append(Json.q(v[0])).append(",\"detail\":").append(Json.q(v[1])).append(",\"at\":").append(Json.q(v[2])).append('}');
        }
        b.append("],\n\"delivered\":{");
        int n = 0;
        for (Map.Entry<String, Boolean> d : delivered.entrySet()) { if (n++ > 0) b.append(','); b.append(Json.q(d.getKey())).append(':').append(d.getValue()); }
        b.append("},\n\"timeline\":[\n").append(String.join(",\n", e.timeline)).append("\n]}\n");
        return b.toString();
    }
}
