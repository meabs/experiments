package com.salesmanager.test.shop.hidden;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeSet;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import com.salesmanager.test.shop.common.ServicesTestSupport;

/** Hidden acceptance test for task CUSTSEARCH: the admin customer list filters by email, name and country. */
public class HiddenCustomerSearchTest extends ServicesTestSupport {

	private static boolean created = false;

	private void create(String email, String first, String last, String country) {
		Map<String, Object> b = new HashMap<>();
		b.put("firstName", first);
		b.put("lastName", last);
		b.put("address", "1 Main Street");
		b.put("city", "Somewhere");
		b.put("postalCode", "12345");
		b.put("country", country);
		Map<String, Object> c = new HashMap<>();
		c.put("emailAddress", email);
		c.put("password", "clear123");
		c.put("gender", "F");
		c.put("language", "en");
		c.put("storeCode", "DEFAULT");
		c.put("billing", b);
		assertTrue(testRestTemplate.exchange("/api/v1/private/customer", HttpMethod.POST, new HttpEntity<>(c, getHeader()), String.class)
				.getStatusCode().is2xxSuccessful());
	}

	@BeforeEach
	public void customers() {
		if (!created) {
			create("zelda.quorn@hcs.test", "Zelda", "Quorn", "CA");
			create("yorick@hcs.test", "Yorick", "Bramble", "US");
			create("zelma.b@hcs.test", "Zelma", "Brambleton", "CA");
			created = true;
		}
	}

	@SuppressWarnings({ "rawtypes", "unchecked" })
	private Set<String> find(String query) {
		ResponseEntity<Map> r = testRestTemplate.exchange("/api/v1/private/customers?count=500&" + query, HttpMethod.GET,
				new HttpEntity<>(getHeader()), Map.class);
		assertEquals(HttpStatus.OK, r.getStatusCode());
		Set<String> out = new TreeSet<>();
		for (Map c : (List<Map>) r.getBody().get("customers")) {
			out.add((String) c.get("emailAddress"));
		}
		return out;
	}

	private Set<String> set(String... v) {
		Set<String> s = new TreeSet<>();
		for (String x : v) s.add(x);
		return s;
	}

	@Test
	public void emailFilterMatchesPartOfTheAddressIgnoringCase() {
		assertEquals(set("zelda.quorn@hcs.test", "zelma.b@hcs.test"), find("email=ZEL"));
	}

	@Test
	public void nameFilterMatchesFirstOrLastNameIgnoringCase() {
		assertEquals(set("yorick@hcs.test", "zelma.b@hcs.test"), find("name=bramble"));
		assertEquals(set("zelda.quorn@hcs.test"), find("name=QUORN"));
	}

	@Test
	public void countryFilterMatchesBillingCountry() {
		Set<String> us = find("country=US");
		assertTrue(us.contains("yorick@hcs.test"));
		assertTrue(!us.contains("zelda.quorn@hcs.test") && !us.contains("zelma.b@hcs.test"));
	}

	@Test
	public void filtersCombine() {
		assertEquals(set("zelma.b@hcs.test"), find("name=bramble&country=CA"));
		assertEquals(set("zelma.b@hcs.test"), find("name=bramble&email=zel"));
		assertEquals(set(), find("name=quorn&country=US"));
		assertEquals(set(), find("name=zel&country=US"));
		assertEquals(set(), find("name=zel&email=yorick"));
	}
}
