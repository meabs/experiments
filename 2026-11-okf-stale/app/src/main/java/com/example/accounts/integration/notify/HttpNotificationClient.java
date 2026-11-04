package com.example.accounts.integration.notify;

import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

@Component
public class HttpNotificationClient implements NotificationClient {

    private final RestClient http;

    public HttpNotificationClient(NotificationProperties props) {
        this.http = RestClient.builder().baseUrl(props.url()).build();
    }

    @Override
    public void send(Notification notification) {
        http.post().uri("/messages").body(notification).retrieve().toBodilessEntity();
    }
}
