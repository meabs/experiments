package estate.svc;

import estate.api.Context;
import estate.api.Service;
import estate.api.ServiceException;

import java.util.Map;

/** Decision: a risk score for a credit request. Stateless. Score runs from 0 (worst) to 100 (best). */
public class Main implements Service {
    @Override
    public void start(Context c) {}

    @Override
    public Map<String, String> handle(String op, Map<String, String> req) throws ServiceException {
        switch (op) {
            case "health": return Map.of("status", "UP");
            case "score": return score(req);
            default: throw new ServiceException("error", "unknown op " + op);
        }
    }

    private Map<String, String> score(Map<String, String> req) throws ServiceException {
        try {
            long income = Long.parseLong(req.get("income"));
            long amount = Long.parseLong(req.get("amount"));
            if (income <= 0) throw new ServiceException("error", "income must be positive");
            long score = Math.max(0, Math.min(1000, 1000 - (amount * 1000) / income));
            return Map.of("score", String.valueOf(score));
        } catch (NumberFormatException e) {
            throw new ServiceException("error", "bad number");
        }
    }
}
