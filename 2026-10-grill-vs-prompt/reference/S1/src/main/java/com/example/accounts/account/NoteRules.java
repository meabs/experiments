package com.example.accounts.account;

final class NoteRules {

    private NoteRules() {
    }

    /** A note body: 1 to 2000 characters after trimming, saved trimmed. */
    static String body(String body) {
        String b = body == null ? "" : body.trim();
        if (b.isEmpty() || b.length() > 2000) {
            throw new IllegalArgumentException("body must be 1 to 2000 characters");
        }
        return b;
    }
}
