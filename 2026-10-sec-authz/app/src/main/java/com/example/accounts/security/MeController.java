package com.example.accounts.security;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

/** Who the API thinks the caller is. */
@RestController
public class MeController {

    private final CurrentUserProvider users;

    public MeController(CurrentUserProvider users) {
        this.users = users;
    }

    @GetMapping("/api/me")
    public CurrentUser me() {
        return users.current();
    }
}
