package com.salesmanager.test.shop.hidden;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.Map;

import org.junit.jupiter.api.Test;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import com.salesmanager.shop.model.catalog.product.product.PersistableProduct;
import com.salesmanager.shop.model.entity.Entity;
import com.salesmanager.test.shop.common.ServicesTestSupport;

/** Hidden acceptance test for task NOTFOUND: missing manufacturers and products answer 404. */
public class HiddenNotFoundTest extends ServicesTestSupport {

	private HttpStatus status(String url) {
		return testRestTemplate.exchange(url, HttpMethod.GET, new HttpEntity<>(getHeader()), String.class).getStatusCode();
	}

	@Test
	public void unknownManufacturerIsNotFound() {
		assertEquals(HttpStatus.NOT_FOUND, status("/api/v1/manufacturer/987654"));
	}

	@SuppressWarnings("rawtypes")
	@Test
	public void deletedManufacturerIsNotFound() {
		ResponseEntity<Map> c = testRestTemplate.exchange("/api/v1/private/manufacturer", HttpMethod.POST,
				new HttpEntity<>(manufacturer("hnfman"), getHeader()), Map.class);
		assertTrue(c.getStatusCode().is2xxSuccessful());
		Object id = c.getBody().get("id");
		assertEquals(HttpStatus.OK, status("/api/v1/manufacturer/" + id));
		testRestTemplate.exchange("/api/v1/private/manufacturer/" + id, HttpMethod.DELETE, new HttpEntity<>(getHeader()), String.class);
		assertEquals(HttpStatus.NOT_FOUND, status("/api/v1/manufacturer/" + id));
	}

	@Test
	public void unknownProductSkuIsNotFound() {
		assertEquals(HttpStatus.NOT_FOUND, status("/api/v2/product/hnf-no-such-sku"));
	}

	@Test
	public void existingProductIsStillFound() {
		PersistableProduct p = product("hnfprod");
		p.setSku("hnfprod");
		ResponseEntity<Entity> r = testRestTemplate.postForEntity("/api/v1/private/product?store=DEFAULT", new HttpEntity<>(p, getHeader()), Entity.class);
		assertEquals(HttpStatus.CREATED, r.getStatusCode());
		assertEquals(HttpStatus.OK, status("/api/v2/product/hnfprod"));
	}
}
