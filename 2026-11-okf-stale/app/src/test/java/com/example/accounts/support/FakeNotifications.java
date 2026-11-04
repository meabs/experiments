package com.example.accounts.support;

import java.util.ArrayList;
import java.util.List;

import com.example.accounts.integration.notify.Notification;
import com.example.accounts.integration.notify.NotificationClient;

/** Records messages. {@link #failNext()} makes the next send throw, as the service does when it is down. */
public class FakeNotifications implements NotificationClient {

    public final List<Notification> sent = new ArrayList<>();
    private boolean fail;

    public void reset() {
        sent.clear();
        fail = false;
    }

    public void failNext() {
        this.fail = true;
    }

    @Override
    public synchronized void send(Notification notification) {
        if (fail) {
            fail = false;
            throw new IllegalStateException("notification service unavailable");
        }
        sent.add(notification);
    }
}
