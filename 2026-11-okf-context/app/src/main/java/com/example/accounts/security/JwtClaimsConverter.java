package com.example.accounts.security;

import java.util.ArrayList;
import java.util.Collection;
import java.util.List;

import org.springframework.core.convert.converter.Converter;
import org.springframework.security.authentication.AbstractAuthenticationToken;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.security.oauth2.server.resource.authentication.JwtAuthenticationToken;
import org.springframework.security.oauth2.server.resource.authentication.JwtGrantedAuthoritiesConverter;
import org.springframework.stereotype.Component;

/**
 * Turns the identity service's token into authorities. Claims used:
 * <ul>
 *   <li>{@code sub}: the user id, e.g. {@code u-alice}</li>
 *   <li>{@code tenant}: the tenant (bank) the user belongs to, e.g. {@code acme}</li>
 *   <li>{@code roles}: e.g. {@code ["CUSTOMER"]}, {@code ["SUPPORT", "APPROVER"]}, mapped to {@code ROLE_*}</li>
 *   <li>{@code scope}: OAuth scopes granted to the client, space separated, mapped to {@code SCOPE_*}</li>
 * </ul>
 */
@Component
public class JwtClaimsConverter implements Converter<Jwt, AbstractAuthenticationToken> {

    private final JwtGrantedAuthoritiesConverter scopes = new JwtGrantedAuthoritiesConverter();

    @Override
    public AbstractAuthenticationToken convert(Jwt jwt) {
        Collection<GrantedAuthority> authorities = new ArrayList<>(scopes.convert(jwt));
        List<String> roles = jwt.getClaimAsStringList("roles");
        if (roles != null) {
            roles.forEach(r -> authorities.add(new SimpleGrantedAuthority("ROLE_" + r)));
        }
        return new JwtAuthenticationToken(jwt, authorities, jwt.getSubject());
    }
}
