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

/** Ledger: persistent postings with idempotent posting by requestId. */
public class Main implements Service {
    private Context ctx;
    private Connection db;

    @Override
    public void start(Context c) throws Exception {
        this.ctx = c;
        this.db = c.db();
        try (Statement s = db.createStatement()) {
            s.execute("CREATE TABLE IF NOT EXISTS schema_version(v INT NOT NULL)");
            int v = 0;
            try (ResultSet rs = s.executeQuery("SELECT COALESCE(MAX(v),0) FROM schema_version")) {
                if (rs.next()) v = rs.getInt(1);
            }
            if (v < 1) {
                s.execute("CREATE TABLE postings(id BIGINT AUTO_INCREMENT PRIMARY KEY, account VARCHAR(40) NOT NULL, "
                        + "amount DECIMAL(18,2) NOT NULL, request_id VARCHAR(80) NOT NULL UNIQUE, ts BIGINT NOT NULL)");
                s.execute("INSERT INTO schema_version(v) VALUES (1)");
            }
        }
    }

    @Override
    public Map<String, String> handle(String op, Map<String, String> req) throws ServiceException {
        try {
            switch (op) {
                case "health": return health();
                case "post": return post(req);
                case "balance": return balance(req);
                case "postings": return postings(req);
                default: throw new ServiceException("error", "unknown op " + op);
            }
        } catch (ServiceException e) {
            throw e;
        } catch (Exception e) {
            throw new ServiceException("error", String.valueOf(e.getMessage()));
        }
    }

    private Map<String, String> health() throws Exception {
        try (Statement s = db.createStatement(); ResultSet rs = s.executeQuery("SELECT COALESCE(SUM(amount),0) FROM postings")) {
            rs.next();
        }
        return Map.of("status", "UP");
    }

    private Map<String, String> post(Map<String, String> req) throws Exception {
        String account = req.get("account");
        BigDecimal amount = new BigDecimal(req.get("amount")).setScale(2);
        String requestId = req.get("requestId");
        try (PreparedStatement q = db.prepareStatement("SELECT id FROM postings WHERE request_id = ?")) {
            q.setString(1, requestId);
            try (ResultSet rs = q.executeQuery()) {
                if (rs.next()) return Map.of("id", String.valueOf(rs.getLong(1)), "dup", "true");
            }
        }
        long id;
        try (PreparedStatement ins = db.prepareStatement(
                "INSERT INTO postings(account, amount, request_id, ts) VALUES (?,?,?,?)", Statement.RETURN_GENERATED_KEYS)) {
            ins.setString(1, account);
            ins.setBigDecimal(2, amount);
            ins.setString(3, requestId);
            ins.setLong(4, ctx.now());
            ins.executeUpdate();
            try (ResultSet k = ins.getGeneratedKeys()) { k.next(); id = k.getLong(1); }
        }
        Map<String, String> ev = new HashMap<>();
        ev.put("account", account);
        ev.put("amountMinor", String.valueOf(amount.movePointRight(2).longValueExact()));
        ev.put("requestId", requestId);
        ctx.publish("payment.posted", ev);
        return Map.of("id", String.valueOf(id), "dup", "false");
    }

    private Map<String, String> balance(Map<String, String> req) throws Exception {
        try (PreparedStatement q = db.prepareStatement("SELECT COALESCE(SUM(amount),0) FROM postings WHERE account = ?")) {
            q.setString(1, req.get("account"));
            try (ResultSet rs = q.executeQuery()) {
                rs.next();
                return Map.of("balance", rs.getBigDecimal(1).setScale(2).toPlainString());
            }
        }
    }

    private Map<String, String> postings(Map<String, String> req) throws Exception {
        try (PreparedStatement q = db.prepareStatement("SELECT COUNT(*), COALESCE(SUM(amount),0) FROM postings WHERE account = ?")) {
            q.setString(1, req.get("account"));
            try (ResultSet rs = q.executeQuery()) {
                rs.next();
                return Map.of("count", String.valueOf(rs.getLong(1)), "total", rs.getBigDecimal(2).setScale(2).toPlainString());
            }
        }
    }
}
