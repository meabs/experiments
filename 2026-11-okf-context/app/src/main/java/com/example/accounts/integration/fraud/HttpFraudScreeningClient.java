package com.example.accounts.integration.fraud;

import java.util.Map;

import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;

@Component
public class HttpFraudScreeningClient implements FraudScreeningClient {

    private final RestClient http;

    public HttpFraudScreeningClient(FraudProperties props) {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(props.timeout());
        factory.setReadTimeout(props.timeout());
        this.http = RestClient.builder().baseUrl(props.url()).requestFactory(factory).build();
    }

    @Override
    @SuppressWarnings("unchecked")
    public Decision screen(ScreeningRequest request) {
        try {
            Map<String, Object> body = http.post().uri("/screen").body(request).retrieve().body(Map.class);
            return Decision.valueOf(String.valueOf(body.get("decision")));
        } catch (RestClientException e) {
            throw new FraudScreeningUnavailableException("Fraud screening unavailable", e);
        }
    }
}
