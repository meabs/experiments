package com.example.accounts.account;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;

import org.junit.jupiter.api.Test;

class BalanceAlertPublisherTest {

    @Test
    void alertReachesTheBroker() throws Exception {
        List<String> sent = new CopyOnWriteArrayList<>();
        CountDownLatch delivered = new CountDownLatch(1);
        BalanceAlertPublisher publisher = new BalanceAlertPublisher(m -> {
            sent.add(m);
            delivered.countDown();
        });

        publisher.publish(1L, "Balance below 50.00");

        assertTrue(delivered.await(50, TimeUnit.MILLISECONDS), "alert not delivered");
        assertEquals(List.of("1:Balance below 50.00"), sent);
    }
}
