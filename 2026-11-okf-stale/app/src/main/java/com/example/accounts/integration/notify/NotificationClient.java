package com.example.accounts.integration.notify;

/** Sends push and email messages to customers through the notification service. */
public interface NotificationClient {

    void send(Notification notification);
}
