package com.salesmanager.test.shop.hidden;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;

import org.junit.jupiter.api.Test;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;

import com.salesmanager.shop.model.catalog.product.product.PersistableProduct;
import com.salesmanager.shop.model.entity.Entity;
import com.salesmanager.test.shop.common.ServicesTestSupport;

/**
 * Hidden acceptance test for feature TIERPRICE: quantity price tiers on products, applied to cart lines. Every product
 * made here costs 125 a unit without tiers (the test helper's discounted price).
 */
@SuppressWarnings({ "rawtypes", "unchecked" })
public class HiddenPriceTiersTest extends ServicesTestSupport {

	private static final AtomicInteger SEQ = new AtomicInteger();

	// ---- helpers

	private long newProduct(String sku) {
		PersistableProduct p = product(sku);
		p.setSku(sku);
		p.setQuantity(1000);
		p.getInventory().setQuantity(1000);
		ResponseEntity<Entity> r = testRestTemplate.postForEntity("/api/v1/private/product?store=DEFAULT",
				new HttpEntity<>(p, getHeader()), Entity.class);
		assertEquals(HttpStatus.CREATED, r.getStatusCode(), "creating product " + sku);
		return r.getBody().getId();
	}

	private String sku() {
		return "tier" + SEQ.incrementAndGet() + "x" + System.nanoTime() % 100000;
	}

	private static Map<String, Object> tier(Object min, Object price) {
		Map<String, Object> t = new HashMap<>();
		t.put("minQuantity", min);
		t.put("price", price);
		return t;
	}

	private static List<Map<String, Object>> tiers(Map<String, Object>... t) {
		List<Map<String, Object>> l = new ArrayList<>();
		for (Map<String, Object> x : t) {
			l.add(x);
		}
		return l;
	}

	private String url(long id) {
		return "/api/v1/private/product/" + id + "/tiers?store=DEFAULT";
	}

	private ResponseEntity<List> put(long id, Object body) {
		return testRestTemplate.exchange(url(id), HttpMethod.PUT, new HttpEntity<>(body, getHeader()), List.class);
	}

	private ResponseEntity<String> putRaw(long id, Object body) {
		return testRestTemplate.exchange(url(id), HttpMethod.PUT, new HttpEntity<>(body, getHeader()), String.class);
	}

	private List<Map> get(long id) {
		ResponseEntity<List> r = testRestTemplate.exchange(url(id), HttpMethod.GET, new HttpEntity<>(getHeader()), List.class);
		assertEquals(HttpStatus.OK, r.getStatusCode());
		return r.getBody();
	}

	private Map<String, Object> line(String sku, int qty) {
		Map<String, Object> i = new HashMap<>();
		i.put("product", sku);
		i.put("quantity", qty);
		return i;
	}

	private String cart(String sku, int qty) {
		ResponseEntity<Map> c = testRestTemplate.exchange("/api/v1/cart/", HttpMethod.POST,
				new HttpEntity<>(line(sku, qty), getHeader()), Map.class);
		assertEquals(HttpStatus.CREATED, c.getStatusCode());
		return (String) c.getBody().get("code");
	}

	private void setQuantity(String cart, String sku, int qty) {
		ResponseEntity<Map> r = testRestTemplate.exchange("/api/v1/cart/" + cart, HttpMethod.PUT,
				new HttpEntity<>(line(sku, qty), getHeader()), Map.class);
		assertTrue(r.getStatusCode().is2xxSuccessful(), "setting " + sku + " to " + qty + ": " + r.getStatusCode());
	}

	private Map read(String cart) {
		ResponseEntity<Map> g = testRestTemplate.exchange("/api/v1/cart/" + cart, HttpMethod.GET,
				new HttpEntity<>(getHeader()), Map.class);
		assertEquals(HttpStatus.OK, g.getStatusCode());
		return g.getBody();
	}

	private static Map lineOf(Map cart, String sku) {
		for (Map p : (List<Map>) cart.get("products")) {
			if (sku.equals(p.get("sku"))) {
				return p;
			}
		}
		throw new AssertionError("no cart line for " + sku + " in " + cart.get("products"));
	}

	private static void assertMoney(String expected, Object actual, String what) {
		assertNotNull(actual, what);
		assertEquals(0, new BigDecimal(expected).compareTo(new BigDecimal(String.valueOf(actual))),
				what + ": expected " + expected + " but was " + actual);
	}

	private void assertCart(Map cart, String sku, String lineSubTotal, String subtotal) {
		assertMoney(lineSubTotal, lineOf(cart, sku).get("subTotal"), "line subTotal for " + sku);
		assertMoney(subtotal, cart.get("subtotal"), "cart subtotal");
		assertMoney(subtotal, cart.get("total"), "cart total");
	}

	private long productWithTiers(String sku) {
		long id = newProduct(sku);
		assertEquals(HttpStatus.OK, put(id, tiers(tier(10, 90), tier(3, 110))).getStatusCode());
		return id;
	}

	// ---- admin API

	@Test
	public void storesTiersAndListsThemByMinimumQuantity() {
		long id = newProduct(sku());
		ResponseEntity<List> r = put(id, tiers(tier(10, 90), tier(3, 110)));
		assertEquals(HttpStatus.OK, r.getStatusCode());
		for (List<Map> l : java.util.Arrays.asList((List<Map>) r.getBody(), get(id))) {
			assertEquals(2, l.size(), "tiers: " + l);
			assertEquals(3, ((Number) l.get(0).get("minQuantity")).intValue());
			assertMoney("110", l.get(0).get("price"), "first tier price");
			assertEquals(10, ((Number) l.get(1).get("minQuantity")).intValue());
			assertMoney("90", l.get(1).get("price"), "second tier price");
		}
	}

	@Test
	public void replacingTiersDropsTheOldOnesAndAnEmptyListRemovesAll() {
		long id = productWithTiers(sku());
		assertEquals(HttpStatus.OK, put(id, tiers(tier(5, 100))).getStatusCode());
		List<Map> l = get(id);
		assertEquals(1, l.size(), "tiers after replace: " + l);
		assertEquals(5, ((Number) l.get(0).get("minQuantity")).intValue());
		assertEquals(HttpStatus.OK, put(id, new ArrayList<>()).getStatusCode());
		assertTrue(get(id).isEmpty(), "tiers after an empty list");
	}

	@Test
	public void invalidTiersAreRejectedAndTheOldTiersKept() {
		long id = productWithTiers(sku());
		Object[] bad = {
				tiers(tier(1, 100)), // minimum below 2
				tiers(tier(3, 0)), // price not positive
				tiers(tier(3, -5)),
				tiers(tier(3, 110), tier(3, 100)), // same minimum twice
				tiers(tier(3, 110), tier(10, 110)), // price does not fall
				tiers(tier(3, 100), tier(10, 105)),
				tiers(tier(2.5, 100)), // not a whole number
				tiers(tier(null, 100)), tiers(tier(3, null)) };
		for (Object b : bad) {
			assertEquals(HttpStatus.BAD_REQUEST, putRaw(id, b).getStatusCode(), "tiers " + b);
		}
		List<Map> l = get(id);
		assertEquals(2, l.size(), "tiers kept after rejected changes: " + l);
		assertEquals(3, ((Number) l.get(0).get("minQuantity")).intValue());
	}

	@Test
	public void atMostTenTiers() {
		long id = newProduct(sku());
		List<Map<String, Object>> ten = new ArrayList<>(), eleven = new ArrayList<>();
		for (int i = 0; i < 11; i++) {
			Map<String, Object> t = tier(2 + i, 120 - i);
			if (i < 10) {
				ten.add(t);
			}
			eleven.add(t);
		}
		assertEquals(HttpStatus.BAD_REQUEST, putRaw(id, eleven).getStatusCode(), "eleven tiers");
		assertEquals(HttpStatus.OK, put(id, ten).getStatusCode(), "ten tiers");
		assertEquals(10, get(id).size());
	}

	@Test
	public void unknownProductIsNotFound() {
		assertEquals(HttpStatus.NOT_FOUND, putRaw(987654321L, tiers(tier(3, 100))).getStatusCode());
		assertEquals(HttpStatus.NOT_FOUND, testRestTemplate.exchange(url(987654321L), HttpMethod.GET,
				new HttpEntity<>(getHeader()), String.class).getStatusCode());
	}

	@Test
	public void tiersNeedAnAdmin() {
		long id = newProduct(sku());
		HttpHeaders anonymous = new HttpHeaders();
		anonymous.setContentType(MediaType.APPLICATION_JSON);
		ResponseEntity<String> r = testRestTemplate.exchange(url(id), HttpMethod.PUT,
				new HttpEntity<>(tiers(tier(3, 100)), anonymous), String.class);
		assertTrue(r.getStatusCode() == HttpStatus.UNAUTHORIZED || r.getStatusCode() == HttpStatus.FORBIDDEN,
				"without a token: " + r.getStatusCode());
		assertTrue(get(id).isEmpty(), "no tiers stored without a token");
	}

	@Test
	public void aProductWithTiersCanStillBeDeleted() {
		long id = productWithTiers(sku());
		ResponseEntity<String> r = testRestTemplate.exchange("/api/v1/private/product/" + id + "?store=DEFAULT",
				HttpMethod.DELETE, new HttpEntity<>(getHeader()), String.class);
		assertTrue(r.getStatusCode().is2xxSuccessful(), "deleting a product with tiers: " + r.getStatusCode());
		assertEquals(HttpStatus.NOT_FOUND, testRestTemplate.exchange(url(id), HttpMethod.GET,
				new HttpEntity<>(getHeader()), String.class).getStatusCode());
	}

	// ---- cart pricing

	@Test
	public void belowTheFirstTierTheNormalPriceApplies() {
		String s = sku();
		productWithTiers(s);
		assertCart(read(cart(s, 2)), s, "250", "250");
	}

	@Test
	public void reachingATierUsesItsPrice() {
		String s = sku();
		productWithTiers(s);
		assertCart(read(cart(s, 3)), s, "330", "330");
	}

	@Test
	public void theLargestTierReachedApplies() {
		String s = sku();
		productWithTiers(s);
		assertCart(read(cart(s, 12)), s, "1080", "1080");
	}

	@Test
	public void changingTheQuantityRepricesTheLine() {
		String s = sku();
		productWithTiers(s);
		String c = cart(s, 3);
		setQuantity(c, s, 10);
		assertCart(read(c), s, "900", "900");
		setQuantity(c, s, 2);
		assertCart(read(c), s, "250", "250");
	}

	@Test
	public void aTierAboveTheNormalPriceIsNotUsed() {
		String s = sku();
		long id = newProduct(s);
		assertEquals(HttpStatus.OK, put(id, tiers(tier(3, 200), tier(6, 100))).getStatusCode());
		String c = cart(s, 3);
		assertCart(read(c), s, "375", "375");
		setQuantity(c, s, 6);
		assertCart(read(c), s, "600", "600");
	}

	@Test
	public void editingTiersRepricesAnExistingCart() {
		String s = sku();
		long id = newProduct(s);
		String c = cart(s, 5);
		assertCart(read(c), s, "625", "625");
		assertEquals(HttpStatus.OK, put(id, tiers(tier(5, 100))).getStatusCode());
		assertCart(read(c), s, "500", "500");
		assertEquals(HttpStatus.OK, put(id, new ArrayList<>()).getStatusCode());
		assertCart(read(c), s, "625", "625");
	}

	@Test
	public void eachLineIsPricedOnItsOwnProductsTiers() {
		String a = sku(), b = sku();
		productWithTiers(a);
		newProduct(b);
		String c = cart(a, 3);
		setQuantity(c, b, 3);
		Map cart = read(c);
		assertMoney("330", lineOf(cart, a).get("subTotal"), "line with tiers");
		assertMoney("375", lineOf(cart, b).get("subTotal"), "line without tiers");
		assertMoney("705", cart.get("subtotal"), "cart subtotal");
		assertMoney("705", cart.get("total"), "cart total");
	}
}
