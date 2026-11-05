package com.salesmanager.test.shop.hidden;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
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
 * Hidden acceptance tests for ticket CUSTOMERCART: a logged-in customer's carts are theirs and findable, their cart
 * total includes tax, logged-in checkout names the right amount, and their order list counts correctly.
 * Every order here is delivered in Ontario, where the hidden set-up charges 13% tax.
 */
@SuppressWarnings({ "rawtypes", "unchecked" })
public class HiddenCustomerCartTest extends HiddenOrderSupport {

	// ---- helpers

	private HttpHeaders customerNow() {
		ensureTax();
		return registerAndLogin("cc" + SEQ.incrementAndGet() + "x" + System.nanoTime() % 100000 + "@example.com",
				"Passw0rd!c");
	}

	private Map item(String sku, int qty) {
		Map m = new HashMap();
		m.put("product", sku);
		m.put("quantity", qty);
		return m;
	}

	private Map newCart(HttpHeaders h, String sku, int qty) {
		ResponseEntity<Map> r = testRestTemplate.postForEntity("/api/v1/cart/?store=DEFAULT",
				new HttpEntity<>(item(sku, qty), h), Map.class);
		assertEquals(HttpStatus.CREATED, r.getStatusCode(), "creating a cart");
		return r.getBody();
	}

	private ResponseEntity<Map> current(HttpHeaders h) {
		return testRestTemplate.exchange("/api/v1/auth/customer/cart?store=DEFAULT", HttpMethod.GET, new HttpEntity<>(h),
				Map.class);
	}

	private ResponseEntity<Map> total(HttpHeaders h, Object cartId) {
		return testRestTemplate.exchange("/api/v1/auth/cart/" + cartId + "/total?store=DEFAULT", HttpMethod.GET,
				new HttpEntity<>(h), Map.class);
	}

	private static BigDecimal line(Map summary, String module) {
		BigDecimal sum = null;
		for (Object o : (List) summary.get("totals")) {
			Map t = (Map) o;
			if (module.equals(t.get("module"))) {
				sum = (sum == null ? BigDecimal.ZERO.setScale(2) : sum).add(money(t.get("value")));
			}
		}
		return sum;
	}

	private ResponseEntity<String> checkout(HttpHeaders h, String code, String amount) {
		ensurePayment();
		fillers();
		Map pay = new HashMap();
		pay.put("paymentModule", "moneyorder");
		pay.put("paymentType", "MONEYORDER");
		pay.put("transactionType", "AUTHORIZECAPTURE");
		pay.put("amount", amount);
		Map order = new HashMap();
		order.put("payment", pay);
		order.put("currency", "CAD");
		return testRestTemplate.postForEntity("/api/v1/auth/cart/" + code + "/checkout?store=DEFAULT",
				new HttpEntity<>(order, h), String.class);
	}

	private Map orders(HttpHeaders h, String query) {
		ResponseEntity<Map> r = testRestTemplate.exchange("/api/v1/auth/orders?store=DEFAULT" + query, HttpMethod.GET,
				new HttpEntity<>(h), Map.class);
		assertEquals(HttpStatus.OK, r.getStatusCode());
		return r.getBody();
	}

	private static List<Long> ids(Map list) {
		List<Long> out = new ArrayList<>();
		Object orders = list.get("orders");
		if (orders != null) {
			for (Object o : (List) orders) {
				out.add(((Number) ((Map) o).get("id")).longValue());
			}
		}
		return out;
	}

	/** One order for the customer: a cart of qty x 10.00, paid at 13% tax. */
	private void order(HttpHeaders h, String sku, int qty) {
		Map cart = newCart(h, sku, qty);
		BigDecimal amount = new BigDecimal("10.00").multiply(new BigDecimal(qty)).multiply(new BigDecimal("1.13"))
				.setScale(2, java.math.RoundingMode.HALF_UP);
		ResponseEntity<String> r = customerCheckout(h, (String) cart.get("code"), amount.toPlainString(),
				new BigDecimal("10.00").multiply(new BigDecimal(qty)).setScale(2).toPlainString());
		assertTrue(r.getStatusCode().is2xxSuccessful(), "customer checkout: " + r.getStatusCode() + " " + r.getBody());
	}

	// ---- tests

	@Test
	public void aCartFilledWhileLoggedInIsFoundWithoutItsCode() {
		String a = uniqueSku("cca");
		createProduct(a, "10.00", 50);
		HttpHeaders h = customerNow();
		Map cart = newCart(h, a, 2);
		ResponseEntity<Map> r = current(h);
		assertEquals(HttpStatus.OK, r.getStatusCode());
		assertEquals(cart.get("code"), r.getBody().get("code"));
	}

	@Test
	public void aCartChangedWhileLoggedInIsTheirs() {
		String a = uniqueSku("ccb");
		String b = uniqueSku("ccc");
		createProduct(a, "10.00", 50);
		createProduct(b, "10.00", 50);
		HttpHeaders h = customerNow();
		String code = cartWith(lines(a, 1));
		ResponseEntity<Map> put = testRestTemplate.exchange("/api/v1/cart/" + code + "?store=DEFAULT", HttpMethod.PUT,
				new HttpEntity<>(item(b, 3), h), Map.class);
		assertTrue(put.getStatusCode().is2xxSuccessful());
		ResponseEntity<Map> r = current(h);
		assertEquals(HttpStatus.OK, r.getStatusCode());
		assertEquals(code, r.getBody().get("code"));
	}

	@Test
	public void theCurrentCartIsTheMostRecentOne() {
		String a = uniqueSku("ccd");
		createProduct(a, "10.00", 50);
		HttpHeaders h = customerNow();
		newCart(h, a, 1);
		Map second = newCart(h, a, 2);
		assertEquals(second.get("code"), current(h).getBody().get("code"));
	}

	@Test
	public void aCustomerWithNoCartGetsNotFound() {
		HttpHeaders h = customerNow();
		assertEquals(HttpStatus.NOT_FOUND, current(h).getStatusCode());
	}

	@Test
	public void aCustomerNeverGetsAnotherCustomersCart() {
		String a = uniqueSku("cce");
		createProduct(a, "10.00", 50);
		HttpHeaders one = customerNow();
		HttpHeaders two = customerNow();
		Map cart = newCart(one, a, 1);
		ResponseEntity<Map> r = current(two);
		assertTrue(r.getStatusCode() == HttpStatus.NOT_FOUND || !cart.get("code").equals(r.getBody().get("code")));
		assertEquals(HttpStatus.NOT_FOUND, total(two, cart.get("id")).getStatusCode());
	}

	@Test
	public void theCartTotalIncludesTaxForTheDeliveryAddress() {
		String a = uniqueSku("ccf");
		createProduct(a, "10.00", 50);
		HttpHeaders h = customerNow();
		Map cart = newCart(h, a, 2);
		ResponseEntity<Map> r = total(h, cart.get("id"));
		assertEquals(HttpStatus.OK, r.getStatusCode());
		assertEquals(m("20.00"), line(r.getBody(), "subtotal"));
		assertEquals(m("2.60"), line(r.getBody(), "tax"));
		assertEquals(m("22.60"), line(r.getBody(), "total"));
	}

	@Test
	public void checkoutChargesWhatTheTotalSaid() {
		String a = uniqueSku("ccg");
		createProduct(a, "10.00", 50);
		HttpHeaders h = customerNow();
		Map cart = newCart(h, a, 3);
		BigDecimal said = line(total(h, cart.get("id")).getBody(), "total");
		assertNotNull(said);
		ResponseEntity<String> r = checkout(h, (String) cart.get("code"), said.toPlainString());
		assertTrue(r.getStatusCode().is2xxSuccessful(), "checkout at the total's amount: " + r.getStatusCode());
	}

	@Test
	public void aWrongAmountIsRefusedNamingTheRightOne() {
		String a = uniqueSku("cch");
		createProduct(a, "10.00", 50);
		HttpHeaders h = customerNow();
		Map cart = newCart(h, a, 2);
		ResponseEntity<String> r = checkout(h, (String) cart.get("code"), "1.00");
		assertEquals(HttpStatus.BAD_REQUEST, r.getStatusCode());
		assertTrue(String.valueOf(r.getBody()).contains("22.60"), "the message names 22.60: " + r.getBody());
		assertEquals(0, ids(orders(h, "")).size(), "nothing is ordered");
	}

	@Test
	public void aCheckedOutCartIsNoLongerTheCurrentOne() {
		String a = uniqueSku("cci");
		createProduct(a, "10.00", 50);
		HttpHeaders h = customerNow();
		Map cart = newCart(h, a, 1);
		assertEquals(cart.get("code"), current(h).getBody().get("code"), "the cart is current before checkout");
		ResponseEntity<String> r = checkout(h, (String) cart.get("code"), "11.30");
		assertTrue(r.getStatusCode().is2xxSuccessful(), "checkout: " + r.getStatusCode());
		assertEquals(HttpStatus.NOT_FOUND, current(h).getStatusCode());
	}

	@Test
	public void theOrderListCountsTheCustomersOrders() {
		String a = uniqueSku("ccj");
		createProduct(a, "10.00", 50);
		HttpHeaders h = customerNow();
		order(h, a, 1);
		order(h, a, 2);
		order(h, a, 1);
		Map all = orders(h, "&count=10");
		assertEquals(3, ((Number) all.get("recordsTotal")).intValue());
		assertEquals(1, ((Number) all.get("totalPages")).intValue());
		Map paged = orders(h, "&count=2&page=0");
		assertEquals(3, ((Number) paged.get("recordsTotal")).intValue());
		assertEquals(2, ((Number) paged.get("totalPages")).intValue());
	}

	@Test
	public void theOrderListHasOnlyTheirOwnOrdersNewestFirst() {
		String a = uniqueSku("cck");
		createProduct(a, "10.00", 50);
		HttpHeaders one = customerNow();
		HttpHeaders two = customerNow();
		order(one, a, 1);
		order(two, a, 1);
		order(one, a, 2);
		List<Long> mine = ids(orders(one, ""));
		List<Long> theirs = ids(orders(two, ""));
		assertEquals(2, mine.size());
		assertEquals(1, theirs.size());
		assertFalse(mine.contains(theirs.get(0)));
		assertTrue(mine.get(0) > mine.get(1), "newest first: " + mine);
	}
}
