package com.salesmanager.test.shop.hidden;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.junit.jupiter.api.Test;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import com.salesmanager.test.shop.common.ServicesTestSupport;

/** Hidden acceptance test for task USERACTIVE: editing a user keeps the account enabled; creating and enabling users keep working. */
public class HiddenUserActiveTest extends ServicesTestSupport {

	private Map<String, Object> user(String userName, String firstName, Boolean active, boolean withPassword) {
		Map<String, Object> g = new HashMap<>();
		g.put("name", "ADMIN");
		Map<String, Object> u = new HashMap<>();
		u.put("defaultLanguage", "en");
		u.put("emailAddress", userName);
		u.put("userName", userName);
		u.put("firstName", firstName);
		u.put("lastName", "Active");
		if (withPassword) {
			u.put("password", "Passw0rd1");
			u.put("repeatPassword", "Passw0rd1");
		}
		if (active != null) {
			u.put("active", active);
		}
		u.put("groups", List.of(g));
		return u;
	}

	@SuppressWarnings("rawtypes")
	private Long create(Map<String, Object> body) {
		ResponseEntity<Map> r = testRestTemplate.exchange("/api/v1/private/user/", HttpMethod.POST, new HttpEntity<>(body, getHeader()), Map.class);
		assertTrue(r.getStatusCode().is2xxSuccessful(), "create: " + r.getStatusCode());
		return ((Number) r.getBody().get("id")).longValue();
	}

	private void enabled(Long id, boolean active) {
		Map<String, Object> e = new HashMap<>();
		e.put("id", id);
		e.put("active", active);
		assertTrue(testRestTemplate.exchange("/api/v1/private/user/" + id + "/enabled", HttpMethod.PATCH, new HttpEntity<>(e, getHeader()),
				String.class).getStatusCode().is2xxSuccessful());
	}

	@SuppressWarnings("rawtypes")
	private boolean active(Long id) {
		ResponseEntity<Map> r = testRestTemplate.exchange("/api/v1/private/users/" + id, HttpMethod.GET, new HttpEntity<>(getHeader()), Map.class);
		assertEquals(HttpStatus.OK, r.getStatusCode());
		return Boolean.TRUE.equals(r.getBody().get("active"));
	}

	private void edit(Long id, Map<String, Object> body) {
		assertTrue(testRestTemplate.exchange("/api/v1/private/user/" + id, HttpMethod.PUT, new HttpEntity<>(body, getHeader()), String.class)
				.getStatusCode().is2xxSuccessful());
	}

	@Test
	public void editingAnEnabledUserKeepsItEnabled() {
		Long id = create(user("uaedit@test.com", "Pat", null, true));
		enabled(id, true);
		edit(id, user("uaedit@test.com", "Patricia", null, false));
		assertTrue(active(id), "editing the name must not disable the account");
	}

	@Test
	public void editingADisabledUserKeepsItDisabled() {
		Long id = create(user("uaoff@test.com", "Sam", null, true));
		enabled(id, false);
		edit(id, user("uaoff@test.com", "Samuel", null, false));
		assertEquals(false, active(id));
	}

	@Test
	public void keepsCreatingEnabledUsers() {
		Long id = create(user("uanew@test.com", "Alex", true, true));
		assertTrue(active(id), "a user created with active: true is enabled");
	}

	@Test
	public void keepsEnablingAndDisablingUsers() {
		Long id = create(user("uatoggle@test.com", "Kim", null, true));
		enabled(id, true);
		assertTrue(active(id));
		enabled(id, false);
		assertEquals(false, active(id));
	}
}
