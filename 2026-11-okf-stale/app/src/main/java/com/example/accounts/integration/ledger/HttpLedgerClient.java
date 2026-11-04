package com.example.accounts.integration.ledger;

import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestClient;

@Component
public class HttpLedgerClient implements LedgerClient {

    private final RestClient http;

    public HttpLedgerClient(LedgerProperties props) {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(props.timeout());
        factory.setReadTimeout(props.timeout());
        this.http = RestClient.builder().baseUrl(props.url()).requestFactory(factory).build();
    }

    @Override
    public void post(LedgerPosting posting) {
        try {
            http.post().uri("/postings").header("X-Reference", posting.reference()).body(posting).retrieve().toBodilessEntity();
        } catch (ResourceAccessException e) {
            throw new LedgerTimeoutException("Ledger did not answer", e);
        }
    }
}
