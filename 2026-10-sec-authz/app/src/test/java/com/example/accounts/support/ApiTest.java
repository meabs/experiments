package com.example.accounts.support;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.patch;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.put;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.ResultActions;
import org.springframework.transaction.annotation.Transactional;

/**
 * Base for API tests: the whole application with its real security chain, over MockMvc. Each test runs in a
 * transaction that is rolled back, so tests can change data without affecting each other.
 */
@SpringBootTest
@AutoConfigureMockMvc
@Transactional
public abstract class ApiTest {

    @Autowired
    protected MockMvc mvc;

    protected ResultActions getAs(TestUsers.User user, String url) throws Exception {
        return getWith(TestTokens.of(user), url);
    }

    protected ResultActions getWith(TestTokens token, String url) throws Exception {
        return mvc.perform(get(url).header(HttpHeaders.AUTHORIZATION, token.bearer()));
    }

    protected ResultActions getAnonymous(String url) throws Exception {
        return mvc.perform(get(url));
    }

    protected ResultActions postAs(TestUsers.User user, String url, String json) throws Exception {
        return postWith(TestTokens.of(user), url, json);
    }

    protected ResultActions postWith(TestTokens token, String url, String json) throws Exception {
        return mvc.perform(post(url).header(HttpHeaders.AUTHORIZATION, token.bearer())
            .contentType(MediaType.APPLICATION_JSON).content(json == null ? "" : json));
    }

    protected ResultActions putAs(TestUsers.User user, String url, String json) throws Exception {
        return putWith(TestTokens.of(user), url, json);
    }

    protected ResultActions putWith(TestTokens token, String url, String json) throws Exception {
        return mvc.perform(put(url).header(HttpHeaders.AUTHORIZATION, token.bearer())
            .contentType(MediaType.APPLICATION_JSON).content(json));
    }

    protected ResultActions patchAs(TestUsers.User user, String url, String json) throws Exception {
        return patchWith(TestTokens.of(user), url, json);
    }

    protected ResultActions patchWith(TestTokens token, String url, String json) throws Exception {
        return mvc.perform(patch(url).header(HttpHeaders.AUTHORIZATION, token.bearer())
            .contentType(MediaType.APPLICATION_JSON).content(json));
    }
}
