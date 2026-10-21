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

/** Hidden acceptance test for task OPTORDER: product options and option values keep their display order. */
public class HiddenOptionOrderTest extends ServicesTestSupport {

	private Map<String, Object> body(String code, String orderField, int order) {
		Map<String, Object> d = new HashMap<>();
		d.put("language", "en");
		d.put("name", code);
		Map<String, Object> o = new HashMap<>();
		o.put("code", code);
		o.put("type", "select");
		o.put(orderField, order);
		o.put("descriptions", List.of(d));
		return o;
	}

	@SuppressWarnings("rawtypes")
	private Long create(String path, Map<String, Object> body) {
		ResponseEntity<Map> r = testRestTemplate.exchange("/api/v1/private/product/" + path, HttpMethod.POST, new HttpEntity<>(body, getHeader()), Map.class);
		assertTrue(r.getStatusCode().is2xxSuccessful(), "create: " + r.getStatusCode());
		return ((Number) r.getBody().get("id")).longValue();
	}

	@SuppressWarnings("rawtypes")
	private int order(String path, Long id) {
		ResponseEntity<Map> r = testRestTemplate.exchange("/api/v1/private/product/" + path + "/" + id, HttpMethod.GET, new HttpEntity<>(getHeader()), Map.class);
		assertEquals(HttpStatus.OK, r.getStatusCode());
		return ((Number) r.getBody().get("order")).intValue();
	}

	private void update(String path, Long id, Map<String, Object> body) {
		assertTrue(testRestTemplate.exchange("/api/v1/private/product/" + path + "/" + id, HttpMethod.PUT, new HttpEntity<>(body, getHeader()),
				String.class).getStatusCode().is2xxSuccessful());
	}

	@Test
	public void optionOrderIsStoredAndReturned() {
		Long id = create("option", body("oocolour", "order", 4));
		assertEquals(4, order("option", id));
		update("option", id, body("oocolour", "order", 7));
		assertEquals(7, order("option", id));
	}

	@Test
	public void optionValueOrderIsStoredAndReturned() {
		Long id = create("option/value", body("oored", "order", 3));
		assertEquals(3, order("option/value", id));
		update("option/value", id, body("oored", "order", 9));
		assertEquals(9, order("option/value", id));
	}

	@Test
	public void keepsOptionValueSortOrderFromExistingClients() {
		Long id = create("option/value", body("oogreen", "sortOrder", 5));
		assertEquals(5, order("option/value", id));
	}
}
