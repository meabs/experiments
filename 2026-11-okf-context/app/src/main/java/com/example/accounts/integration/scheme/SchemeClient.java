package com.example.accounts.integration.scheme;

/** Sends payment instructions to the payment scheme gateway. */
public interface SchemeClient {

    /**
     * @throws SchemeRejectedException if the scheme refuses the instruction
     * @throws SchemeTimeoutException if the scheme does not answer in time
     */
    SchemeReceipt submit(SchemePayment payment);
}
