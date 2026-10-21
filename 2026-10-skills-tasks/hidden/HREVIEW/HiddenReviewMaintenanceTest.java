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

/** Hidden acceptance test for task HREVIEW: reviews can be edited and deleted, and product ratings stay current. */
public class HiddenReviewMaintenanceTest extends ServicesTestSupport {

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

	private Long createProduct(String sku) {
		PersistableProduct p = product(sku);
		p.setSku(sku);
		ResponseEntity<Entity> r = testRestTemplate.postForEntity("/api/v1/private/product?store=DEFAULT", new HttpEntity<>(p, getHeader()), Entity.class);
		assertEquals(HttpStatus.CREATED, r.getStatusCode());
		return r.getBody().getId();
	}

	private Map<String, Object> body(Long product, Long customer, double rating) {
		Map<String, Object> rv = new HashMap<>();
		rv.put("customerId", customer);
		rv.put("productId", product);
		rv.put("rating", rating);
		rv.put("description", "review " + rating);
		rv.put("language", "en");
		rv.put("date", "2026-10-01");
		return rv;
	}

	@SuppressWarnings("rawtypes")
	private Long review(Long product, Long customer, double rating) {
		ResponseEntity<Map> r = testRestTemplate.exchange("/api/v1/private/products/" + product + "/reviews", HttpMethod.POST,
				new HttpEntity<>(body(product, customer, rating), getHeader()), Map.class);
		assertEquals(HttpStatus.CREATED, r.getStatusCode());
		return ((Number) r.getBody().get("id")).longValue();
	}

	@SuppressWarnings("rawtypes")
	private List reviews(Long product) {
		ResponseEntity<List> r = testRestTemplate.exchange("/api/v1/product/" + product + "/reviews", HttpMethod.GET, new HttpEntity<>(getHeader()), List.class);
		assertEquals(HttpStatus.OK, r.getStatusCode());
		return r.getBody();
	}

	@SuppressWarnings("rawtypes")
	private void assertRating(String sku, double rating, int count) {
		ResponseEntity<Map> r = testRestTemplate.exchange("/api/v2/product/" + sku, HttpMethod.GET, new HttpEntity<>(getHeader()), Map.class);
		assertEquals(HttpStatus.OK, r.getStatusCode());
		assertEquals(rating, ((Number) r.getBody().get("rating")).doubleValue(), 0.01, "rating");
		assertEquals(count, ((Number) r.getBody().get("ratingCount")).intValue(), "ratingCount");
	}

	@SuppressWarnings({ "rawtypes", "unchecked" })
	@Test
	public void editingAReviewChangesItAndTheRating() {
		Long p = createProduct("hrvedit");
		review(p, customer("hrve1@test.com"), 5.0);
		Long c2 = customer("hrve2@test.com");
		Long r2 = review(p, c2, 1.0);
		assertRating("hrvedit", 3.0, 2);
		ResponseEntity<String> e = testRestTemplate.exchange("/api/v1/private/products/" + p + "/reviews/" + r2, HttpMethod.PUT,
				new HttpEntity<>(body(p, c2, 3.0), getHeader()), String.class);
		assertTrue(e.getStatusCode().is2xxSuccessful(), "edit: " + e.getStatusCode());
		List<Map> list = reviews(p);
		assertEquals(2, list.size(), "editing must not add a review");
		assertTrue(list.stream().anyMatch(r -> ((Number) r.get("id")).longValue() == r2 && ((Number) r.get("rating")).doubleValue() == 3.0));
		assertRating("hrvedit", 4.0, 2);
	}

	@Test
	public void deletingAReviewRemovesItAndUpdatesTheRating() {
		Long p = createProduct("hrvdel");
		Long r1 = review(p, customer("hrvd1@test.com"), 4.0);
		review(p, customer("hrvd2@test.com"), 2.0);
		ResponseEntity<String> d = testRestTemplate.exchange("/api/v1/private/products/" + p + "/reviews/" + r1, HttpMethod.DELETE,
				new HttpEntity<>(getHeader()), String.class);
		assertTrue(d.getStatusCode().is2xxSuccessful(), "delete: " + d.getStatusCode());
		assertEquals(1, reviews(p).size());
		assertRating("hrvdel", 2.0, 1);
	}

	@Test
	public void missingReviewIsNotFound() {
		Long p = createProduct("hrvmiss");
		Long c = customer("hrvm1@test.com");
		assertEquals(HttpStatus.NOT_FOUND, testRestTemplate.exchange("/api/v1/private/products/" + p + "/reviews/987654", HttpMethod.DELETE,
				new HttpEntity<>(getHeader()), String.class).getStatusCode());
		assertEquals(HttpStatus.NOT_FOUND, testRestTemplate.exchange("/api/v1/private/products/" + p + "/reviews/987654", HttpMethod.PUT,
				new HttpEntity<>(body(p, c, 3.0), getHeader()), String.class).getStatusCode());
	}
}
