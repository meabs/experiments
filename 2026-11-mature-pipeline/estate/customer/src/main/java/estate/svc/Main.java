package estate.svc;

import estate.api.Context;
import estate.api.Service;
import estate.api.ServiceException;

import java.math.BigDecimal;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.Statement;
import java.util.HashMap;
import java.util.Map;

/**
 * Customer: profiles and consent, payments (through the ledger), a statement read model built from ledger events,
 * credit applications (through the decision service) and marketing offers.
 */
public class Main implements Service {
    private Context ctx;
    private Connection db;

    @Override
    public void start(Context c) throws Exception {
        this.ctx = c;
        this.db = c.db();
        try (Statement s = db.createStatement()) {
            s.execute("CREATE TABLE IF NOT EXISTS customers(id VARCHAR(40) PRIMARY KEY, consent VARCHAR(20) NOT NULL)");
            s.execute("CREATE TABLE IF NOT EXISTS statement(account VARCHAR(40) PRIMARY KEY, balance_cents BIGINT NOT NULL, lines INT NOT NULL)");
        }
    }

    @Override
    public Map<String, String> handle(String op, Map<String, String> req) throws ServiceException {
        try {
            switch (op) {
                case "health": {
                    try (Statement s = db.createStatement(); ResultSet rs = s.executeQuery("SELECT COUNT(*) FROM customers")) { rs.next(); }
                    return Map.of("status", "UP");
                }
                case "create": return create(req);
                case "pay": return pay(req);
                case "statement": return statement(req);
                case "apply": return apply(req);
                case "offer": return offer(req);
                case "consent.check": return consentCheck(req);
                default: throw new ServiceException("error", "unknown op " + op);
            }
        } catch (ServiceException e) {
            throw e;
        } catch (Exception e) {
            throw new ServiceException("error", String.valueOf(e.getMessage()));
        }
    }

    /** consent is one of: none, implied (legacy customers), explicit. */
    private Map<String, String> create(Map<String, String> req) throws Exception {
        try (PreparedStatement ins = db.prepareStatement("INSERT INTO customers(id, consent) VALUES (?,?)")) {
            ins.setString(1, req.get("customerId"));
            ins.setString(2, req.get("consent"));
            ins.executeUpdate();
        }
        return Map.of("status", "OK");
    }

    private Map<String, String> pay(Map<String, String> req) throws Exception {
        Map<String, String> post = new HashMap<>();
        post.put("account", req.get("account"));
        post.put("amount", req.get("amount"));
        post.put("requestId", req.get("ref"));
        try {
            ctx.call("ledger", "post", post);
            return Map.of("status", "OK");
        } catch (ServiceException e) {
            if ("timeout".equals(e.code)) return Map.of("status", "FAILED", "reason", "timeout");
            throw e;
        }
    }

    @Override
    public void onEvent(String topic, Map<String, String> ev) throws Exception {
        if (!"payment.posted".equals(topic)) return;
        long cents = new BigDecimal(ev.get("amount")).movePointRight(2).longValueExact();
        try (PreparedStatement up = db.prepareStatement("UPDATE statement SET balance_cents = balance_cents + ?, lines = lines + 1 WHERE account = ?")) {
            up.setLong(1, cents);
            up.setString(2, ev.get("account"));
            if (up.executeUpdate() == 0) {
                try (PreparedStatement ins = db.prepareStatement("INSERT INTO statement(account, balance_cents, lines) VALUES (?,?,1)")) {
                    ins.setString(1, ev.get("account"));
                    ins.setLong(2, cents);
                    ins.executeUpdate();
                }
            }
        }
    }

    private Map<String, String> statement(Map<String, String> req) throws Exception {
        try (PreparedStatement q = db.prepareStatement("SELECT balance_cents, lines FROM statement WHERE account = ?")) {
            q.setString(1, req.get("account"));
            try (ResultSet rs = q.executeQuery()) {
                if (!rs.next()) return Map.of("balance", "0.00", "lines", "0");
                return Map.of("balance", BigDecimal.valueOf(rs.getLong(1), 2).toPlainString(), "lines", String.valueOf(rs.getInt(2)));
            }
        }
    }

    /** Approve at a score of 60 or more, refer at 40 or more, otherwise decline. */
    private Map<String, String> apply(Map<String, String> req) throws Exception {
        Map<String, String> r = ctx.call("decision", "score", Map.of("income", req.get("income"), "amount", req.get("amount")));
        int score = Integer.parseInt(r.get("score"));
        String decision = score >= 60 ? "APPROVE" : score >= 40 ? "REFER" : "DECLINE";
        return Map.of("decision", decision, "score", String.valueOf(score));
    }

    private String consentOf(String customerId) throws Exception {
        try (PreparedStatement q = db.prepareStatement("SELECT consent FROM customers WHERE id = ?")) {
            q.setString(1, customerId);
            try (ResultSet rs = q.executeQuery()) { return rs.next() ? rs.getString(1) : "none"; }
        }
    }

    private Map<String, String> consentCheck(Map<String, String> req) throws Exception {
        String c = consentOf(req.get("customerId"));
        boolean allowed = c.equals("implied") || c.equals("explicit");
        return Map.of("allowed", String.valueOf(allowed), "basis", c);
    }

    private Map<String, String> offer(Map<String, String> req) throws Exception {
        String c = consentOf(req.get("customerId"));
        if (!(c.equals("implied") || c.equals("explicit"))) return Map.of("queued", "false");
        ctx.publish("offer.queued", Map.of("customerId", req.get("customerId"), "offerId", req.get("offerId")));
        return Map.of("queued", "true");
    }
}
