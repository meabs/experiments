package com.salesmanager.test.shop.hidden;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import org.junit.jupiter.api.Test;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import com.salesmanager.shop.model.catalog.category.Category;
import com.salesmanager.shop.model.catalog.category.PersistableCategory;
import com.salesmanager.shop.model.catalog.product.product.PersistableProduct;
import com.salesmanager.shop.model.entity.Entity;
import com.salesmanager.test.shop.common.ServicesTestSupport;

/** Hidden acceptance test for task CATCOUNT: productCount counts the products in a category and its subcategories. */
public class HiddenCategoryProductCountTest extends ServicesTestSupport {

	private Category ref(PersistableCategory c) {
		Category r = new Category();
		r.setId(c.getId());
		r.setCode(c.getCode());
		return r;
	}

	private PersistableCategory createCategory(String code, PersistableCategory parent) {
		PersistableCategory c = category(code);
		if (parent != null) {
			c.setParent(ref(parent));
		}
		ResponseEntity<PersistableCategory> r = testRestTemplate.postForEntity("/api/v1/private/category?store=DEFAULT",
				new HttpEntity<>(c, getHeader()), PersistableCategory.class);
		assertEquals(HttpStatus.CREATED, r.getStatusCode());
		assertNotNull(r.getBody().getId());
		return r.getBody();
	}

	private void createProduct(String sku, boolean available, PersistableCategory... cats) {
		PersistableProduct p = product(sku);
		p.setSku(sku);
		p.setAvailable(available);
		p.setQuantity(10);
		List<Category> list = new ArrayList<>();
		for (PersistableCategory c : cats) {
			list.add(ref(c));
		}
		p.setCategories(list);
		ResponseEntity<Entity> r = testRestTemplate.postForEntity("/api/v1/private/product?store=DEFAULT",
				new HttpEntity<>(p, getHeader()), Entity.class);
		assertEquals(HttpStatus.CREATED, r.getStatusCode());
	}

	@SuppressWarnings("rawtypes")
	private Map get(String url) {
		ResponseEntity<Map> r = testRestTemplate.exchange(url, HttpMethod.GET, new HttpEntity<>(getHeader()), Map.class);
		assertEquals(HttpStatus.OK, r.getStatusCode());
		return r.getBody();
	}

	private int count(Map<?, ?> category) {
		return ((Number) category.get("productCount")).intValue();
	}

	@SuppressWarnings({ "unchecked", "rawtypes" })
	@Test
	public void countsIncludeSubcategoriesAndCountEachProductOnce() {
		PersistableCategory parent = createCategory("hcntparent", null);
		PersistableCategory child = createCategory("hcntchild", parent);
		PersistableCategory empty = createCategory("hcntempty", null);
		createProduct("hcnta", true, parent);
		createProduct("hcntb", true, child);
		createProduct("hcntc", true, parent, child);

		List<Map> top = (List<Map>) get("/api/v1/category?count=100").get("categories");
		Map p = top.stream().filter(c -> "hcntparent".equals(c.get("code"))).findFirst().orElse(null);
		assertNotNull(p, "parent missing from list: " + top);
		assertEquals(3, count(p), "parent counts a, b and c once each");
		List<Map> children = (List<Map>) p.get("children");
		assertTrue(children.stream().anyMatch(c -> "hcntchild".equals(c.get("code")) && count(c) == 2),
				"child inside parent's children should count b and c: " + children);
		assertTrue(top.stream().anyMatch(c -> "hcntempty".equals(c.get("code")) && count(c) == 0),
				"empty category should count 0: " + top);
	}
}
