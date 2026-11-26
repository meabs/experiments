package estate.api;

public class ServiceException extends Exception {
    public final String code;

    public ServiceException(String code, String message) {
        super(message);
        this.code = code;
    }
}
