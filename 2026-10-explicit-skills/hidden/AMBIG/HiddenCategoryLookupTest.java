package com.salesmanager.test.shop.hidden;

import static org.junit.jupiter.api.Assertions.assertEquals;

import java.util.Map;

import org.junit.jupiter.api.Test;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import com.salesmanager.shop.model.catalog.category.PersistableCategory;
import com.salesmanager.test.shop.common.ServicesTestSupport;

/** Hidden acceptance test for task AMBIG: categories can be read by id and by friendly URL. */
public class HiddenCategoryLookupTest extends ServicesTestSupport {

	private PersistableCategory create(String code, String friendlyUrl) {
		ResponseEntity<PersistableCategory> r = testRestTemplate.postForEntity("/api/v1/private/category?store=DEFAULT",
				new HttpEntity<>(category(code, friendlyUrl), getHeader()), PersistableCategory.class);
		assertEquals(HttpStatus.CREATED, r.getStatusCode());
		return r.getBody();
	}

	@SuppressWarnings("rawtypes")
	private ResponseEntity<Map> get(String path) {
		return testRestTemplate.exchange("/api/v1/category/" + path, HttpMethod.GET, new HttpEntity<>(getHeader()), Map.class);
	}

	@Test
	public void categoryIsFoundById() {
		PersistableCategory c = create("hambiga", "hambig-chairs");
		@SuppressWarnings("rawtypes")
		ResponseEntity<Map> r = get(String.valueOf(c.getId()));
		assertEquals(HttpStatus.OK, r.getStatusCode());
		assertEquals("hambiga", r.getBody().get("code"));
	}

	@Test
	public void categoryIsFoundByFriendlyUrl() {
		create("hambigb", "hambig-tables");
		@SuppressWarnings("rawtypes")
		ResponseEntity<Map> r = get("hambig-tables");
		assertEquals(HttpStatus.OK, r.getStatusCode());
		assertEquals("hambigb", r.getBody().get("code"));
	}

	@Test
	public void unknownIdIsNotFound() {
		assertEquals(HttpStatus.NOT_FOUND, get("987654").getStatusCode());
	}

	@Test
	public void unknownFriendlyUrlIsNotFound() {
		assertEquals(HttpStatus.NOT_FOUND, get("hambig-no-such-url").getStatusCode());
	}
}
