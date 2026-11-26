package estate.svc;

import org.junit.jupiter.api.Test;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

class MainTest {
    private Main start(FakeContext c) throws Exception {
        Main m = new Main();
        m.start(c);
        return m;
    }

    @Test
    void statementFollowsPaymentEvents() throws Exception {
        FakeContext c = new FakeContext();
        c.stubs.put("ledger.balance", r -> Map.of("balance", "19.75", "balanceCents", "1975"));
        Main m = start(c);
        m.onEvent("payment.posted", Map.of("account", "a1", "amount", "12.50", "requestId", "r1"));
        m.onEvent("payment.posted", Map.of("account", "a1", "amount", "7.25", "requestId", "r2"));
        Map<String, String> s = m.handle("statement", Map.of("account", "a1"));
        assertEquals("19.75", s.get("balance"));
        assertEquals("2", s.get("lines"));
        assertEquals("1975", s.get("availableCents"));
    }

    @Test
    void payPostsToTheLedgerAndReportsTimeouts() throws Exception {
        FakeContext c = new FakeContext();
        Main m = start(c);
        c.stubs.put("ledger.post", r -> Map.of("id", "1", "dup", "false"));
        assertEquals("OK", m.handle("pay", Map.of("customerId", "c1", "account", "a1", "amount", "5.00", "ref", "r1")).get("status"));
        c.stubs.put("ledger.post", r -> { throw new estate.api.ServiceException("timeout", "lost"); });
        assertEquals("FAILED", m.handle("pay", Map.of("customerId", "c1", "account", "a1", "amount", "5.00", "ref", "r2")).get("status"));
    }

    @Test
    void applyUsesScoreThresholds() throws Exception {
        FakeContext c = new FakeContext();
        Main m = start(c);
        c.stubs.put("decision.score", r -> Map.of("score", "65"));
        assertEquals("APPROVE", m.handle("apply", Map.of("customerId", "c1", "income", "1000", "amount", "100")).get("decision"));
        c.stubs.put("decision.score", r -> Map.of("score", "45"));
        assertEquals("REFER", m.handle("apply", Map.of("customerId", "c1", "income", "1000", "amount", "100")).get("decision"));
        c.stubs.put("decision.score", r -> Map.of("score", "10"));
        assertEquals("DECLINE", m.handle("apply", Map.of("customerId", "c1", "income", "1000", "amount", "100")).get("decision"));
    }

    @Test
    void offersNeedConsent() throws Exception {
        FakeContext c = new FakeContext();
        Main m = start(c);
        m.handle("create", Map.of("customerId", "c1", "consent", "explicit"));
        m.handle("create", Map.of("customerId", "c2", "consent", "none"));
        assertEquals("true", m.handle("offer", Map.of("customerId", "c1", "offerId", "o1")).get("queued"));
        assertEquals("false", m.handle("offer", Map.of("customerId", "c2", "offerId", "o1")).get("queued"));
        assertEquals(1, c.events.size());
    }
}
