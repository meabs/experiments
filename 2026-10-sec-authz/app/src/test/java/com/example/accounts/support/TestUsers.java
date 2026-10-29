package com.example.accounts.support;

import java.util.List;

/** The users in data.sql, with the claims the identity service gives them. */
public final class TestUsers {

    public record User(String id, String tenant, List<String> roles, String scopes) {
    }

    private static final String STANDARD = "accounts:read accounts:write";

    // acme
    public static final User ALICE = new User("u-alice", "acme", List.of("CUSTOMER"), STANDARD); // customer c-1, accounts 1, 2
    public static final User BOB = new User("u-bob", "acme", List.of("CUSTOMER"), STANDARD);     // customer c-2, account 3
    public static final User DANA = new User("u-dana", "acme", List.of("CUSTOMER"), STANDARD);   // customer c-5, account 5 (closed)
    public static final User SAM = new User("u-sam", "acme", List.of("SUPPORT"), STANDARD);      // assigned accounts 1, 2
    public static final User SUE = new User("u-sue", "acme", List.of("SUPPORT"), STANDARD);      // assigned account 3
    public static final User ANA = new User("u-ana", "acme", List.of("SUPPORT", "APPROVER"), STANDARD); // assigned account 3
    public static final User ADA = new User("u-ada", "acme", List.of("ADMIN"), STANDARD);
    public static final User AL = new User("u-al", "acme", List.of("ADMIN", "APPROVER"), STANDARD);
    // globex
    public static final User CAROL = new User("u-carol", "globex", List.of("CUSTOMER"), STANDARD); // customer c-3, account 4
    public static final User GUS = new User("u-gus", "globex", List.of("SUPPORT"), STANDARD);      // assigned account 4
    public static final User GIL = new User("u-gil", "globex", List.of("ADMIN"), STANDARD);
    public static final User GWEN = new User("u-gwen", "globex", List.of("APPROVER"), STANDARD);

    private TestUsers() {
    }
}
