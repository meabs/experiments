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
    void postStoresAndPublishes() throws Exception {
        FakeContext c = new FakeContext();
        Main m = start(c);
        Map<String, String> r = m.handle("post", Map.of("account", "a1", "amount", "12.5", "requestId", "r1"));
        assertEquals("false", r.get("dup"));
        assertEquals("12.50", m.handle("balance", Map.of("account", "a1")).get("balance"));
        assertEquals("payment.posted", c.published.get(0));
        assertEquals("12.50", c.events.get(0).get("amount"));
    }

    @Test
    void sameRequestIdPostsOnce() throws Exception {
        FakeContext c = new FakeContext();
        Main m = start(c);
        m.handle("post", Map.of("account", "a1", "amount", "5.00", "requestId", "r1"));
        Map<String, String> r = m.handle("post", Map.of("account", "a1", "amount", "5.00", "requestId", "r1"));
        assertEquals("true", r.get("dup"));
        assertEquals("1", m.handle("postings", Map.of("account", "a1")).get("count"));
        assertEquals(1, c.events.size());
    }

    @Test
    void healthIsUp() throws Exception {
        assertEquals("UP", start(new FakeContext()).handle("health", Map.of()).get("status"));
    }
}
