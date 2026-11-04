package com.example.accounts.security;

import java.util.Set;
import java.util.stream.Collectors;

import org.springframework.security.authentication.AuthenticationCredentialsNotFoundException;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.oauth2.server.resource.authentication.JwtAuthenticationToken;
import org.springframework.stereotype.Component;

/** Reads the caller from the security context. */
@Component
public class CurrentUserProvider {

    public CurrentUser current() {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        if (!(auth instanceof JwtAuthenticationToken token)) {
            throw new AuthenticationCredentialsNotFoundException("No bearer token");
        }
        Set<String> authorities = token.getAuthorities().stream().map(GrantedAuthority::getAuthority).collect(Collectors.toSet());
        return new CurrentUser(
            token.getToken().getSubject(),
            token.getToken().getClaimAsString("tenant"),
            strip(authorities, "ROLE_"),
            strip(authorities, "SCOPE_"));
    }

    private static Set<String> strip(Set<String> authorities, String prefix) {
        return authorities.stream().filter(a -> a.startsWith(prefix)).map(a -> a.substring(prefix.length())).collect(Collectors.toSet());
    }
}
