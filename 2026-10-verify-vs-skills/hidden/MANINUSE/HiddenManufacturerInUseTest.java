package com.salesmanager.test.shop.hidden;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.List;
import java.util.Map;

import org.junit.jupiter.api.Test;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import com.salesmanager.shop.model.catalog.product.product.PersistableProduct;
import com.salesmanager.shop.model.catalog.product.product.ProductSpecification;
import com.salesmanager.shop.model.entity.Entity;
import com.salesmanager.test.shop.common.ServicesTestSupport;

/** Hidden acceptance test for task MANINUSE: a manufacturer still used by products cannot be deleted (409). */
public class HiddenManufacturerInUseTest extends ServicesTestSupport {

	@SuppressWarnings("rawtypes")
	private Object createManufacturer(String code) {
		ResponseEntity<Map> r = testRestTemplate.exchange("/api/v1/private/manufacturer", HttpMethod.POST,
				new HttpEntity<>(manufacturer(code), getHeader()), Map.class);
		assertTrue(r.getStatusCode().is2xxSuccessful());
		return r.getBody().get("id");
	}

	private void createProductOf(String sku, String manufacturerCode) {
		PersistableProduct p = product(sku);
		p.setSku(sku);
		ProductSpecification spec = new ProductSpecification();
		spec.setManufacturer(manufacturerCode);
		p.setProductSpecifications(spec);
		ResponseEntity<Entity> r = testRestTemplate.postForEntity("/api/v1/private/product?store=DEFAULT", new HttpEntity<>(p, getHeader()), Entity.class);
		assertEquals(HttpStatus.CREATED, r.getStatusCode());
	}

	private HttpStatus delete(Object id) {
		return testRestTemplate.exchange("/api/v1/private/manufacturer/" + id, HttpMethod.DELETE, new HttpEntity<>(getHeader()), String.class)
				.getStatusCode();
	}

	@SuppressWarnings({ "rawtypes", "unchecked" })
	private boolean listed(String code) {
		ResponseEntity<Map> r = testRestTemplate.exchange("/api/v1/manufacturers?count=500", HttpMethod.GET, new HttpEntity<>(getHeader()), Map.class);
		return ((List<Map>) r.getBody().get("manufacturers")).stream().anyMatch(m -> code.equals(m.get("code")));
	}

	@Test
	public void manufacturerUsedByAProductIsAConflict() {
		Object id = createManufacturer("hmiuused");
		createProductOf("hmiuprod", "hmiuused");
		assertEquals(HttpStatus.CONFLICT, delete(id));
		assertTrue(listed("hmiuused"), "manufacturer must still exist");
	}

	@Test
	public void unusedManufacturerIsDeleted() {
		Object id = createManufacturer("hmiufree");
		assertEquals(HttpStatus.OK, delete(id));
		assertFalse(listed("hmiufree"), "manufacturer must be gone");
	}

	@Test
	public void unknownManufacturerIsNotFound() {
		assertEquals(HttpStatus.NOT_FOUND, delete(987655));
	}
}
