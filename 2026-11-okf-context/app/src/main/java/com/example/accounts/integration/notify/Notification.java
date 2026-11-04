package com.example.accounts.integration.notify;

import java.util.Map;

/** A message to a customer: the template id and the values it is filled with. */
public record Notification(String userId, String template, Map<String, String> params) {
}
