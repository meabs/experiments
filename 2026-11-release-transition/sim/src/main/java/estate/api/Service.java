package estate.api;

import java.util.Map;

/** A deployable service. One instance of the implementing class runs per deployed instance of the service. */
public interface Service {
    /** Called once when an instance starts. Run your schema migrations here. */
    void start(Context ctx) throws Exception;

    /** Handle a synchronous request. `op` and the maps are the service's published contract. */
    Map<String, String> handle(String op, Map<String, String> req) throws ServiceException;

    /** Handle an asynchronous event from a topic this service subscribes to. */
    default void onEvent(String topic, Map<String, String> event) throws Exception {}
}
