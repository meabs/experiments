package com.salesmanager.test.shop.hidden;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.junit.jupiter.api.MethodOrderer;
import org.junit.jupiter.api.Order;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestMethodOrder;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import com.salesmanager.shop.store.security.AuthenticationRequest;
import com.salesmanager.test.shop.common.ServicesTestSupport;

/**
 * Hidden acceptance test for task SUPERDEL: the super administrator cannot be deleted, a missing user is 404, and
 * deleting other users keeps working. The super administrator test runs last, so that if it deletes the account it
 * cannot break the other checks.
 */
@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
public class HiddenSuperadminDeleteTest extends ServicesTestSupport {

	@SuppressWarnings("rawtypes")
	private Long createUser(String email) {
		Map<String, Object> g = new HashMap<>();
		g.put("name", "ADMIN");
		Map<String, Object> u = new HashMap<>();
		u.put("defaultLanguage", "en");
		u.put("emailAddress", email);
		u.put("userName", email);
		u.put("firstName", "Ord");
		u.put("lastName", "Inary");
		u.put("password", "Passw0rd!x");
		u.put("repeatPassword", "Passw0rd!x");
		u.put("groups", List.of(g));
		ResponseEntity<Map> r = testRestTemplate.exchange("/api/v1/private/user/", HttpMethod.POST, new HttpEntity<>(u, getHeader()), Map.class);
		assertTrue(r.getStatusCode().is2xxSuccessful(), "create user: " + r.getStatusCode());
		return ((Number) r.getBody().get("id")).longValue();
	}

	private HttpStatus delete(Long id) {
		return testRestTemplate.exchange("/api/v1/private/user/" + id, HttpMethod.DELETE, new HttpEntity<>(getHeader()), String.class)
				.getStatusCode();
	}

	@Test
	@Order(1)
	public void keepsDeletingOrdinaryUsers() {
		Long id = createUser("ordinary1@test.com");
		assertTrue(delete(id).is2xxSuccessful(), "deleting an ordinary user");
		assertEquals(HttpStatus.NOT_FOUND, testRestTemplate.exchange("/api/v1/private/users/" + id, HttpMethod.GET,
				new HttpEntity<>(getHeader()), String.class).getStatusCode(), "deleted user should be gone");
	}

	@Test
	@Order(2)
	public void missingUserIsNotFound() {
		assertEquals(HttpStatus.NOT_FOUND, delete(987654L));
	}

	@Test
	@Order(3)
	public void superadminCannotBeDeleted() {
		assertEquals(HttpStatus.BAD_REQUEST, delete(1L));
		ResponseEntity<String> login = testRestTemplate.postForEntity("/api/v1/private/login",
				new HttpEntity<>(new AuthenticationRequest("admin@shopizer.com", "password")), String.class);
		assertEquals(HttpStatus.OK, login.getStatusCode(), "the super administrator must still be able to log in");
	}
}
