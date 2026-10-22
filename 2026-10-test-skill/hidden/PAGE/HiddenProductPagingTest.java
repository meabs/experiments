package com.salesmanager.test.shop.hidden;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

import org.junit.jupiter.api.Test;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import com.salesmanager.shop.model.catalog.product.product.PersistableProduct;
import com.salesmanager.shop.model.entity.Entity;
import com.salesmanager.test.shop.common.ServicesTestSupport;

/** Hidden acceptance test for task PAGE: the v2 product list must honour the page parameter. */
public class HiddenProductPagingTest extends ServicesTestSupport {

	private static final String PREFIX = "pgxq";

	private void createProducts() {
		for (int i = 0; i < 5; i++) {
			PersistableProduct p = product(PREFIX + i);
			p.setSku(PREFIX + i);
			p.setAvailable(true);
			p.setQuantity(10);
			ResponseEntity<Entity> r = testRestTemplate.postForEntity("/api/v1/private/product?store=DEFAULT",
					new HttpEntity<>(p, getHeader()), Entity.class);
			assertEquals(HttpStatus.CREATED, r.getStatusCode());
		}
	}

	@SuppressWarnings("unchecked")
	private List<String> page(int page) {
		ResponseEntity<Map> r = testRestTemplate.exchange("/api/v2/products?name=" + PREFIX + "&count=2&page=" + page,
				HttpMethod.GET, new HttpEntity<>(getHeader()), Map.class);
		assertEquals(HttpStatus.OK, r.getStatusCode());
		List<String> skus = new ArrayList<>();
		for (Map<String, Object> p : (List<Map<String, Object>>) r.getBody().get("products")) {
			skus.add((String) p.get("sku"));
		}
		return skus;
	}

	@Test
	public void pagesAreDistinctAndCoverEveryProduct() {
		createProducts();
		List<String> p0 = page(0), p1 = page(1), p2 = page(2), p3 = page(3);
		assertEquals(2, p0.size(), "page 0: " + p0);
		assertEquals(2, p1.size(), "page 1: " + p1);
		assertEquals(1, p2.size(), "page 2: " + p2);
		assertTrue(p3.isEmpty(), "page 3 should be empty: " + p3);
		Set<String> all = new HashSet<>();
		all.addAll(p0);
		all.addAll(p1);
		all.addAll(p2);
		assertEquals(5, all.size(), "pages overlap: " + p0 + p1 + p2);
		for (int i = 0; i < 5; i++) {
			assertTrue(all.contains(PREFIX + i), "missing " + PREFIX + i);
		}
	}
}
