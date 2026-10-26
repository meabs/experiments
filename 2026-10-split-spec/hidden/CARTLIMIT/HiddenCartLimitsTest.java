package com.salesmanager.test.shop.hidden;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.ArrayList;
import java.util.Arrays;
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
 * Hidden acceptance test for feature CARTLIMIT: per-product purchase limits and store-wide cart caps, enforced on cart
 * changes, with warnings on carts that break rules set later. Tests that set the store's caps clear them afterwards.
 */
@SuppressWarnings({ "rawtypes", "unchecked" })
public class HiddenCartLimitsTest extends ServicesTestSupport {

	private static final AtomicInteger SEQ = new AtomicInteger();

	// ---- helpers

	private static final class P {
		final long id;
		final String sku;

		P(long id, String sku) {
			this.id = id;
			this.sku = sku;
		}
	}

	private P newProduct() {
		String sku = "lim" + SEQ.incrementAndGet() + "x" + System.nanoTime() % 100000;
		PersistableProduct p = product(sku);
		p.setSku(sku);
		p.setQuantity(1000);
		p.getInventory().setQuantity(1000);
		ResponseEntity<Entity> r = testRestTemplate.postForEntity("/api/v1/private/product?store=DEFAULT",
				new HttpEntity<>(p, getHeader()), Entity.class);
		assertEquals(HttpStatus.CREATED, r.getStatusCode(), "creating product " + sku);
		return new P(r.getBody().getId(), sku);
	}

	private static Map<String, Object> limits(Integer min, Integer max, Integer pack) {
		Map<String, Object> m = new HashMap<>();
		m.put("minPerCart", min);
		m.put("maxPerCart", max);
		m.put("packSize", pack);
		return m;
	}

	private ResponseEntity<Map> setLimits(P p, Object body) {
		return testRestTemplate.exchange("/api/v1/private/product/" + p.id + "/limits?store=DEFAULT", HttpMethod.PUT,
				new HttpEntity<>(body, getHeader()), Map.class);
	}

	private HttpStatus setLimitsStatus(long id, Object body) {
		return testRestTemplate.exchange("/api/v1/private/product/" + id + "/limits?store=DEFAULT", HttpMethod.PUT,
				new HttpEntity<>(body, getHeader()), String.class).getStatusCode();
	}

	private Map getLimits(P p) {
		ResponseEntity<Map> r = testRestTemplate.exchange("/api/v1/private/product/" + p.id + "/limits?store=DEFAULT", HttpMethod.GET,
				new HttpEntity<>(getHeader()), Map.class);
		assertEquals(HttpStatus.OK, r.getStatusCode());
		return r.getBody();
	}

	private ResponseEntity<Map> setCaps(Integer maxLines, Integer maxUnits) {
		Map<String, Object> m = new HashMap<>();
		m.put("maxLines", maxLines);
		m.put("maxUnits", maxUnits);
		return testRestTemplate.exchange("/api/v1/private/cart-rules?store=DEFAULT", HttpMethod.PUT, new HttpEntity<>(m, getHeader()),
				Map.class);
	}

	private void clearCaps() {
		assertEquals(HttpStatus.OK, setCaps(null, null).getStatusCode());
	}

	private Map<String, Object> line(String sku, int qty) {
		Map<String, Object> i = new HashMap<>();
		i.put("product", sku);
		i.put("quantity", qty);
		return i;
	}

	private ResponseEntity<Map> newCart(String sku, int qty) {
		return testRestTemplate.exchange("/api/v1/cart/", HttpMethod.POST, new HttpEntity<>(line(sku, qty), getHeader()), Map.class);
	}

	private String cart(String sku, int qty) {
		ResponseEntity<Map> c = newCart(sku, qty);
		assertEquals(HttpStatus.CREATED, c.getStatusCode(), "new cart with " + qty + " of " + sku);
		return (String) c.getBody().get("code");
	}

	private ResponseEntity<Map> put(String cart, String sku, int qty) {
		return testRestTemplate.exchange("/api/v1/cart/" + cart, HttpMethod.PUT, new HttpEntity<>(line(sku, qty), getHeader()), Map.class);
	}

	private void ok(ResponseEntity<Map> r, String what) {
		assertTrue(r.getStatusCode().is2xxSuccessful(), what + ": " + r.getStatusCode() + " " + r.getBody());
	}

	private void refused(ResponseEntity<Map> r, String rule, String what) {
		assertEquals(HttpStatus.BAD_REQUEST, r.getStatusCode(), what + ": " + r.getBody());
		assertEquals(rule, r.getBody().get("errorCode"), what + ": " + r.getBody());
	}

	private Map read(String cart) {
		ResponseEntity<Map> g = testRestTemplate.exchange("/api/v1/cart/" + cart, HttpMethod.GET, new HttpEntity<>(getHeader()), Map.class);
		assertEquals(HttpStatus.OK, g.getStatusCode());
		return g.getBody();
	}

	private int quantity(String cart, String sku) {
		int q = 0;
		for (Map p : (List<Map>) read(cart).get("products")) {
			if (sku.equals(p.get("sku"))) {
				q += ((Number) p.get("quantity")).intValue();
			}
		}
		return q;
	}

	private List<String> warnings(String cart) {
		List<String> out = new ArrayList<>();
		Object w = read(cart).get("limitWarnings");
		assertTrue(w instanceof List, "limitWarnings is a list: " + w);
		for (Map m : (List<Map>) w) {
			out.add(m.get("sku") + ":" + m.get("rule"));
		}
		return out;
	}

	// ---- admin API

	@Test
	public void limitsAreStoredAndRead() {
		P p = newProduct(), none = newProduct();
		ResponseEntity<Map> r = setLimits(p, limits(2, 6, 2));
		assertEquals(HttpStatus.OK, r.getStatusCode());
		for (Map m : Arrays.asList(r.getBody(), getLimits(p))) {
			assertEquals(2, ((Number) m.get("minPerCart")).intValue());
			assertEquals(6, ((Number) m.get("maxPerCart")).intValue());
			assertEquals(2, ((Number) m.get("packSize")).intValue());
		}
		Map n = getLimits(none);
		assertNull(n.get("minPerCart"));
		assertNull(n.get("maxPerCart"));
		assertNull(n.get("packSize"));
	}

	@Test
	public void invalidLimitsAreRejectedAndTheOldOnesKept() {
		P p = newProduct();
		setLimits(p, limits(null, 5, null));
		Map<String, Object> fraction = limits(null, null, null);
		fraction.put("packSize", 1.5);
		Map<String, Object> text = limits(null, null, null);
		text.put("maxPerCart", "many");
		Object[] bad = { limits(0, null, null), limits(null, -1, null), limits(4, 3, null), limits(null, 2, 3), fraction, text };
		for (Object b : bad) {
			assertEquals(HttpStatus.BAD_REQUEST, setLimitsStatus(p.id, b), "limits " + b);
		}
		assertEquals(5, ((Number) getLimits(p).get("maxPerCart")).intValue());
	}

	@Test
	public void unknownProduct() {
		assertEquals(HttpStatus.NOT_FOUND, setLimitsStatus(987654321L, limits(null, 3, null)));
	}

	@Test
	public void limitsNeedAnAdmin() {
		P p = newProduct();
		HttpHeaders anonymous = new HttpHeaders();
		anonymous.setContentType(MediaType.APPLICATION_JSON);
		HttpStatus s = testRestTemplate.exchange("/api/v1/private/product/" + p.id + "/limits?store=DEFAULT", HttpMethod.PUT,
				new HttpEntity<>(limits(null, 1, null), anonymous), String.class).getStatusCode();
		assertTrue(s == HttpStatus.UNAUTHORIZED || s == HttpStatus.FORBIDDEN, "without a token: " + s);
		assertNull(getLimits(p).get("maxPerCart"));
	}

	@Test
	public void storeCapsAreStoredAndValidated() {
		try {
			ResponseEntity<Map> r = setCaps(7, 40);
			assertEquals(HttpStatus.OK, r.getStatusCode());
			ResponseEntity<Map> g = testRestTemplate.exchange("/api/v1/private/cart-rules?store=DEFAULT", HttpMethod.GET,
					new HttpEntity<>(getHeader()), Map.class);
			assertEquals(7, ((Number) g.getBody().get("maxLines")).intValue());
			assertEquals(40, ((Number) g.getBody().get("maxUnits")).intValue());
			Map<String, Object> zero = new HashMap<>();
			zero.put("maxLines", 0);
			assertEquals(HttpStatus.BAD_REQUEST, testRestTemplate.exchange("/api/v1/private/cart-rules?store=DEFAULT", HttpMethod.PUT,
					new HttpEntity<>(zero, getHeader()), String.class).getStatusCode());
		} finally {
			clearCaps();
		}
	}

	// ---- per-product limits in the cart

	@Test
	public void maximumPerCart() {
		P p = newProduct();
		setLimits(p, limits(null, 3, null));
		refused(newCart(p.sku, 4), "MAX_PER_CART", "a new cart over the maximum");
		String c = cart(p.sku, 3);
		refused(put(c, p.sku, 4), "MAX_PER_CART", "raising a line over the maximum");
		assertEquals(3, quantity(c, p.sku), "the cart is unchanged");
	}

	@Test
	public void minimumPerCart() {
		P p = newProduct(), other = newProduct();
		setLimits(p, limits(2, null, null));
		refused(newCart(p.sku, 1), "MIN_PER_CART", "a new cart under the minimum");
		String c = cart(other.sku, 1);
		refused(put(c, p.sku, 1), "MIN_PER_CART", "adding a line under the minimum");
		ok(put(c, p.sku, 2), "adding the minimum");
		refused(put(c, p.sku, 1), "MIN_PER_CART", "lowering a line under the minimum");
		assertEquals(2, quantity(c, p.sku));
		ok(put(c, p.sku, 0), "removing the line is always allowed");
		assertEquals(0, quantity(c, p.sku));
	}

	@Test
	public void packSize() {
		P p = newProduct();
		setLimits(p, limits(null, null, 6));
		refused(newCart(p.sku, 4), "PACK_SIZE", "not a whole number of packs");
		String c = cart(p.sku, 6);
		ok(put(c, p.sku, 12), "two packs");
		refused(put(c, p.sku, 13), "PACK_SIZE", "a broken pack");
		assertEquals(12, quantity(c, p.sku));
	}

	@Test
	public void theMultiEndpointIsCheckedToo() {
		P p = newProduct(), q = newProduct();
		setLimits(p, limits(null, 2, null));
		String c = cart(q.sku, 1);
		ResponseEntity<Map> r = testRestTemplate.exchange("/api/v1/cart/" + c + "/multi", HttpMethod.POST,
				new HttpEntity<>(Arrays.asList(line(q.sku, 2), line(p.sku, 5)), getHeader()), Map.class);
		refused(r, "MAX_PER_CART", "multi update with a line over the maximum");
		assertEquals(1, quantity(c, q.sku), "nothing in the request was applied");
		assertEquals(0, quantity(c, p.sku));
	}

	@Test
	public void otherProductsAreNotLimited() {
		P limited = newProduct(), free = newProduct();
		setLimits(limited, limits(null, 2, null));
		String c = cart(free.sku, 50);
		ok(put(c, free.sku, 80), "a product with no limits");
		ok(put(c, limited.sku, 2), "the limited product at its maximum");
	}

	@Test
	public void clearingLimitsLiftsThem() {
		P p = newProduct();
		setLimits(p, limits(null, 2, null));
		assertEquals(HttpStatus.OK, setLimits(p, limits(null, null, null)).getStatusCode());
		assertNull(getLimits(p).get("maxPerCart"));
		cart(p.sku, 9);
	}

	// ---- store caps

	@Test
	public void maximumLinesPerCart() {
		P a = newProduct(), b = newProduct(), d = newProduct();
		try {
			assertEquals(HttpStatus.OK, setCaps(2, null).getStatusCode());
			String c = cart(a.sku, 1);
			ok(put(c, b.sku, 1), "second line");
			refused(put(c, d.sku, 1), "MAX_LINES", "third line");
			ok(put(c, a.sku, 5), "changing an existing line");
			assertEquals(0, quantity(c, d.sku));
		} finally {
			clearCaps();
		}
	}

	@Test
	public void maximumUnitsPerCart() {
		P a = newProduct(), b = newProduct();
		try {
			assertEquals(HttpStatus.OK, setCaps(null, 5).getStatusCode());
			String c = cart(a.sku, 3);
			refused(put(c, b.sku, 3), "MAX_UNITS", "going over the units cap");
			ok(put(c, b.sku, 2), "up to the cap");
			refused(put(c, a.sku, 4), "MAX_UNITS", "raising a line over the cap");
			ok(put(c, a.sku, 1), "lowering is allowed");
			refused(newCart(a.sku, 6), "MAX_UNITS", "a new cart over the cap");
		} finally {
			clearCaps();
		}
	}

	// ---- warnings

	@Test
	public void aCartShowsTheRulesItBreaks() {
		P a = newProduct(), b = newProduct();
		String c = cart(a.sku, 5);
		ok(put(c, b.sku, 3), "second line");
		assertTrue(warnings(c).isEmpty(), "no warnings before any rule: " + warnings(c));
		try {
			setLimits(a, limits(null, 3, null));
			setLimits(b, limits(null, null, 2));
			assertEquals(HttpStatus.OK, setCaps(1, null).getStatusCode());
			List<String> w = warnings(c);
			assertTrue(w.contains(a.sku + ":MAX_PER_CART"), "warnings: " + w);
			assertTrue(w.contains(b.sku + ":PACK_SIZE"), "warnings: " + w);
			assertTrue(w.contains("null:MAX_LINES"), "warnings: " + w);
			assertEquals(3, w.size(), "warnings: " + w);
			refused(put(c, a.sku, 4), "MAX_PER_CART", "a change that still breaks the line's limit");
			ok(put(c, a.sku, 3), "fixing the line");
			ok(put(c, b.sku, 0), "removing the other line");
			assertTrue(warnings(c).isEmpty(), "no warnings once fixed: " + warnings(c));
		} finally {
			clearCaps();
		}
	}
}
