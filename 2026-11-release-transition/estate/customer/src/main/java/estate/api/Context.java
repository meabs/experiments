package estate.api;

import java.sql.Connection;
import java.util.Map;

/** What the platform gives an instance. The database is shared by every instance and every version of the service. */
public interface Context {
    Connection db();

    /** Synchronous call to another service. Throws ServiceException with code "timeout", "unavailable" or "error". */
    Map<String, String> call(String service, String op, Map<String, String> request) throws ServiceException;

    /** Publish an event; consumers receive it a few ticks later. */
    void publish(String topic, Map<String, String> event);

    /** Platform clock (ticks). */
    long now();
}
