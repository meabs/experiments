package com.salesmanager.test.shop.hidden;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.List;
import java.util.Map;

import org.junit.jupiter.api.Test;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import com.salesmanager.shop.model.catalog.category.PersistableCategory;
import com.salesmanager.test.shop.common.ServicesTestSupport;

/** Hidden acceptance test for task CATDUP: category codes are unique per store; a clash answers 409. */
public class HiddenDuplicateCategoryCodeTest extends ServicesTestSupport {

	private ResponseEntity<PersistableCategory> create(String code, String name) {
		return testRestTemplate.exchange("/api/v1/private/category", HttpMethod.POST, new HttpEntity<>(category(code, name), getHeader()),
				PersistableCategory.class);
	}

	private HttpStatus update(Long id, String code, String name) {
		return testRestTemplate.exchange("/api/v1/private/category/" + id, HttpMethod.PUT, new HttpEntity<>(category(code, name), getHeader()),
				String.class).getStatusCode();
	}

	@SuppressWarnings({ "rawtypes", "unchecked" })
	private long countWithCode(String code) {
		ResponseEntity<Map> r = testRestTemplate.exchange("/api/v1/category?count=500&filter=admin", HttpMethod.GET, new HttpEntity<>(getHeader()), Map.class);
		return ((List<Map>) r.getBody().get("categories")).stream().filter(c -> code.equals(c.get("code"))).count();
	}

	@Test
	public void creatingADuplicateCodeIsAConflict() {
		assertEquals(HttpStatus.CREATED, create("hcdupa", "hcdupa-one").getStatusCode());
		assertEquals(HttpStatus.CONFLICT, create("hcdupa", "hcdupa-two").getStatusCode());
		assertEquals(1, countWithCode("hcdupa"));
	}

	@Test
	public void renamingToAnotherCategorysCodeIsAConflict() {
		assertEquals(HttpStatus.CREATED, create("hcdupb", "hcdupb-one").getStatusCode());
		Long second = create("hcdupc", "hcdupc-one").getBody().getId();
		assertEquals(HttpStatus.CONFLICT, update(second, "hcdupb", "hcdupc-one"));
		assertEquals(1, countWithCode("hcdupb"));
		assertEquals(1, countWithCode("hcdupc"));
	}

	@Test
	public void updatingACategoryKeepingItsOwnCodeWorks() {
		Long id = create("hcdupd", "hcdupd-one").getBody().getId();
		assertTrue(update(id, "hcdupd", "hcdupd-renamed").is2xxSuccessful());
	}
}
