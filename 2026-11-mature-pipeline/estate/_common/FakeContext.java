package estate.svc;

import estate.api.Context;
import estate.api.ServiceException;

import java.sql.Connection;
import java.sql.DriverManager;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;

/** Test double for the platform: in-memory H2, stubbed calls, recorded events. */
public class FakeContext implements Context {
    private static final AtomicInteger N = new AtomicInteger();

    public interface Stub { Map<String, String> apply(Map<String, String> req) throws ServiceException; }

    public final Map<String, Stub> stubs = new HashMap<>();
    public final List<String> published = new ArrayList<>();
    public final List<Map<String, String>> events = new ArrayList<>();
    public long tick = 0;
    private final Connection db;

    public FakeContext() {
        try {
            db = DriverManager.getConnection("jdbc:h2:mem:test" + N.incrementAndGet() + ";DB_CLOSE_DELAY=-1");
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }

    public Connection db() { return db; }

    public Map<String, String> call(String service, String op, Map<String, String> request) throws ServiceException {
        Stub s = stubs.get(service + "." + op);
        if (s == null) throw new ServiceException("unavailable", "no stub for " + service + "." + op);
        return s.apply(request);
    }

    public void publish(String topic, Map<String, String> event) { published.add(topic); events.add(event); }

    public long now() { return tick; }
}
