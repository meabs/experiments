package estate.svc;

import estate.api.Context;
import estate.api.Service;
import estate.api.ServiceException;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.Statement;
import java.util.Map;

/** Notifier: sends marketing offers queued by the customer service. A "send" is a row in `sent`. */
public class Main implements Service {
    private Context ctx;
    private Connection db;

    @Override
    public void start(Context c) throws Exception {
        this.ctx = c;
        this.db = c.db();
        try (Statement s = db.createStatement()) {
            s.execute("CREATE TABLE IF NOT EXISTS capped(customer_id VARCHAR(40) NOT NULL, n INT NOT NULL)");
            s.execute("CREATE TABLE IF NOT EXISTS sent(id BIGINT AUTO_INCREMENT PRIMARY KEY, customer_id VARCHAR(40) NOT NULL, "
                    + "offer_id VARCHAR(40) NOT NULL, ts BIGINT NOT NULL)");
        }
    }

    @Override
    public void onEvent(String topic, Map<String, String> ev) throws Exception {
        if (!"offer.queued".equals(topic)) return;
        Map<String, String> consent = ctx.call("customer", "consent.check", Map.of("customerId", ev.get("customerId"), "purpose", "marketing"));
        if (!"true".equals(consent.get("allowed"))) return;
        long day = ctx.now() / 100;
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
        try (PreparedStatement ins = db.prepareStatement("INSERT INTO sent(customer_id, offer_id, ts) VALUES (?,?,?)")) {
            ins.setString(1, ev.get("customerId"));
            ins.setString(2, ev.get("offerId"));
            ins.setLong(3, ctx.now());
            ins.executeUpdate();
        }
    }

    @Override
    public Map<String, String> handle(String op, Map<String, String> req) throws ServiceException {
        try {
            switch (op) {
                case "health": {
                    try (Statement s = db.createStatement(); ResultSet rs = s.executeQuery("SELECT COUNT(*) FROM sent")) { rs.next(); }
                    return Map.of("status", "UP");
                }
                case "sent": return sent(req);
                default: throw new ServiceException("error", "unknown op " + op);
            }
        } catch (ServiceException e) {
            throw e;
        } catch (Exception e) {
            throw new ServiceException("error", String.valueOf(e.getMessage()));
        }
    }

    /** Messages sent to a customer: count, and the ticks as a comma separated list. */
    private Map<String, String> sent(Map<String, String> req) throws Exception {
        try (PreparedStatement q = db.prepareStatement("SELECT ts FROM sent WHERE customer_id = ? ORDER BY id")) {
            q.setString(1, req.get("customerId"));
            StringBuilder ticks = new StringBuilder();
            int n = 0;
            try (ResultSet rs = q.executeQuery()) {
                while (rs.next()) { if (n++ > 0) ticks.append(','); ticks.append(rs.getLong(1)); }
            }
            long capped = 0;
            try (PreparedStatement c = db.prepareStatement("SELECT COALESCE(SUM(n),0) FROM capped WHERE customer_id = ?")) {
                c.setString(1, req.get("customerId"));
                try (ResultSet rs = c.executeQuery()) { rs.next(); capped = rs.getLong(1); }
            }
            return Map.of("count", String.valueOf(n), "ticks", ticks.toString(), "capped", String.valueOf(capped));
        }
    }
}
