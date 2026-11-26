"""Generate the reference changes (artifact-correct, unit tests pass) for each scenario into refs/<scenario>/<variant>/.

Each variant is {service: files} overlaid on the base estate, plus an optional release plan. `safe` variants are the
changes a careful team would ship; `unsafe` ones satisfy the tickets and pass every test but break the transition.
Run: python3 -I scripts/refs.py
"""
import os, re, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
E = os.path.join(HERE, "..", "estate")
OUT = os.path.join(HERE, "..", "refs")
MAIN = "src/main/java/estate/svc/Main.java"
TEST = "src/test/java/estate/svc/MainTest.java"


def rd(svc, p):
    return open(os.path.join(E, svc, p)).read()


def rep(t, old, new):
    assert t.count(old) == 1, (t.count(old), old[:70])
    return t.replace(old, new)


def method(t, name, new_text, next_name=None):
    """Replace the private method `name` up to the next `private`/end of class."""
    i = t.index("    private Map<String, String> %s(" % name)
    j = t.index("    private ", i + 10) if next_name is None and "    private " in t[i + 10:] else (t.index("    private Map<String, String> %s(" % next_name) if next_name else t.rindex("}"))
    return t[:i] + new_text + "\n" + t[j:]


V = {}  # scenario -> variant -> {"files": {svc: {path: text}}, "plan": str|None}


def add(s, name, files, plan=None):
    V.setdefault(s, {})[name] = {"files": files, "plan": plan}


# ---------------------------------------------------------------- S1 event schema
led = rd("ledger", MAIN); ledt = rd("ledger", TEST)
led_drop = rep(led, 'ev.put("amount", amount.toPlainString());', 'ev.put("amountMinor", String.valueOf(amount.movePointRight(2).longValueExact()));')
ledt_drop = rep(ledt, 'assertEquals("12.50", c.events.get(0).get("amount"));', 'assertEquals("1250", c.events.get(0).get("amountMinor"));')
cus = rd("customer", MAIN); cust = rd("customer", TEST)
cus_naive = rep(cus, 'long cents = new BigDecimal(ev.get("amount")).movePointRight(2).longValueExact();', 'long cents = Long.parseLong(ev.get("amountMinor"));')
cus_tol = rep(cus, 'long cents = new BigDecimal(ev.get("amount")).movePointRight(2).longValueExact();',
              'long cents = ev.containsKey("amountMinor") ? Long.parseLong(ev.get("amountMinor")) : new BigDecimal(ev.get("amount")).movePointRight(2).longValueExact();')
cust_s1 = rep(rep(cust, '"amount", "12.50"', '"amountMinor", "1250"'), '"amount", "7.25"', '"amountMinor", "725"')
add("S1", "unsafe", {"ledger": {MAIN: led_drop, TEST: ledt_drop}, "customer": {MAIN: cus_naive, TEST: cust_s1}})
add("S1", "safe", {"ledger": {MAIN: led_drop, TEST: ledt_drop}, "customer": {MAIN: cus_tol, TEST: cust_s1}})

# ---------------------------------------------------------------- S2 migration
MIG_NAIVE = '''            if (v < 2) {
                s.execute("ALTER TABLE postings ADD COLUMN amount_cents BIGINT");
                s.execute("UPDATE postings SET amount_cents = amount * 100");
                s.execute("ALTER TABLE postings ALTER COLUMN amount_cents SET NOT NULL");
                s.execute("ALTER TABLE postings DROP COLUMN amount");
                s.execute("INSERT INTO schema_version(v) VALUES (2)");
            }
'''
MIG_EXPAND = '''            if (v < 2) {
                s.execute("ALTER TABLE postings ADD COLUMN amount_cents BIGINT");
                s.execute("UPDATE postings SET amount_cents = ROUND(amount * 100)");
                s.execute("INSERT INTO schema_version(v) VALUES (2)");
            }
'''
anchor = '''                s.execute("INSERT INTO schema_version(v) VALUES (1)");
            }
'''
BAL_CENTS = '''    private Map<String, String> balance(Map<String, String> req) throws Exception {
        try (PreparedStatement q = db.prepareStatement("SELECT COALESCE(SUM(%s),0) FROM postings WHERE account = ?")) {
            q.setString(1, req.get("account"));
            try (ResultSet rs = q.executeQuery()) {
                rs.next();
                long cents = rs.getLong(1);
                return Map.of("balance", BigDecimal.valueOf(cents, 2).toPlainString(), "balanceCents", String.valueOf(cents));
            }
        }
    }
'''
POST_CENTS = '''    private Map<String, String> postings(Map<String, String> req) throws Exception {
        try (PreparedStatement q = db.prepareStatement("SELECT COUNT(*), COALESCE(SUM(%s),0) FROM postings WHERE account = ?")) {
            q.setString(1, req.get("account"));
            try (ResultSet rs = q.executeQuery()) {
                rs.next();
                return Map.of("count", String.valueOf(rs.getLong(1)), "total", BigDecimal.valueOf(rs.getLong(2), 2).toPlainString());
            }
        }
    }
'''
naive = rep(led, anchor, anchor + MIG_NAIVE)
naive = rep(naive, 'SELECT COALESCE(SUM(amount),0) FROM postings")) {\n            rs.next();', 'SELECT COALESCE(SUM(amount_cents),0) FROM postings")) {\n            rs.next();')
naive = rep(naive, 'INSERT INTO postings(account, amount, request_id, ts)', 'INSERT INTO postings(account, amount_cents, request_id, ts)')
naive = rep(naive, 'ins.setBigDecimal(2, amount);', 'ins.setLong(2, amount.movePointRight(2).longValueExact());')
naive = method(naive, "balance", BAL_CENTS % "amount_cents", "postings")
naive = method(naive, "postings", POST_CENTS % "amount_cents")
exp = rep(led, anchor, anchor + MIG_EXPAND)
exp = rep(exp, 'INSERT INTO postings(account, amount, request_id, ts) VALUES (?,?,?,?)', 'INSERT INTO postings(account, amount, amount_cents, request_id, ts) VALUES (?,?,?,?,?)')
exp = rep(exp, 'ins.setBigDecimal(2, amount);\n            ins.setString(3, requestId);\n            ins.setLong(4, ctx.now());',
          'ins.setBigDecimal(2, amount);\n            ins.setLong(3, amount.movePointRight(2).longValueExact());\n            ins.setString(4, requestId);\n            ins.setLong(5, ctx.now());')
COAL = "COALESCE(amount_cents, ROUND(amount * 100))"
exp = method(exp, "balance", BAL_CENTS % COAL, "postings")
exp = method(exp, "postings", POST_CENTS % COAL)
ST_NEW = '''    private Map<String, String> statement(Map<String, String> req) throws Exception {
        Map<String, String> l = ctx.call("ledger", "balance", Map.of("account", req.get("account")));
        %s
        try (PreparedStatement q = db.prepareStatement("SELECT balance_cents, lines FROM statement WHERE account = ?")) {
            q.setString(1, req.get("account"));
            try (ResultSet rs = q.executeQuery()) {
                if (!rs.next()) return Map.of("balance", "0.00", "lines", "0", "availableCents", available);
                return Map.of("balance", BigDecimal.valueOf(rs.getLong(1), 2).toPlainString(), "lines", String.valueOf(rs.getInt(2)), "availableCents", available);
            }
        }
    }
'''
cus2_naive = method(cus, "statement", ST_NEW % 'String available = String.valueOf(Long.parseLong(l.get("balanceCents")));', "apply")
cus2_tol = method(cus, "statement", ST_NEW % 'String available = l.containsKey("balanceCents") ? l.get("balanceCents") : new BigDecimal(l.get("balance")).movePointRight(2).toBigInteger().toString();', "apply")
cust2 = rep(cust, '''        FakeContext c = new FakeContext();
        Main m = start(c);
        m.onEvent("payment.posted", Map.of("account", "a1", "amount", "12.50", "requestId", "r1"));''',
            '''        FakeContext c = new FakeContext();
        c.stubs.put("ledger.balance", r -> Map.of("balance", "19.75", "balanceCents", "1975"));
        Main m = start(c);
        m.onEvent("payment.posted", Map.of("account", "a1", "amount", "12.50", "requestId", "r1"));''')
cust2 = rep(cust2, 'assertEquals("2", s.get("lines"));', 'assertEquals("2", s.get("lines"));\n        assertEquals("1975", s.get("availableCents"));')
add("S2", "unsafe", {"ledger": {MAIN: naive}, "customer": {MAIN: cus2_tol, TEST: cust2}})
add("S2", "safe", {"ledger": {MAIN: exp}, "customer": {MAIN: cus2_tol, TEST: cust2}})

# ---------------------------------------------------------------- S3 retries and idempotency
l3 = rep(led, anchor, anchor + '''            if (v < 2) {
                s.execute("ALTER TABLE postings ADD COLUMN idem_key VARCHAR(80)");
                s.execute("INSERT INTO schema_version(v) VALUES (2)");
            }
''')
l3 = rep(l3, '''        String requestId = req.get("requestId");
        try (PreparedStatement q = db.prepareStatement("SELECT id FROM postings WHERE request_id = ?")) {
            q.setString(1, requestId);''', '''        String requestId = req.get("requestId");
        String key = req.get("idempotencyKey");
        try (PreparedStatement q = db.prepareStatement(key != null ? "SELECT id FROM postings WHERE idem_key = ?" : "SELECT id FROM postings WHERE request_id = ?")) {
            q.setString(1, key != null ? key : requestId);''')
l3 = rep(l3, 'INSERT INTO postings(account, amount, request_id, ts) VALUES (?,?,?,?)', 'INSERT INTO postings(account, amount, request_id, ts, idem_key) VALUES (?,?,?,?,?)')
l3 = rep(l3, 'ins.setLong(4, ctx.now());', 'ins.setLong(4, ctx.now());\n            ins.setString(5, key);')
l3t = rep(ledt, '    @Test\n    void healthIsUp()', '''    @Test
    void sameIdempotencyKeyPostsOnce() throws Exception {
        FakeContext c = new FakeContext();
        Main m = start(c);
        m.handle("post", Map.of("account", "a1", "amount", "5.00", "requestId", "r1", "idempotencyKey", "k1"));
        Map<String, String> r = m.handle("post", Map.of("account", "a1", "amount", "5.00", "requestId", "r2", "idempotencyKey", "k1"));
        assertEquals("true", r.get("dup"));
        assertEquals("1", m.handle("postings", Map.of("account", "a1")).get("count"));
    }

    @Test
    void healthIsUp()''')
PAY_RETRY = '''    private Map<String, String> pay(Map<String, String> req) throws Exception {
        String ref = req.get("ref");
        for (int attempt = 1; attempt <= 3; attempt++) {
            Map<String, String> post = new HashMap<>();
            post.put("account", req.get("account"));
            post.put("amount", req.get("amount"));
            post.put("requestId", ref + "-" + attempt);
            post.put("idempotencyKey", ref);
            try {
                ctx.call("ledger", "post", post);
                return Map.of("status", "OK");
            } catch (ServiceException e) {
                if (!"timeout".equals(e.code)) throw e;
            }
        }
        return Map.of("status", "FAILED", "reason", "timeout");
    }
'''
c3 = method(cus, "pay", PAY_RETRY, "onEvent") if "private Map<String, String> onEvent" in cus else None
i = cus.index("    private Map<String, String> pay("); j = cus.index("    @Override\n    public void onEvent")
c3 = cus[:i] + PAY_RETRY + "\n" + cus[j:]
add("S3", "unsafe", {"ledger": {MAIN: l3, TEST: l3t}, "customer": {MAIN: c3}})
add("S3", "safe", {"ledger": {MAIN: l3, TEST: l3t}, "customer": {MAIN: c3}}, plan="stage ledger\nstage customer\n")

# ---------------------------------------------------------------- S4 consent
c4 = rep(cus, 'boolean allowed = c.equals("implied") || c.equals("explicit");', 'boolean allowed = c.equals("explicit");')
c4 = rep(c4, 'if (!(c.equals("implied") || c.equals("explicit"))) return Map.of("queued", "false");', 'if (!c.equals("explicit")) return Map.of("queued", "false");')
ntf = rd("notifier", MAIN); ntft = rd("notifier", TEST)
n4 = rep(ntf, '''            s.execute("CREATE TABLE IF NOT EXISTS sent(''', '''            s.execute("CREATE TABLE IF NOT EXISTS capped(customer_id VARCHAR(40) NOT NULL, n INT NOT NULL)");
            s.execute("CREATE TABLE IF NOT EXISTS sent(''')
CAP = '''        long day = ctx.now() / 100;
        try (PreparedStatement q = db.prepareStatement("SELECT COUNT(*) FROM sent WHERE customer_id = ? AND ts / 100 = ?")) {
            q.setString(1, ev.get("customerId"));
            q.setLong(2, day);
            try (ResultSet rs = q.executeQuery()) {
                rs.next();
                if (rs.getInt(1) >= 2) {
                    try (PreparedStatement c = db.prepareStatement("INSERT INTO capped(customer_id, n) VALUES (?,1)")) {
                        c.setString(1, ev.get("customerId"));
                        c.executeUpdate();
                    }
                    return;
                }
            }
        }
'''
RECHECK = '''        Map<String, String> consent = ctx.call("customer", "consent.check", Map.of("customerId", ev.get("customerId"), "purpose", "marketing"));
        if (!"true".equals(consent.get("allowed"))) return;
'''
n4 = rep(n4, '''        if (!"offer.queued".equals(topic)) return;
''', '''        if (!"offer.queued".equals(topic)) return;
''' + CAP)
n4 = rep(n4, '''            return Map.of("count", String.valueOf(n), "ticks", ticks.toString());''', '''            long capped = 0;
            try (PreparedStatement c = db.prepareStatement("SELECT COALESCE(SUM(n),0) FROM capped WHERE customer_id = ?")) {
                c.setString(1, req.get("customerId"));
                try (ResultSet rs = c.executeQuery()) { rs.next(); capped = rs.getLong(1); }
            }
            return Map.of("count", String.valueOf(n), "ticks", ticks.toString(), "capped", String.valueOf(capped));''')
n4s = rep(n4, '''        if (!"offer.queued".equals(topic)) return;
''', '''        if (!"offer.queued".equals(topic)) return;
''' + RECHECK)
n4st = rep(ntft, '        c.tick = 7;', '        c.stubs.put("customer.consent.check", r -> Map.of("allowed", "true", "basis", "explicit"));\n        c.tick = 7;')
add("S4", "unsafe", {"customer": {MAIN: c4}, "notifier": {MAIN: n4}})
add("S4", "safe", {"customer": {MAIN: c4}, "notifier": {MAIN: n4s, TEST: n4st}}, plan="stage notifier\nstage customer\n")

# ---------------------------------------------------------------- S5 decision model
dec = rd("decision", MAIN); dect = rd("decision", TEST)
d5 = rep(dec, 'Math.max(0, Math.min(100, 100 - (amount * 100) / income))', 'Math.max(0, Math.min(1000, 1000 - (amount * 1000) / income))')
d5t = rep(rep(rep(dect, '"90"', '"900"'), '"50"', '"500"'), 'assertEquals("0", m.handle("score", Map.of("income", "1000", "amount", "5000"))', 'assertEquals("0", m.handle("score", Map.of("income", "1000", "amount", "5000"))')
c5 = rep(rep(cus, 'score >= 60 ? "APPROVE" : score >= 40 ? "REFER"', 'score >= 600 ? "APPROVE" : score >= 400 ? "REFER"'), 'Approve at a score of 60 or more, refer at 40 or more', 'Approve at a score of 600 or more, refer at 400 or more')
c5t = rep(rep(rep(cust, 'Map.of("score", "65")', 'Map.of("score", "650")'), 'Map.of("score", "45")', 'Map.of("score", "450")'), 'Map.of("score", "10")', 'Map.of("score", "100")')
add("S5", "unsafe", {"decision": {MAIN: d5, TEST: d5t}, "customer": {MAIN: c5, TEST: c5t}})
add("S5", "safe", {"decision": {MAIN: d5, TEST: d5t}, "customer": {MAIN: c5, TEST: c5t}}, plan="stage customer,decision\n")

# ---------------------------------------------------------------- S0 control
d0 = rep(dec, 'return Map.of("score", String.valueOf(score));', 'return Map.of("score", String.valueOf(score), "reason", "ratio " + (amount * 100) / income + "%");')
d0 = rep(d0, 'return Map.of("score", String.valueOf(score));', 'return Map.of("score", String.valueOf(score));') if False else d0
c0 = rep(cus, 'return Map.of("decision", decision, "score", String.valueOf(score));', '''Map<String, String> out = new HashMap<>();
        out.put("decision", decision);
        out.put("score", String.valueOf(score));
        if (r.get("reason") != null) out.put("reason", r.get("reason"));
        return out;''')
add("S0", "safe", {"decision": {MAIN: d0}, "customer": {MAIN: c0}})

# ---------------------------------------------------------------- write
if os.path.isdir(OUT):
    shutil.rmtree(OUT)
for s, vs in V.items():
    for name, v in vs.items():
        for svc, files in v["files"].items():
            for p, text in files.items():
                path = os.path.join(OUT, s, name, svc, p)
                os.makedirs(os.path.dirname(path), exist_ok=True)
                open(path, "w").write(text)
        if v["plan"]:
            open(os.path.join(OUT, s, name, "plan.txt"), "w").write(v["plan"])
print("wrote", sum(len(v) for v in V.values()), "variants")
