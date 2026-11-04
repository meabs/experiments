package com.example.accounts.integration.scheme;

import java.util.Map;
import java.util.Optional;

import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.HttpClientErrorException.NotFound;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestClient;

@Component
public class HttpSchemeClient implements SchemeClient {

    private final RestClient http;

    public HttpSchemeClient(SchemeProperties props) {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(props.timeout());
        factory.setReadTimeout(props.timeout());
        this.http = RestClient.builder().baseUrl(props.url()).requestFactory(factory).build();
    }

    @Override
    @SuppressWarnings("unchecked")
    public SchemeReceipt submit(SchemePayment payment) {
        try {
            Map<String, Object> body = http.post().uri("/v2/instructions").body(payment).retrieve().body(Map.class);
            return new SchemeReceipt((String) body.get("instructionId"));
        } catch (HttpClientErrorException e) {
            Map<String, Object> err = e.getResponseBodyAs(Map.class);
            String code = err == null ? "UNKNOWN" : String.valueOf(err.get("reasonCode"));
            throw new SchemeRejectedException(code, e.getMessage());
        } catch (ResourceAccessException e) {
            throw new SchemeTimeoutException("Scheme gateway did not answer", e);
        }
    }

    @Override
    @SuppressWarnings("unchecked")
    public Optional<SchemeReceipt> find(String reference) {
        try {
            Map<String, Object> body = http.get().uri("/v2/instructions/{reference}", reference).retrieve().body(Map.class);
            return Optional.of(new SchemeReceipt((String) body.get("instructionId")));
        } catch (NotFound e) {
            return Optional.empty();
        } catch (ResourceAccessException e) {
            throw new SchemeTimeoutException("Scheme gateway did not answer", e);
        }
    }
}
