package com.salesmanager.test.shop.hidden;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.HashMap;
import java.util.Map;

import org.junit.jupiter.api.Test;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import com.salesmanager.shop.store.security.AuthenticationRequest;
import com.salesmanager.test.shop.common.ServicesTestSupport;

/** Hidden acceptance test for task CUSTLOGIN: admin updates set the customer's login, and other logins keep working. */
public class HiddenCustomerLoginTest extends ServicesTestSupport {

	private Map<String, Object> customer(String email, String password, String firstName) {
		Map<String, Object> b = new HashMap<>();
		b.put("firstName", firstName);
		b.put("lastName", "Login");
		b.put("address", "1 Main Street");
		b.put("city", "Montreal");
		b.put("postalCode", "H1H1H1");
		b.put("stateProvince", "QC");
		b.put("country", "CA");
		Map<String, Object> c = new HashMap<>();
		c.put("emailAddress", email);
		if (password != null) {
			c.put("password", password);
		}
		c.put("gender", "F");
		c.put("language", "en");
		c.put("storeCode", "DEFAULT");
		c.put("billing", b);
		return c;
	}

	@SuppressWarnings("rawtypes")
	private Long create(String email) {
		ResponseEntity<Map> r = testRestTemplate.exchange("/api/v1/private/customer", HttpMethod.POST,
				new HttpEntity<>(customer(email, "clear123", "Cara"), getHeader()), Map.class);
		assertTrue(r.getStatusCode().is2xxSuccessful(), "create: " + r.getStatusCode());
		return ((Number) r.getBody().get("id")).longValue();
	}

	private void update(Long id, Map<String, Object> body) {
		ResponseEntity<String> r = testRestTemplate.exchange("/api/v1/private/customer/" + id, HttpMethod.PUT,
				new HttpEntity<>(body, getHeader()), String.class);
		assertTrue(r.getStatusCode().is2xxSuccessful(), "update: " + r.getStatusCode());
	}

	private HttpStatus login(String user, String password) {
		return testRestTemplate.postForEntity("/api/v1/customer/login", new HttpEntity<>(new AuthenticationRequest(user, password)),
				String.class).getStatusCode();
	}

	@Test
	public void passwordSetByAdminIsTheNewLogin() {
		Long id = create("clpw@test.com");
		update(id, customer("clpw@test.com", "newpass9", "Cara"));
		assertEquals(HttpStatus.OK, login("clpw@test.com", "newpass9"), "new password");
		assertEquals(HttpStatus.UNAUTHORIZED, login("clpw@test.com", "clear123"), "old password");
	}

	@Test
	public void emailChangedByAdminIsTheNewLogin() {
		Long id = create("clmail@test.com");
		update(id, customer("clmail2@test.com", null, "Cara"));
		assertEquals(HttpStatus.OK, login("clmail2@test.com", "clear123"), "new email");
		assertEquals(HttpStatus.UNAUTHORIZED, login("clmail@test.com", "clear123"), "old email");
	}

	@Test
	public void keepsLoginAfterOtherUpdates() {
		Long id = create("clsame@test.com");
		update(id, customer("clsame@test.com", null, "Renamed"));
		assertEquals(HttpStatus.OK, login("clsame@test.com", "clear123"));
	}

	@Test
	public void keepsRegisteredCustomersLoggingIn() {
		ResponseEntity<String> r = testRestTemplate.postForEntity("/api/v1/customer/register",
				new HttpEntity<>(customer("clreg@test.com", "clear123", "Reg"), getHeader()), String.class);
		assertTrue(r.getStatusCode().is2xxSuccessful(), "register: " + r.getStatusCode());
		assertEquals(HttpStatus.OK, login("clreg@test.com", "clear123"));
	}
}
