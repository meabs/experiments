package com.example.accounts.account;

import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ThreadLocalRandom;
import java.util.function.Consumer;

/** Sends low-balance alerts to the notification broker without holding up the request that triggered them. */
public class BalanceAlertPublisher {

    private final Consumer<String> broker;

    public BalanceAlertPublisher(Consumer<String> broker) {
        this.broker = broker;
    }

    public CompletableFuture<Void> publish(long accountId, String message) {
        return CompletableFuture.runAsync(() -> {
            brokerRoundTrip();
            broker.accept(accountId + ":" + message);
        });
    }

    // Stands in for the network hop to the broker until the real client is wired in.
    private static void brokerRoundTrip() {
        try {
            Thread.sleep(ThreadLocalRandom.current().nextInt(0, 100));
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}
