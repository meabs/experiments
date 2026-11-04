package com.example.accounts.integration.scheme;

import java.util.Optional;

/** Sends payment instructions to the payment scheme gateway. */
public interface SchemeClient {

    /**
     * @throws SchemeRejectedException if the scheme refuses the instruction
     * @throws SchemeTimeoutException if the scheme does not answer in time
     */
    SchemeReceipt submit(SchemePayment payment);

    /**
     * The scheme's status query ({@code GET /v2/instructions/{reference}}): the instruction the scheme holds under this
     * reference, if any. Not used by the service yet.
     *
     * @throws SchemeTimeoutException if the scheme does not answer in time
     */
    Optional<SchemeReceipt> find(String reference);
}
