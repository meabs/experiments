package com.salesmanager.test.shop.hidden;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.junit.jupiter.api.Test;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import com.salesmanager.shop.model.catalog.category.Category;
import com.salesmanager.shop.model.catalog.category.PersistableCategory;
import com.salesmanager.shop.model.entity.Entity;

/**
 * Hidden acceptance tests for ticket CATEGORYDELETE: deleting a category deletes it and the categories below it, and
 * nothing else: products, carts and orders are kept; the deleted category is not found.
 */
@SuppressWarnings({ "rawtypes", "unchecked" })
public class HiddenCategoryDeleteTest extends HiddenOrderSupport {

	// ---- helpers

	private final Map<Long, String> codes = new HashMap<>();

	private long newCategory(String code, Long parent) {
		PersistableCategory c = category(code, code + "-page");
		if (parent != null) {
			Category p = new Category();
			p.setId(parent);
			p.setCode(codes.get(parent)); // Shopizer needs a parent's code and id
			c.setParent(p);
			c.setDepth(2);
		}
		ResponseEntity<Entity> r = testRestTemplate.postForEntity("/api/v1/private/category?store=DEFAULT",
				new HttpEntity<>(c, getHeader()), Entity.class);
		assertTrue(r.getStatusCode().is2xxSuccessful(), "creating category " + code + ": " + r.getStatusCode());
		assertNotNull(r.getBody().getId());
		codes.put(r.getBody().getId(), code);
		return r.getBody().getId();
	}

	private void put(long productId, long categoryId) {
		ResponseEntity<String> r = testRestTemplate.postForEntity(
				"/api/v1/private/product/" + productId + "/category/" + categoryId + "?store=DEFAULT",
				new HttpEntity<>(getHeader()), String.class);
		assertTrue(r.getStatusCode().is2xxSuccessful(), "putting product " + productId + " in category " + categoryId);
	}

	private HttpStatus delete(long categoryId) {
		return testRestTemplate.exchange("/api/v1/private/category/" + categoryId + "?store=DEFAULT", HttpMethod.DELETE,
				new HttpEntity<>(getHeader()), String.class).getStatusCode();
	}

	private ResponseEntity<Map> readProduct(String sku) {
		return testRestTemplate.exchange("/api/v2/product/" + sku + "?store=DEFAULT", HttpMethod.GET,
				new HttpEntity<>(getHeader()), Map.class);
	}

	private static List<Long> categoryIds(Map product) {
		List<Long> ids = new ArrayList<>();
		Object cats = product.get("categories");
		if (cats != null) {
			for (Object o : (List) cats) {
				ids.add(((Number) ((Map) o).get("id")).longValue());
			}
		}
		return ids;
	}

	private List<Long> listedCategories() {
		ResponseEntity<Map> r = testRestTemplate.exchange("/api/v1/category?store=DEFAULT&count=1000", HttpMethod.GET,
				new HttpEntity<>(getHeader()), Map.class);
		assertEquals(HttpStatus.OK, r.getStatusCode());
		List<Long> ids = new ArrayList<>();
		collect((List) r.getBody().get("categories"), ids);
		return ids;
	}

	private static void collect(List cats, List<Long> ids) {
		if (cats == null) {
			return;
		}
		for (Object o : cats) {
			Map c = (Map) o;
			ids.add(((Number) c.get("id")).longValue());
			collect((List) c.get("children"), ids);
		}
	}

	private List<String> productsIn(long categoryId) {
		ResponseEntity<Map> r = testRestTemplate.exchange("/api/v1/products?store=DEFAULT&count=1000&category=" + categoryId,
				HttpMethod.GET, new HttpEntity<>(getHeader()), Map.class);
		List<String> skus = new ArrayList<>();
		if (r.getStatusCode().is2xxSuccessful() && r.getBody() != null && r.getBody().get("products") != null) {
			for (Object o : (List) r.getBody().get("products")) {
				skus.add(String.valueOf(((Map) o).get("sku")));
			}
		}
		return skus;
	}

	private Map item(String sku, int qty) {
		Map m = new HashMap();
		m.put("product", sku);
		m.put("quantity", qty);
		return m;
	}

	// ---- tests

	@Test
	public void aProductOnlyInTheDeletedCategoryIsKept() {
		long cat = newCategory(uniqueSku("cda"), null);
		String a = uniqueSku("cdp");
		long id = createProduct(a, "7.25", 13);
		put(id, cat);
		assertTrue(delete(cat).is2xxSuccessful());
		ResponseEntity<Map> r = readProduct(a);
		assertEquals(HttpStatus.OK, r.getStatusCode(), "the product is still there");
		assertEquals(13, ((Number) r.getBody().get("quantity")).intValue());
		assertEquals(m("7.25"), money(r.getBody().get("price")));
		assertFalse(categoryIds(r.getBody()).contains(cat));
	}

	@Test
	public void aProductKeepsItsOtherCategories() {
		long gone = newCategory(uniqueSku("cdb"), null);
		long stays = newCategory(uniqueSku("cdc"), null);
		String a = uniqueSku("cdq");
		long id = createProduct(a, "3.00", 10);
		put(id, gone);
		put(id, stays);
		assertTrue(delete(gone).is2xxSuccessful());
		List<Long> ids = categoryIds(readProduct(a).getBody());
		assertTrue(ids.contains(stays), "still in the other category: " + ids);
		assertFalse(ids.contains(gone));
		assertTrue(productsIn(stays).contains(a));
	}

	@Test
	public void categoriesBelowAreDeletedAndTheirProductsKept() {
		long parent = newCategory(uniqueSku("cdd"), null);
		long child = newCategory(uniqueSku("cde"), parent);
		String a = uniqueSku("cdr");
		String b = uniqueSku("cds");
		long ida = createProduct(a, "2.00", 10);
		long idb = createProduct(b, "2.00", 10);
		put(ida, parent);
		put(idb, child);
		assertTrue(delete(parent).is2xxSuccessful());
		assertEquals(HttpStatus.NOT_FOUND, testRestTemplate.exchange("/api/v1/category/" + child + "?store=DEFAULT",
				HttpMethod.GET, new HttpEntity<>(getHeader()), String.class).getStatusCode(), "the child is deleted too");
		assertEquals(HttpStatus.OK, readProduct(a).getStatusCode());
		assertEquals(HttpStatus.OK, readProduct(b).getStatusCode());
	}

	@Test
	public void aDeletedCategoryIsNotFound() {
		long cat = newCategory(uniqueSku("cdf"), null);
		assertTrue(delete(cat).is2xxSuccessful());
		assertEquals(HttpStatus.NOT_FOUND, testRestTemplate.exchange("/api/v1/category/" + cat + "?store=DEFAULT",
				HttpMethod.GET, new HttpEntity<>(getHeader()), String.class).getStatusCode());
		assertFalse(listedCategories().contains(cat));
	}

	@Test
	public void aDeletedCategoryListsNoProducts() {
		long cat = newCategory(uniqueSku("cdg"), null);
		String a = uniqueSku("cdt");
		long id = createProduct(a, "2.00", 10);
		put(id, cat);
		assertTrue(productsIn(cat).contains(a));
		assertTrue(delete(cat).is2xxSuccessful());
		assertTrue(productsIn(cat).isEmpty());
	}

	@Test
	public void deletingACategoryThatDoesNotExistIsNotFound() {
		assertEquals(HttpStatus.NOT_FOUND, delete(987654321L));
	}

	@Test
	public void cartsHoldingItsProductsStillWork() {
		long cat = newCategory(uniqueSku("cdh"), null);
		String a = uniqueSku("cdu");
		long id = createProduct(a, "5.00", 10);
		put(id, cat);
		String code = cartWith(lines(a, 2));
		assertTrue(delete(cat).is2xxSuccessful());
		ResponseEntity<Map> c = testRestTemplate.exchange("/api/v1/cart/" + code + "?store=DEFAULT", HttpMethod.GET,
				new HttpEntity<>(getHeader()), Map.class);
		assertEquals(HttpStatus.OK, c.getStatusCode());
		assertEquals(m("10.00"), money(c.getBody().get("subtotal")));
		assertTrue(testRestTemplate.exchange("/api/v1/cart/" + code + "?store=DEFAULT", HttpMethod.PUT,
				new HttpEntity<>(item(a, 3), getHeader()), String.class).getStatusCode().is2xxSuccessful());
		ResponseEntity<Map> co = checkoutCart(code, "cd" + SEQ.incrementAndGet() + "@example.com");
		assertNotNull(co.getBody().get("id"));
	}

	@Test
	public void ordersWithItsProductsStillOpen() {
		long cat = newCategory(uniqueSku("cdi"), null);
		String a = uniqueSku("cdv");
		long id = createProduct(a, "6.00", 10);
		put(id, cat);
		long order = placeOrder(lines(a, 2));
		Map before = getOrder(order);
		assertTrue(delete(cat).is2xxSuccessful());
		ResponseEntity<Map> r = testRestTemplate.exchange("/api/v1/private/orders/" + order + "?store=DEFAULT",
				HttpMethod.GET, new HttpEntity<>(getHeader()), Map.class);
		assertEquals(HttpStatus.OK, r.getStatusCode());
		assertEquals(before.get("totals"), r.getBody().get("totals"));
	}

	@Test
	public void otherCategoriesAreUntouched() {
		long gone = newCategory(uniqueSku("cdj"), null);
		long other = newCategory(uniqueSku("cdk"), null);
		String a = uniqueSku("cdw");
		long id = createProduct(a, "2.00", 10);
		put(id, other);
		assertTrue(delete(gone).is2xxSuccessful());
		assertTrue(listedCategories().contains(other));
		assertEquals(HttpStatus.OK, testRestTemplate.exchange("/api/v1/category/" + other + "?store=DEFAULT",
				HttpMethod.GET, new HttpEntity<>(getHeader()), String.class).getStatusCode());
		assertTrue(productsIn(other).contains(a));
	}
}
