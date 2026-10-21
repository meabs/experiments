package com.salesmanager.test.shop.hidden;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.math.BigDecimal;
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

/** Hidden acceptance test for task CARTLAST: a cart emptied by the shopper stays usable; removing other lines keeps working. */
public class HiddenEmptyCartTest extends ServicesTestSupport {

	private void createProduct(String sku, int price) {
		PersistableProduct p = product(sku);
		p.setSku(sku);
		p.setAvailable(true);
		p.setQuantity(10);
		p.getInventory().getPrice().setPrice(new BigDecimal(price));
		p.getInventory().getPrice().setDiscountedPrice(null);
		ResponseEntity<Entity> r = testRestTemplate.postForEntity("/api/v1/private/product?store=DEFAULT", new HttpEntity<>(p, getHeader()), Entity.class);
		assertEquals(HttpStatus.CREATED, r.getStatusCode());
	}

	private Map<String, Object> item(String sku, int quantity) {
		Map<String, Object> i = new HashMap<>();
		i.put("product", sku);
		i.put("quantity", quantity);
		return i;
	}

	@SuppressWarnings("rawtypes")
	private String newCart(String sku, int quantity) {
		ResponseEntity<Map> r = testRestTemplate.exchange("/api/v1/cart", HttpMethod.POST, new HttpEntity<>(item(sku, quantity), getHeader()), Map.class);
		assertTrue(r.getStatusCode().is2xxSuccessful(), "create cart: " + r.getStatusCode());
		return (String) r.getBody().get("code");
	}

	@SuppressWarnings("rawtypes")
	private ResponseEntity<Map> put(String cart, String sku, int quantity) {
		return testRestTemplate.exchange("/api/v1/cart/" + cart, HttpMethod.PUT, new HttpEntity<>(item(sku, quantity), getHeader()), Map.class);
	}

	@SuppressWarnings("rawtypes")
	private Map get(String cart) {
		ResponseEntity<Map> r = testRestTemplate.exchange("/api/v1/cart/" + cart, HttpMethod.GET, new HttpEntity<>(getHeader()), Map.class);
		assertEquals(HttpStatus.OK, r.getStatusCode(), "GET cart");
		return r.getBody();
	}

	@SuppressWarnings("rawtypes")
	private int lines(Map cart) {
		Object p = cart.get("products");
		return p == null ? 0 : ((List) p).size();
	}

	private double subtotal(Map<?, ?> cart) {
		Object s = cart.get("subtotal");
		return s == null ? 0 : ((Number) s).doubleValue();
	}

	@SuppressWarnings("rawtypes")
	private void assertEmptyThenRefill(String cart, String other) {
		Map empty = get(cart);
		assertEquals(0, lines(empty), "emptied cart has no products");
		assertEquals(0.0, subtotal(empty), 0.001, "emptied cart subtotal");
		ResponseEntity<Map> r = put(cart, other, 2);
		assertTrue(r.getStatusCode().is2xxSuccessful(), "add to emptied cart: " + r.getStatusCode());
		Map refilled = get(cart);
		assertEquals(1, lines(refilled));
		assertEquals(14.0, subtotal(refilled), 0.001);
	}

	@Test
	public void cartEmptiedByRemovingTheLastProductStaysUsable() {
		createProduct("clast1", 10);
		createProduct("clast2", 7);
		String cart = newCart("clast1", 1);
		assertTrue(testRestTemplate.exchange("/api/v1/cart/" + cart + "/product/clast1", HttpMethod.DELETE, new HttpEntity<>(getHeader()),
				String.class).getStatusCode().is2xxSuccessful());
		assertEmptyThenRefill(cart, "clast2");
	}

	@Test
	public void cartEmptiedBySettingTheLastQuantityToZeroStaysUsable() {
		createProduct("clast3", 10);
		createProduct("clast4", 7);
		String cart = newCart("clast3", 1);
		assertTrue(put(cart, "clast3", 0).getStatusCode().is2xxSuccessful());
		assertEmptyThenRefill(cart, "clast4");
	}

	@SuppressWarnings("rawtypes")
	@Test
	public void keepsRemovingOneOfSeveralProducts() {
		createProduct("clast5", 10);
		createProduct("clast6", 7);
		String cart = newCart("clast5", 2);
		put(cart, "clast6", 1);
		assertTrue(testRestTemplate.exchange("/api/v1/cart/" + cart + "/product/clast5", HttpMethod.DELETE, new HttpEntity<>(getHeader()),
				String.class).getStatusCode().is2xxSuccessful());
		Map c = get(cart);
		assertEquals(1, lines(c));
		assertEquals(7.0, subtotal(c), 0.001);
		put(cart, "clast5", 3);
		put(cart, "clast6", 0);
		Map d = get(cart);
		assertEquals(1, lines(d));
		assertEquals(30.0, subtotal(d), 0.001);
	}
}
