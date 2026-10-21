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

import com.salesmanager.shop.store.security.AuthenticationRequest;
import com.salesmanager.test.shop.common.ServicesTestSupport;

/** Hidden acceptance test for task USERERR: user-management mistakes get the right client error; normal use keeps working. */
public class HiddenUserErrorsTest extends ServicesTestSupport {

	private Map<String, Object> user(String userName) {
		Map<String, Object> g = new HashMap<>();
		g.put("name", "ADMIN");
		Map<String, Object> u = new HashMap<>();
		u.put("defaultLanguage", "en");
		u.put("emailAddress", userName);
		u.put("userName", userName);
		u.put("firstName", "Err");
		u.put("lastName", "Ors");
		u.put("password", "Passw0rd!x");
		u.put("repeatPassword", "Passw0rd!x");
		u.put("groups", List.of(g));
		return u;
	}

	@SuppressWarnings("rawtypes")
	private ResponseEntity<Map> create(String userName) {
		return testRestTemplate.exchange("/api/v1/private/user/", HttpMethod.POST, new HttpEntity<>(user(userName), getHeader()), Map.class);
	}

	private HttpStatus changePassword(Object id, String current, String next) {
		Map<String, Object> p = new HashMap<>();
		p.put("password", current);
		p.put("changePassword", next);
		return testRestTemplate.exchange("/api/v1/private/user/" + id + "/password", HttpMethod.PATCH, new HttpEntity<>(p, getHeader()),
				String.class).getStatusCode();
	}

	private HttpStatus login(String user, String password) {
		return testRestTemplate.postForEntity("/api/v1/private/login", new HttpEntity<>(new AuthenticationRequest(user, password)), String.class)
				.getStatusCode();
	}

	@Test
	public void duplicateUserNameIsConflict() {
		assertTrue(create("uedup@test.com").getStatusCode().is2xxSuccessful());
		assertEquals(HttpStatus.CONFLICT, create("uedup@test.com").getStatusCode());
	}

	@Test
	public void missingUserIsNotFoundOnUpdateAndPasswordChange() {
		assertEquals(HttpStatus.NOT_FOUND, testRestTemplate.exchange("/api/v1/private/user/987654", HttpMethod.PUT,
				new HttpEntity<>(user("uemiss@test.com"), getHeader()), String.class).getStatusCode());
		assertEquals(HttpStatus.NOT_FOUND, changePassword(987654, "Passw0rd!x", "Newpass9"));
	}

	@SuppressWarnings("rawtypes")
	@Test
	public void wrongCurrentPasswordIsBadRequest() {
		ResponseEntity<Map> r = create("uewrong@test.com");
		assertTrue(r.getStatusCode().is2xxSuccessful());
		assertEquals(HttpStatus.BAD_REQUEST, changePassword(r.getBody().get("id"), "notmypassword", "Newpass9"));
		assertEquals(HttpStatus.OK, login("uewrong@test.com", "Passw0rd!x"), "password must be unchanged");
	}

	@SuppressWarnings("rawtypes")
	@Test
	public void keepsChangingPasswordWithTheRightCurrentPassword() {
		ResponseEntity<Map> r = create("ueright@test.com");
		assertTrue(r.getStatusCode().is2xxSuccessful());
		assertEquals(HttpStatus.OK, changePassword(r.getBody().get("id"), "Passw0rd!x", "Newpass9"));
		assertEquals(HttpStatus.OK, login("ueright@test.com", "Newpass9"));
	}

	@Test
	public void keepsOtherNotFoundAnswers() {
		Map<String, Object> e = new HashMap<>();
		e.put("id", 987654);
		e.put("active", true);
		assertEquals(HttpStatus.NOT_FOUND, testRestTemplate.exchange("/api/v1/private/user/987654/enabled", HttpMethod.PATCH,
				new HttpEntity<>(e, getHeader()), String.class).getStatusCode());
		assertEquals(HttpStatus.NOT_FOUND, testRestTemplate.exchange("/api/v1/private/users/987654", HttpMethod.GET,
				new HttpEntity<>(getHeader()), String.class).getStatusCode());
	}
}
