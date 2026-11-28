package estate.svc;

import org.junit.jupiter.api.Test;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

class MainTest {
    @Test
    void queuedOfferIsSent() throws Exception {
        FakeContext c = new FakeContext();
        Main m = new Main();
        m.start(c);
        c.tick = 7;
        m.onEvent("offer.queued", Map.of("customerId", "c1", "offerId", "o1"));
        Map<String, String> r = m.handle("sent", Map.of("customerId", "c1"));
        assertEquals("1", r.get("count"));
        assertEquals("7", r.get("ticks"));
    }

    @Test
    void healthIsUp() throws Exception {
        Main m = new Main();
        m.start(new FakeContext());
        assertEquals("UP", m.handle("health", Map.of()).get("status"));
    }
}
