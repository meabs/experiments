package com.example.accounts.support;

import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.security.KeyFactory;
import java.security.interfaces.RSAPrivateKey;
import java.security.spec.PKCS8EncodedKeySpec;
import java.time.Instant;
import java.util.Arrays;
import java.util.Base64;
import java.util.Date;
import java.util.List;

import com.nimbusds.jose.JOSEException;
import com.nimbusds.jose.JWSAlgorithm;
import com.nimbusds.jose.JWSHeader;
import com.nimbusds.jose.crypto.RSASSASigner;
import com.nimbusds.jwt.JWTClaimsSet;
import com.nimbusds.jwt.SignedJWT;

/**
 * Signs real bearer tokens with the dev key (src/test/resources/keys/private.pem), so tests go through the application's
 * full security chain: token decoding, claim conversion, URL rules and method security.
 *
 * <pre>
 *   TestTokens.of(TestUsers.ALICE).bearer()                                  // Alice's usual token
 *   TestTokens.of(TestUsers.ALICE).scopes("accounts:read").bearer()          // fewer scopes
 *   TestTokens.user("u-x").tenant("acme").roles("SUPPORT").bearer()          // any claims
 * </pre>
 */
public final class TestTokens {

    private static final RSAPrivateKey KEY = loadKey();

    private String subject;
    private String tenant;
    private List<String> roles = List.of();
    private String scope = "";
    private Instant expires = Instant.now().plusSeconds(3600);

    private TestTokens() {
    }

    public static TestTokens user(String subject) {
        TestTokens t = new TestTokens();
        t.subject = subject;
        return t;
    }

    public static TestTokens of(TestUsers.User u) {
        return user(u.id()).tenant(u.tenant()).roles(u.roles()).scopes(u.scopes());
    }

    public TestTokens tenant(String tenant) {
        this.tenant = tenant;
        return this;
    }

    public TestTokens roles(String... roles) {
        this.roles = Arrays.asList(roles);
        return this;
    }

    public TestTokens roles(List<String> roles) {
        this.roles = roles;
        return this;
    }

    /** Space-separated OAuth scopes, e.g. "accounts:read transactions:read". */
    public TestTokens scopes(String scope) {
        this.scope = scope;
        return this;
    }

    public TestTokens expiredAt(Instant when) {
        this.expires = when;
        return this;
    }

    /** The token. */
    public String token() {
        JWTClaimsSet.Builder claims = new JWTClaimsSet.Builder()
            .subject(subject)
            .issueTime(Date.from(Instant.now().minusSeconds(60)))
            .expirationTime(Date.from(expires))
            .claim("roles", roles);
        if (tenant != null) {
            claims.claim("tenant", tenant);
        }
        if (!scope.isBlank()) {
            claims.claim("scope", scope);
        }
        try {
            SignedJWT jwt = new SignedJWT(new JWSHeader(JWSAlgorithm.RS256), claims.build());
            jwt.sign(new RSASSASigner(KEY));
            return jwt.serialize();
        } catch (JOSEException e) {
            throw new IllegalStateException(e);
        }
    }

    /** The value for an Authorization header. */
    public String bearer() {
        return "Bearer " + token();
    }

    private static RSAPrivateKey loadKey() {
        try (InputStream in = TestTokens.class.getResourceAsStream("/keys/private.pem")) {
            String pem = new String(in.readAllBytes(), StandardCharsets.US_ASCII)
                .replaceAll("-----[A-Z ]+-----", "").replaceAll("\\s", "");
            return (RSAPrivateKey) KeyFactory.getInstance("RSA")
                .generatePrivate(new PKCS8EncodedKeySpec(Base64.getDecoder().decode(pem)));
        } catch (IOException | java.security.GeneralSecurityException e) {
            throw new IllegalStateException("Cannot load the dev signing key", e);
        }
    }
}
