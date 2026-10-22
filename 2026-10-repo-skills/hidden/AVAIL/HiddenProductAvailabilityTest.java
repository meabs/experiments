package com.salesmanager.test.shop.hidden;

import static org.junit.jupiter.api.Assertions.assertEquals;

import java.util.Map;

import org.junit.jupiter.api.Test;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import com.salesmanager.shop.model.catalog.product.product.PersistableProduct;
import com.salesmanager.shop.model.entity.Entity;
import com.salesmanager.test.shop.common.ServicesTestSupport;

/** Hidden acceptance test for task AVAIL: the availability sent on create is stored and returned. */
public class HiddenProductAvailabilityTest extends ServicesTestSupport {

	private Object createAndRead(String sku, boolean available, boolean visible) {
		PersistableProduct p = product(sku);
		p.setSku(sku);
		p.setAvailable(available);
		p.setVisible(visible);
		p.setQuantity(10);
		ResponseEntity<Entity> r = testRestTemplate.postForEntity("/api/v1/private/product?store=DEFAULT",
				new HttpEntity<>(p, getHeader()), Entity.class);
		assertEquals(HttpStatus.CREATED, r.getStatusCode());
		@SuppressWarnings("rawtypes")
		ResponseEntity<Map> g = testRestTemplate.exchange("/api/v2/product/" + sku, HttpMethod.GET,
				new HttpEntity<>(getHeader()), Map.class);
		assertEquals(HttpStatus.OK, g.getStatusCode());
		return g.getBody().get("available");
	}

	@Test
	public void unavailableProductIsStoredAsUnavailable() {
		assertEquals(Boolean.FALSE, createAndRead("havailno", false, true));
	}

	@Test
	public void availableProductIsStoredAsAvailable() {
		assertEquals(Boolean.TRUE, createAndRead("havailyes", true, true));
	}

	@Test
	public void availabilityDoesNotFollowVisibility() {
		assertEquals(Boolean.TRUE, createAndRead("havailhidden", true, false));
	}
}
