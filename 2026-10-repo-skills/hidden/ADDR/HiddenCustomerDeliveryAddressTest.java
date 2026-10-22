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

import com.salesmanager.test.shop.common.ServicesTestSupport;

/** Hidden acceptance test for task ADDR: PATCHing a customer's delivery address stores every field correctly. */
public class HiddenCustomerDeliveryAddressTest extends ServicesTestSupport {

	private Map<String, Object> billing() {
		Map<String, Object> b = new HashMap<>();
		b.put("firstName", "Ann");
		b.put("lastName", "Lee");
		b.put("address", "1 Main Street");
		b.put("city", "Montreal");
		b.put("postalCode", "H1H1H1");
		b.put("stateProvince", "QC");
		b.put("country", "CA");
		return b;
	}

	@SuppressWarnings("rawtypes")
	private Object createCustomer(String email) {
		Map<String, Object> c = new HashMap<>();
		c.put("emailAddress", email);
		c.put("password", "clear123");
		c.put("gender", "F");
		c.put("language", "en");
		c.put("storeCode", "DEFAULT");
		c.put("billing", billing());
		ResponseEntity<Map> r = testRestTemplate.exchange("/api/v1/private/customer", HttpMethod.POST, new HttpEntity<>(c, getHeader()), Map.class);
		assertTrue(r.getStatusCode().is2xxSuccessful(), "create customer: " + r.getStatusCode());
		return r.getBody().get("id");
	}

	@SuppressWarnings({ "rawtypes", "unchecked" })
	private Map<String, Object> patchAndReadDelivery(Object id, Map<String, Object> delivery) {
		Map<String, Object> body = new HashMap<>();
		body.put("billing", billing());
		body.put("delivery", delivery);
		ResponseEntity<String> p = testRestTemplate.exchange("/api/v1/private/customer/" + id + "/address", HttpMethod.PATCH,
				new HttpEntity<>(body, getHeader()), String.class);
		assertTrue(p.getStatusCode().is2xxSuccessful(), "patch: " + p.getStatusCode() + " " + p.getBody());
		ResponseEntity<Map> g = testRestTemplate.exchange("/api/v1/private/customer/" + id, HttpMethod.GET, new HttpEntity<>(getHeader()), Map.class);
		assertEquals(HttpStatus.OK, g.getStatusCode());
		return (Map<String, Object>) g.getBody().get("delivery");
	}

	@Test
	public void fullDeliveryAddressIsStoredAsSent() {
		Object id = createCustomer("haddr1@test.com");
		Map<String, Object> d = new HashMap<>();
		d.put("firstName", "Bob");
		d.put("lastName", "Ray");
		d.put("address", "9 Elm Street");
		d.put("city", "New York");
		d.put("postalCode", "10001");
		d.put("stateProvince", "NY");
		d.put("country", "US");
		Map<String, Object> got = patchAndReadDelivery(id, d);
		assertEquals("9 Elm Street", got.get("address"));
		assertEquals("New York", got.get("city"));
		assertEquals("10001", got.get("postalCode"));
		assertEquals("NY", got.get("stateProvince"));
		assertEquals("US", got.get("country"));
	}

	@Test
	public void missingDeliveryFieldsFallBackToBilling() {
		Object id = createCustomer("haddr2@test.com");
		Map<String, Object> d = new HashMap<>();
		d.put("firstName", "Bob");
		d.put("lastName", "Ray");
		d.put("address", "22 Oak Avenue");
		Map<String, Object> got = patchAndReadDelivery(id, d);
		assertEquals("22 Oak Avenue", got.get("address"));
		assertEquals("Montreal", got.get("city"));
		assertEquals("H1H1H1", got.get("postalCode"));
		assertEquals("CA", got.get("country"));
	}
}
