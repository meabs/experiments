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

/** Hidden acceptance test for task CUSTDUP: a second customer with the same email gets 409 and is not created. */
public class HiddenDuplicateCustomerTest extends ServicesTestSupport {

	private Map<String, Object> customer(String email) {
		Map<String, Object> b = new HashMap<>();
		b.put("firstName", "Dup");
		b.put("lastName", "Test");
		b.put("address", "1 Main Street");
		b.put("city", "Montreal");
		b.put("postalCode", "H1H1H1");
		b.put("stateProvince", "QC");
		b.put("country", "CA");
		Map<String, Object> c = new HashMap<>();
		c.put("emailAddress", email);
		c.put("password", "clear123");
		c.put("gender", "F");
		c.put("language", "en");
		c.put("storeCode", "DEFAULT");
		c.put("billing", b);
		return c;
	}

	private HttpStatus register(String email) {
		return testRestTemplate.exchange("/api/v1/customer/register", HttpMethod.POST, new HttpEntity<>(customer(email), getHeader()),
				String.class).getStatusCode();
	}

	private HttpStatus adminCreate(String email) {
		return testRestTemplate.exchange("/api/v1/private/customer", HttpMethod.POST, new HttpEntity<>(customer(email), getHeader()),
				String.class).getStatusCode();
	}

	@SuppressWarnings({ "rawtypes", "unchecked" })
	private long countWithEmail(String email) {
		ResponseEntity<Map> r = testRestTemplate.exchange("/api/v1/private/customers?count=500", HttpMethod.GET,
				new HttpEntity<>(getHeader()), Map.class);
		return ((List<Map>) r.getBody().get("customers")).stream().filter(c -> email.equals(c.get("emailAddress"))).count();
	}

	@Test
	public void registeringTheSameEmailTwiceIsAConflict() {
		assertTrue(register("hdup1@test.com").is2xxSuccessful());
		assertEquals(HttpStatus.CONFLICT, register("hdup1@test.com"));
		assertEquals(1, countWithEmail("hdup1@test.com"));
	}

	@Test
	public void adminCreatingTheSameEmailTwiceIsAConflict() {
		assertTrue(adminCreate("hdup2@test.com").is2xxSuccessful());
		assertEquals(HttpStatus.CONFLICT, adminCreate("hdup2@test.com"));
		assertEquals(1, countWithEmail("hdup2@test.com"));
	}

	@Test
	public void registeringAnEmailCreatedByAnAdminIsAConflict() {
		assertTrue(adminCreate("hdup3@test.com").is2xxSuccessful());
		assertEquals(HttpStatus.CONFLICT, register("hdup3@test.com"));
		assertEquals(1, countWithEmail("hdup3@test.com"));
	}

	@Test
	public void differentEmailsAreBothCreated() {
		assertTrue(register("hdup4a@test.com").is2xxSuccessful());
		assertTrue(register("hdup4b@test.com").is2xxSuccessful());
	}
}
