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

import com.salesmanager.shop.model.catalog.product.product.PersistableProduct;
import com.salesmanager.shop.model.entity.Entity;
import com.salesmanager.test.shop.common.ServicesTestSupport;

/** Hidden acceptance test for task REVIEW: review ratings 1 to 5, one review per customer and product, correct codes. */
public class HiddenProductReviewTest extends ServicesTestSupport {

	@SuppressWarnings("rawtypes")
	private Long customer(String email) {
		Map<String, Object> b = new HashMap<>();
		b.put("firstName", "Rev");
		b.put("lastName", "Iewer");
		b.put("address", "1 Main Street");
		b.put("city", "Montreal");
		b.put("postalCode", "H1H1H1");
		b.put("country", "CA");
		Map<String, Object> c = new HashMap<>();
		c.put("emailAddress", email);
		c.put("password", "clear123");
		c.put("gender", "F");
		c.put("language", "en");
		c.put("storeCode", "DEFAULT");
		c.put("billing", b);
		ResponseEntity<Map> r = testRestTemplate.exchange("/api/v1/private/customer", HttpMethod.POST, new HttpEntity<>(c, getHeader()), Map.class);
		assertTrue(r.getStatusCode().is2xxSuccessful());
		return ((Number) r.getBody().get("id")).longValue();
	}

	private Long product(String sku, boolean unused) {
		PersistableProduct p = product(sku);
		p.setSku(sku);
		ResponseEntity<Entity> r = testRestTemplate.postForEntity("/api/v1/private/product?store=DEFAULT", new HttpEntity<>(p, getHeader()), Entity.class);
		assertEquals(HttpStatus.CREATED, r.getStatusCode());
		return r.getBody().getId();
	}

	private HttpStatus review(Long product, Long customer, Double rating) {
		Map<String, Object> rv = new HashMap<>();
		rv.put("customerId", customer);
		rv.put("productId", product);
		rv.put("rating", rating);
		rv.put("description", "review");
		rv.put("language", "en");
		rv.put("date", "2026-10-01");
		return testRestTemplate.exchange("/api/v1/private/products/" + product + "/reviews", HttpMethod.POST, new HttpEntity<>(rv, getHeader()),
				String.class).getStatusCode();
	}

	@SuppressWarnings("rawtypes")
	private int reviewCount(Long product) {
		ResponseEntity<List> r = testRestTemplate.exchange("/api/v1/product/" + product + "/reviews", HttpMethod.GET, new HttpEntity<>(getHeader()), List.class);
		assertEquals(HttpStatus.OK, r.getStatusCode());
		return r.getBody().size();
	}

	@Test
	public void ratingsFromOneToFiveAreAccepted() {
		Long p = product("hrevok", true);
		assertEquals(HttpStatus.CREATED, review(p, customer("hrev1@test.com"), 1.0));
		assertEquals(HttpStatus.CREATED, review(p, customer("hrev2@test.com"), 5.0));
		assertEquals(2, reviewCount(p));
	}

	@Test
	public void ratingAboveFiveIsABadRequest() {
		Long p = product("hrevhigh", true);
		assertEquals(HttpStatus.BAD_REQUEST, review(p, customer("hrev3@test.com"), 6.0));
		assertEquals(0, reviewCount(p));
	}

	@Test
	public void ratingBelowOneIsABadRequest() {
		Long p = product("hrevlow", true);
		assertEquals(HttpStatus.BAD_REQUEST, review(p, customer("hrev4@test.com"), 0.0));
		assertEquals(HttpStatus.BAD_REQUEST, review(p, customer("hrev5@test.com"), -2.0));
		assertEquals(0, reviewCount(p));
	}

	@Test
	public void secondReviewBySameCustomerIsAConflict() {
		Long p = product("hrevdup", true);
		Long c = customer("hrev6@test.com");
		assertEquals(HttpStatus.CREATED, review(p, c, 4.0));
		assertEquals(HttpStatus.CONFLICT, review(p, c, 2.0));
		assertEquals(1, reviewCount(p));
	}
}
