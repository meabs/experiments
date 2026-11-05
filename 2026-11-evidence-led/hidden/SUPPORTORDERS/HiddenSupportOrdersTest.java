package com.salesmanager.test.shop.hidden;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.junit.jupiter.api.Test;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

/**
 * Hidden acceptance tests for ticket SUPPORTORDERS: orders of deleted customers stay readable and findable by
 * customer id, and the admin order list pages correctly with its filters.
 */
@SuppressWarnings({ "rawtypes", "unchecked" })
public class HiddenSupportOrdersTest extends HiddenOrderSupport {

	// ---- helpers

	private String email() {
		return "sup" + SEQ.incrementAndGet() + "x" + System.nanoTime() % 100000 + "@example.com";
	}

	private Map item(String sku, int qty) {
		Map m = new HashMap();
		m.put("product", sku);
		m.put("quantity", qty);
		return m;
	}

	/** A registered customer's order of qty x 10.00; returns {orderId, customerId}. */
	private long[] customerOrder(HttpHeaders h, String sku, int qty) {
		ResponseEntity<Map> c = testRestTemplate.postForEntity("/api/v1/cart/?store=DEFAULT",
				new HttpEntity<>(item(sku, qty), h), Map.class);
		BigDecimal net = new BigDecimal("10.00").multiply(new BigDecimal(qty)).setScale(2);
		BigDecimal gross = net.multiply(new BigDecimal("1.13")).setScale(2, java.math.RoundingMode.HALF_UP);
		ResponseEntity<String> co = customerCheckout(h, (String) c.getBody().get("code"), gross.toPlainString(),
				net.toPlainString());
		assertTrue(co.getStatusCode().is2xxSuccessful(), "customer checkout: " + co.getStatusCode());
		Map body;
		try {
			body = new com.fasterxml.jackson.databind.ObjectMapper().readValue(co.getBody(), Map.class);
		} catch (Exception e) {
			throw new AssertionError(e);
		}
		long orderId = ((Number) body.get("id")).longValue();
		long customerId = ((Number) ((Map) getOrder(orderId).get("customer")).get("id")).longValue();
		return new long[] { orderId, customerId };
	}

	private HttpStatus deleteCustomer(long id) {
		return testRestTemplate.exchange("/api/v1/private/customer/" + id + "?store=DEFAULT", HttpMethod.DELETE,
				new HttpEntity<>(getHeader()), String.class).getStatusCode();
	}

	private ResponseEntity<Map> list(String query) {
		return testRestTemplate.exchange("/api/v1/private/orders?store=DEFAULT" + query, HttpMethod.GET,
				new HttpEntity<>(getHeader()), Map.class);
	}

	private ResponseEntity<Map> byCustomer(long customerId) {
		return testRestTemplate.exchange("/api/v1/private/orders/customers/" + customerId + "?store=DEFAULT",
				HttpMethod.GET, new HttpEntity<>(getHeader()), Map.class);
	}

	private static List<Long> ids(Map list) {
		List<Long> out = new ArrayList<>();
		if (list != null && list.get("orders") != null) {
			for (Object o : (List) list.get("orders")) {
				out.add(((Number) ((Map) o).get("id")).longValue());
			}
		}
		return out;
	}

	private static int number(Map m, String key) {
		return ((Number) m.get(key)).intValue();
	}

	/** n guest orders placed with the same email; ids in the order placed. */
	private List<Long> guestOrders(String email, int n) {
		String a = uniqueSku("sgo");
		createProduct(a, "4.00", 100);
		List<Long> ids = new ArrayList<>();
		for (int i = 0; i < n; i++) {
			ResponseEntity<Map> r = checkoutCart(cartWith(lines(a, 1)), email);
			ids.add(((Number) r.getBody().get("id")).longValue());
		}
		return ids;
	}

	// ---- tests

	@Test
	public void aDeletedCustomersOrderOpensAsBefore() {
		ensureTax();
		String a = uniqueSku("sda");
		createProduct(a, "10.00", 50);
		String email = email();
		HttpHeaders h = registerAndLogin(email, "Passw0rd!s");
		long[] ids = customerOrder(h, a, 2);
		Map before = getOrder(ids[0]);
		assertTrue(deleteCustomer(ids[1]).is2xxSuccessful());
		ResponseEntity<Map> r = testRestTemplate.exchange("/api/v1/private/orders/" + ids[0] + "?store=DEFAULT",
				HttpMethod.GET, new HttpEntity<>(getHeader()), Map.class);
		assertEquals(HttpStatus.OK, r.getStatusCode());
		Map after = r.getBody();
		assertEquals(before.get("totals"), after.get("totals"));
		assertEquals(((Map) before.get("billing")).get("address"), ((Map) after.get("billing")).get("address"));
		assertEquals(((Map) before.get("delivery")).get("city"), ((Map) after.get("delivery")).get("city"));
		assertEquals(email, ((Map) after.get("billing")).get("email"));
		assertNull(after.get("customer"), "the order has no customer any more");
	}

	@Test
	public void aDeletedCustomersOrderCanStillBeWorkedOn() {
		ensureTax();
		String a = uniqueSku("sdb");
		createProduct(a, "10.00", 50);
		HttpHeaders h = registerAndLogin(email(), "Passw0rd!s");
		long[] ids = customerOrder(h, a, 1);
		assertTrue(deleteCustomer(ids[1]).is2xxSuccessful());
		ResponseEntity<String> s = testRestTemplate.exchange("/api/v1/private/orders/" + ids[0] + "/status?store=DEFAULT",
				HttpMethod.PUT, new HttpEntity<>("PROCESSED", getHeader()), String.class);
		assertTrue(s.getStatusCode().is2xxSuccessful());
		assertEquals("PROCESSED", getOrder(ids[0]).get("orderStatus"));
		assertEquals(HttpStatus.OK, testRestTemplate.exchange("/api/v1/private/orders/" + ids[0] + "/history?store=DEFAULT",
				HttpMethod.GET, new HttpEntity<>(getHeader()), String.class).getStatusCode());
		assertEquals(HttpStatus.OK, testRestTemplate.exchange(
				"/api/v1/private/orders/" + ids[0] + "/payment/transactions?store=DEFAULT", HttpMethod.GET,
				new HttpEntity<>(getHeader()), String.class).getStatusCode());
	}

	@Test
	public void aDeletedCustomersOrdersCanBeLookedUpByTheirId() {
		ensureTax();
		String a = uniqueSku("sdc");
		createProduct(a, "10.00", 50);
		HttpHeaders h = registerAndLogin(email(), "Passw0rd!s");
		long[] first = customerOrder(h, a, 1);
		long[] second = customerOrder(h, a, 2);
		assertTrue(deleteCustomer(first[1]).is2xxSuccessful());
		ResponseEntity<Map> r = byCustomer(first[1]);
		assertEquals(HttpStatus.OK, r.getStatusCode());
		List<Long> found = ids(r.getBody());
		assertEquals(2, found.size(), "both orders: " + found);
		assertEquals(Long.valueOf(second[0]), found.get(0), "newest first");
		assertEquals(2, number(r.getBody(), "recordsTotal"));
	}

	@Test
	public void aLiveCustomersOrdersAreListedWithTheirCount() {
		ensureTax();
		String a = uniqueSku("sdd");
		createProduct(a, "10.00", 50);
		HttpHeaders h = registerAndLogin(email(), "Passw0rd!s");
		long[] first = customerOrder(h, a, 1);
		customerOrder(h, a, 1);
		customerOrder(h, a, 3);
		ResponseEntity<Map> r = byCustomer(first[1]);
		assertEquals(HttpStatus.OK, r.getStatusCode());
		assertEquals(3, ids(r.getBody()).size());
		assertEquals(3, number(r.getBody(), "recordsTotal"));
	}

	@Test
	public void anIdWithNoOrdersGivesAnEmptyList() {
		ResponseEntity<Map> r = byCustomer(987654321L);
		assertEquals(HttpStatus.OK, r.getStatusCode());
		assertEquals(0, ids(r.getBody()).size());
		assertEquals(0, number(r.getBody(), "recordsTotal"));
	}

	@Test
	public void laterPagesOfTheOrderListShowTheOlderOrders() {
		String email = email();
		List<Long> placed = guestOrders(email, 5);
		List<Long> seen = new ArrayList<>();
		for (int p = 0; p < 3; p++) {
			ResponseEntity<Map> r = list("&email=" + email + "&count=2&page=" + p);
			assertEquals(HttpStatus.OK, r.getStatusCode());
			assertEquals(5, number(r.getBody(), "recordsTotal"), "page " + p);
			assertEquals(3, number(r.getBody(), "totalPages"), "page " + p);
			List<Long> page = ids(r.getBody());
			assertEquals(p < 2 ? 2 : 1, page.size(), "orders on page " + p + ": " + page);
			seen.addAll(page);
		}
		List<Long> newestFirst = new ArrayList<>(placed);
		java.util.Collections.reverse(newestFirst);
		assertEquals(newestFirst, seen, "every order once, newest first across the pages");
	}

	@Test
	public void aPageAfterTheLastIsEmptyWithTheSameTotals() {
		String email = email();
		guestOrders(email, 3);
		ResponseEntity<Map> r = list("&email=" + email + "&count=2&page=5");
		assertEquals(HttpStatus.OK, r.getStatusCode());
		assertEquals(0, ids(r.getBody()).size());
		assertEquals(3, number(r.getBody(), "recordsTotal"));
		assertEquals(2, number(r.getBody(), "totalPages"));
	}

	@Test
	public void pagingCombinesWithTheStatusFilter() {
		String email = email();
		List<Long> placed = guestOrders(email, 4);
		for (int i = 0; i < 3; i++) {
			testRestTemplate.exchange("/api/v1/private/orders/" + placed.get(i) + "/status?store=DEFAULT", HttpMethod.PUT,
					new HttpEntity<>("PROCESSED", getHeader()), String.class);
		}
		ResponseEntity<Map> p0 = list("&email=" + email + "&status=PROCESSED&count=2&page=0");
		ResponseEntity<Map> p1 = list("&email=" + email + "&status=PROCESSED&count=2&page=1");
		assertEquals(3, number(p0.getBody(), "recordsTotal"));
		assertEquals(2, number(p0.getBody(), "totalPages"));
		List<Long> all = new ArrayList<>(ids(p0.getBody()));
		all.addAll(ids(p1.getBody()));
		assertEquals(3, all.size(), "the processed orders across both pages: " + all);
		assertFalse(all.contains(placed.get(3)), "the order still ORDERED is not listed");
	}

	@Test
	public void theFirstPageIsAsBefore() {
		String email = email();
		List<Long> placed = guestOrders(email, 2);
		ResponseEntity<Map> r = list("&email=" + email);
		assertEquals(HttpStatus.OK, r.getStatusCode());
		assertEquals(2, number(r.getBody(), "recordsTotal"));
		assertTrue(ids(r.getBody()).containsAll(placed));
	}

	@Test
	public void reRegisteringADeletedEmailStartsAFreshAccount() {
		ensureTax();
		String a = uniqueSku("sde");
		createProduct(a, "10.00", 50);
		String email = email();
		HttpHeaders old = registerAndLogin(email, "Passw0rd!s");
		long[] ids = customerOrder(old, a, 1);
		assertTrue(deleteCustomer(ids[1]).is2xxSuccessful());
		HttpHeaders fresh = registerAndLogin(email, "Passw0rd!t");
		ResponseEntity<Map> mine = testRestTemplate.exchange("/api/v1/auth/orders?store=DEFAULT", HttpMethod.GET,
				new HttpEntity<>(fresh), Map.class);
		assertEquals(HttpStatus.OK, mine.getStatusCode());
		assertFalse(ids(mine.getBody()).contains(ids[0]), "the new account doesn't see the old orders");
		assertEquals(HttpStatus.OK, testRestTemplate.exchange("/api/v1/private/orders/" + ids[0] + "?store=DEFAULT",
				HttpMethod.GET, new HttpEntity<>(getHeader()), String.class).getStatusCode());
	}

	@Test
	public void anExactNumberOfPagesHasNoEmptyExtraPage() {
		String email = email();
		guestOrders(email, 4);
		ResponseEntity<Map> r = list("&email=" + email + "&count=2&page=0");
		assertEquals(4, number(r.getBody(), "recordsTotal"));
		assertEquals(2, number(r.getBody(), "totalPages"), "4 orders, 2 a page");
	}

	@Test
	public void pagesOfOneOrderEach() {
		String email = email();
		List<Long> placed = guestOrders(email, 3);
		for (int p = 0; p < 3; p++) {
			ResponseEntity<Map> r = list("&email=" + email + "&count=1&page=" + p);
			assertEquals(HttpStatus.OK, r.getStatusCode());
			assertEquals(java.util.Collections.singletonList(placed.get(2 - p)), ids(r.getBody()), "page " + p);
			assertEquals(3, number(r.getBody(), "recordsTotal"));
			assertEquals(3, number(r.getBody(), "totalPages"));
		}
	}
}
