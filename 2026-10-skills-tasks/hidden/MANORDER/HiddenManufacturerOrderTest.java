package com.salesmanager.test.shop.hidden;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import org.junit.jupiter.api.Test;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import com.salesmanager.shop.model.catalog.manufacturer.PersistableManufacturer;
import com.salesmanager.test.shop.common.ServicesTestSupport;

/** Hidden acceptance test for task MANORDER: manufacturer display order is stored and the list is sorted by it. */
public class HiddenManufacturerOrderTest extends ServicesTestSupport {

	@SuppressWarnings("rawtypes")
	private Object create(String code, int order) {
		PersistableManufacturer m = manufacturer(code);
		m.setOrder(order);
		ResponseEntity<Map> r = testRestTemplate.exchange("/api/v1/private/manufacturer", HttpMethod.POST, new HttpEntity<>(m, getHeader()), Map.class);
		assertTrue(r.getStatusCode().is2xxSuccessful(), "create " + code + ": " + r.getStatusCode());
		return r.getBody().get("id");
	}

	@SuppressWarnings({ "rawtypes", "unchecked" })
	private List<String> listedCodes(String prefix) {
		ResponseEntity<Map> r = testRestTemplate.exchange("/api/v1/manufacturers?count=200", HttpMethod.GET, new HttpEntity<>(getHeader()), Map.class);
		assertEquals(HttpStatus.OK, r.getStatusCode());
		List<String> codes = new ArrayList<>();
		for (Map m : (List<Map>) r.getBody().get("manufacturers")) {
			String c = (String) m.get("code");
			if (c.startsWith(prefix)) codes.add(c);
		}
		return codes;
	}

	@SuppressWarnings("rawtypes")
	@Test
	public void orderIsStoredAndReturned() {
		Object id = create("hmsingle", 7);
		ResponseEntity<Map> r = testRestTemplate.exchange("/api/v1/manufacturer/" + id, HttpMethod.GET, new HttpEntity<>(getHeader()), Map.class);
		assertEquals(HttpStatus.OK, r.getStatusCode());
		assertEquals(7, ((Number) r.getBody().get("order")).intValue());
	}

	@Test
	public void listIsSortedByOrderThenCode() {
		create("hmordc", 30);
		create("hmorda", 10);
		create("hmordb", 20);
		create("hmordd", 20);
		List<String> expected = new ArrayList<>();
		expected.add("hmorda");
		expected.add("hmordb");
		expected.add("hmordd");
		expected.add("hmordc");
		assertEquals(expected, listedCodes("hmord"));
	}

	@Test
	public void updatingOrderMovesTheManufacturer() {
		Object id = create("hmupdx", 50);
		create("hmupdy", 60);
		PersistableManufacturer m = manufacturer("hmupdx");
		m.setOrder(70);
		ResponseEntity<String> u = testRestTemplate.exchange("/api/v1/private/manufacturer/" + id, HttpMethod.PUT, new HttpEntity<>(m, getHeader()), String.class);
		assertTrue(u.getStatusCode().is2xxSuccessful(), "update: " + u.getStatusCode());
		List<String> expected = new ArrayList<>();
		expected.add("hmupdy");
		expected.add("hmupdx");
		assertEquals(expected, listedCodes("hmupd"));
	}
}
