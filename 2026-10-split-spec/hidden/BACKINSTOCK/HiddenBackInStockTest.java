package com.salesmanager.test.shop.hidden;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

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
 * Hidden acceptance test for feature BACKINSTOCK: shoppers ask to be told when an out-of-stock product is back, and
 * raising its stock sends the alerts to the store's outbox. Stock is changed through the existing inventory API.
 */
@SuppressWarnings({ "rawtypes", "unchecked" })
public class HiddenBackInStockTest extends ServicesTestSupport {

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

	private P newProduct(int quantity) {
		String sku = "bis" + SEQ.incrementAndGet() + "x" + System.nanoTime() % 100000;
		PersistableProduct p = product(sku);
		p.setSku(sku);
		p.setQuantity(quantity);
		p.getInventory().setQuantity(quantity);
		ResponseEntity<Entity> r = testRestTemplate.postForEntity("/api/v1/private/product?store=DEFAULT",
				new HttpEntity<>(p, getHeader()), Entity.class);
		assertEquals(HttpStatus.CREATED, r.getStatusCode(), "creating product " + sku);
		return new P(r.getBody().getId(), sku);
	}

	private String email() {
		return "shopper" + SEQ.incrementAndGet() + "_" + System.nanoTime() % 1000000 + "@example.com";
	}

	private HttpHeaders anonymous() {
		HttpHeaders h = new HttpHeaders();
		h.setContentType(MediaType.APPLICATION_JSON);
		return h;
	}

	private static Map<String, Object> body(Object email) {
		Map<String, Object> b = new HashMap<>();
		if (email != null) {
			b.put("email", email);
		}
		return b;
	}

	private ResponseEntity<Map> subscribe(String sku, String email) {
		return testRestTemplate.exchange("/api/v1/products/" + sku + "/alerts?store=DEFAULT", HttpMethod.POST,
				new HttpEntity<>(body(email), anonymous()), Map.class);
	}

	private HttpStatus subscribeStatus(String sku, Object email) {
		return testRestTemplate.exchange("/api/v1/products/" + sku + "/alerts?store=DEFAULT", HttpMethod.POST,
				new HttpEntity<>(body(email), anonymous()), String.class).getStatusCode();
	}

	private HttpStatus unsubscribe(String sku, String email) {
		return testRestTemplate.exchange("/api/v1/products/" + sku + "/alerts?store=DEFAULT&email=" + email, HttpMethod.DELETE,
				new HttpEntity<>(anonymous()), String.class).getStatusCode();
	}

	private List<Map> alerts(String query, String sku) {
		ResponseEntity<List> r = testRestTemplate.exchange("/api/v1/private/stock-alerts?store=DEFAULT" + query, HttpMethod.GET,
				new HttpEntity<>(getHeader()), List.class);
		assertEquals(HttpStatus.OK, r.getStatusCode());
		List<Map> out = new ArrayList<>();
		for (Map a : (List<Map>) r.getBody()) {
			if (sku.equals(a.get("sku"))) {
				out.add(a);
			}
		}
		return out;
	}

	private List<Map> outbox(String sku) {
		ResponseEntity<List> r = testRestTemplate.exchange("/api/v1/private/stock-alerts/outbox?store=DEFAULT", HttpMethod.GET,
				new HttpEntity<>(getHeader()), List.class);
		assertEquals(HttpStatus.OK, r.getStatusCode());
		List<Map> out = new ArrayList<>();
		for (Map m : (List<Map>) r.getBody()) {
			if (sku.equals(m.get("sku"))) {
				out.add(m);
			}
		}
		return out;
	}

	/** Sets the product's stock through the existing inventory API (its first inventory entry, listed by sku). */
	private void setStock(P p, int quantity) {
		ResponseEntity<Map> inv = testRestTemplate.exchange("/api/v1/private/product/" + p.sku + "/inventory?store=DEFAULT",
				HttpMethod.GET, new HttpEntity<>(getHeader()), Map.class);
		assertEquals(HttpStatus.OK, inv.getStatusCode());
		List<Map> items = (List<Map>) inv.getBody().get("items");
		assertTrue(items != null && !items.isEmpty(), "inventory for " + p.sku + ": " + inv.getBody());
		long inventoryId = ((Number) items.get(0).get("id")).longValue();
		Map<String, Object> b = new HashMap<>();
		b.put("productId", p.id);
		b.put("quantity", quantity);
		b.put("available", true);
		ResponseEntity<String> r = testRestTemplate.exchange("/api/v1/private/product/" + p.id + "/inventory/" + inventoryId
				+ "?store=DEFAULT", HttpMethod.PUT, new HttpEntity<>(b, getHeader()), String.class);
		assertTrue(r.getStatusCode().is2xxSuccessful(), "setting stock of " + p.sku + " to " + quantity + ": " + r.getStatusCode()
				+ " " + r.getBody());
	}

	// ---- subscribing

	@Test
	public void aShopperCanAskForAnOutOfStockProductWithoutLoggingIn() {
		P p = newProduct(0);
		String e = email();
		ResponseEntity<Map> r = subscribe(p.sku, e);
		assertEquals(HttpStatus.CREATED, r.getStatusCode());
		assertEquals(p.sku, r.getBody().get("sku"));
		assertEquals(e, r.getBody().get("email"));
		assertEquals("PENDING", r.getBody().get("status"));
		List<Map> l = alerts("", p.sku);
		assertEquals(1, l.size(), "alerts: " + l);
		assertEquals("PENDING", l.get(0).get("status"));
		assertEquals(e, l.get(0).get("email"));
		assertNotNull(l.get(0).get("id"));
		assertNotNull(l.get(0).get("createdAt"));
		assertNull(l.get(0).get("sentAt"));
	}

	@Test
	public void aProductInStockCannotBeAskedFor() {
		P p = newProduct(5);
		assertEquals(HttpStatus.CONFLICT, subscribeStatus(p.sku, email()));
		assertTrue(alerts("", p.sku).isEmpty());
	}

	@Test
	public void invalidRequests() {
		P p = newProduct(0);
		assertEquals(HttpStatus.BAD_REQUEST, subscribeStatus(p.sku, null));
		assertEquals(HttpStatus.BAD_REQUEST, subscribeStatus(p.sku, ""));
		assertEquals(HttpStatus.BAD_REQUEST, subscribeStatus(p.sku, "not-an-email"));
		assertEquals(HttpStatus.NOT_FOUND, subscribeStatus("no-such-sku-" + System.nanoTime(), email()));
		assertTrue(alerts("", p.sku).isEmpty());
	}

	@Test
	public void askingTwiceIgnoringCaseKeepsOneAlert() {
		P p = newProduct(0);
		String e = email();
		assertEquals(HttpStatus.CREATED, subscribe(p.sku, e).getStatusCode());
		assertEquals(HttpStatus.OK, subscribe(p.sku, e.toUpperCase()).getStatusCode());
		assertEquals(1, alerts("", p.sku).size());
	}

	@Test
	public void cancellingAnAlert() {
		P p = newProduct(0);
		String e = email(), keep = email();
		subscribe(p.sku, e);
		subscribe(p.sku, keep);
		assertEquals(HttpStatus.NO_CONTENT, unsubscribe(p.sku, e));
		List<Map> l = alerts("", p.sku);
		assertEquals(1, l.size());
		assertEquals(keep, l.get(0).get("email"));
		assertEquals(HttpStatus.NOT_FOUND, unsubscribe(p.sku, e));
	}

	// ---- sending

	@Test
	public void restockingSendsEveryPendingAlert() {
		P p = newProduct(0);
		String a = email(), b = email();
		subscribe(p.sku, a);
		subscribe(p.sku, b);
		setStock(p, 5);
		List<Map> l = alerts("", p.sku);
		assertEquals(2, l.size());
		for (Map x : l) {
			assertEquals("SENT", x.get("status"), "alert " + x);
			assertNotNull(x.get("sentAt"), "sentAt of " + x);
		}
		List<Map> m = outbox(p.sku);
		assertEquals(2, m.size(), "outbox: " + m);
		List<Object> to = new ArrayList<>();
		for (Map x : m) {
			to.add(x.get("to"));
			assertEquals(p.sku + " is back in stock", x.get("subject"));
		}
		assertTrue(to.contains(a) && to.contains(b), "sent to " + to);
	}

	@Test
	public void restockingOneProductLeavesOthersPending() {
		P p = newProduct(0), q = newProduct(0);
		subscribe(p.sku, email());
		subscribe(q.sku, email());
		setStock(p, 3);
		assertEquals("PENDING", alerts("", q.sku).get(0).get("status"));
		assertTrue(outbox(q.sku).isEmpty());
	}

	@Test
	public void stockThatStaysAtZeroSendsNothing() {
		P p = newProduct(0);
		subscribe(p.sku, email());
		setStock(p, 0);
		assertEquals("PENDING", alerts("", p.sku).get(0).get("status"));
		assertTrue(outbox(p.sku).isEmpty());
	}

	@Test
	public void eachAlertIsSentOnce() {
		P p = newProduct(0);
		subscribe(p.sku, email());
		setStock(p, 2);
		setStock(p, 9);
		assertEquals(1, outbox(p.sku).size());
	}

	@Test
	public void afterSellingOutAgainAShopperCanAskAgain() {
		P p = newProduct(0);
		String e = email();
		subscribe(p.sku, e);
		setStock(p, 4);
		setStock(p, 0);
		assertEquals(HttpStatus.CREATED, subscribe(p.sku, e).getStatusCode());
		assertEquals(1, alerts("&status=PENDING", p.sku).size());
		assertEquals(1, alerts("&status=SENT", p.sku).size());
		setStock(p, 1);
		assertEquals(2, outbox(p.sku).size());
		assertEquals(2, alerts("&status=SENT", p.sku).size());
	}

	// ---- admin

	@Test
	public void theAlertListFiltersByStatus() {
		P p = newProduct(0), q = newProduct(0);
		subscribe(p.sku, email());
		subscribe(q.sku, email());
		setStock(q, 1);
		assertEquals(1, alerts("&status=PENDING", p.sku).size());
		assertTrue(alerts("&status=SENT", p.sku).isEmpty());
		assertEquals(1, alerts("&status=SENT", q.sku).size());
		assertTrue(alerts("&status=PENDING", q.sku).isEmpty());
		assertEquals(HttpStatus.BAD_REQUEST, testRestTemplate.exchange("/api/v1/private/stock-alerts?store=DEFAULT&status=LOST",
				HttpMethod.GET, new HttpEntity<>(getHeader()), String.class).getStatusCode());
	}

	@Test
	public void alertsAndOutboxNeedAnAdmin() {
		for (String u : new String[] { "/api/v1/private/stock-alerts?store=DEFAULT", "/api/v1/private/stock-alerts/outbox?store=DEFAULT" }) {
			HttpStatus s = testRestTemplate.exchange(u, HttpMethod.GET, new HttpEntity<>(anonymous()), String.class).getStatusCode();
			assertTrue(s == HttpStatus.UNAUTHORIZED || s == HttpStatus.FORBIDDEN, u + " without a token: " + s);
		}
	}

	@Test
	public void aProductWithAlertsCanStillBeDeleted() {
		P p = newProduct(0);
		subscribe(p.sku, email());
		ResponseEntity<String> d = testRestTemplate.exchange("/api/v1/private/product/" + p.id + "?store=DEFAULT",
				HttpMethod.DELETE, new HttpEntity<>(getHeader()), String.class);
		assertTrue(d.getStatusCode().is2xxSuccessful(), "deleting the product: " + d.getStatusCode());
		assertTrue(alerts("", p.sku).isEmpty(), "alerts of a deleted product");
	}
}
