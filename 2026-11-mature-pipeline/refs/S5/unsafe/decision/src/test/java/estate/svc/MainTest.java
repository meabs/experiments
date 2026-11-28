package estate.svc;

import org.junit.jupiter.api.Test;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

class MainTest {
    @Test
    void scoreFallsAsTheRequestGrows() throws Exception {
        Main m = new Main();
        assertEquals("900", m.handle("score", Map.of("income", "1000", "amount", "100")).get("score"));
        assertEquals("500", m.handle("score", Map.of("income", "1000", "amount", "500")).get("score"));
        assertEquals("0", m.handle("score", Map.of("income", "1000", "amount", "5000")).get("score"));
    }

    @Test
    void healthIsUp() throws Exception {
        assertEquals("UP", new Main().handle("health", Map.of()).get("status"));
    }
}
