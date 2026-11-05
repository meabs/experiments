package com.salesmanager.test.shop.hidden;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.math.BigDecimal;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.junit.jupiter.api.Test;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import com.salesmanager.shop.model.catalog.product.PersistableProductPrice;
import com.salesmanager.shop.model.catalog.product.ProductDescription;
import com.salesmanager.shop.model.catalog.product.product.PersistableProduct;
import com.salesmanager.shop.model.catalog.product.product.PersistableProductInventory;
import com.salesmanager.shop.model.entity.Entity;

/**
 * Hidden acceptance tests for ticket STOCK: checkout takes stock from the products ordered (and no others), refuses
 * what can't be filled, carts can't hold more than stock, cancelling restocks once, and no-stock products show as
 * unavailable.
 */
@SuppressWarnings({ "rawtypes", "unchecked" })
public class HiddenStockTest extends HiddenOrderSupport {

	private static final Pattern CALCULATED = Pattern.compile("calculated ([0-9]+(?:\\.[0-9]+)?)");

	// ---- helpers

	private Map item(String sku, int qty) {
		Map m = new HashMap();
		m.put("product", sku);
		m.put("quantity", qty);
		return m;
	}

	/** Checkout that reports the final status instead of failing: pays what the shop calculates. */
	private HttpStatus checkoutStatus(String cartCode) {
		ensurePayment();
		fillers();
		String amount = "0";
		HttpStatus last = null;
		for (int attempt = 0; attempt < 2; attempt++) {
			Map pay = new HashMap();
			pay.put("paymentModule", "moneyorder");
			pay.put("paymentType", "MONEYORDER");
			pay.put("transactionType", "AUTHORIZECAPTURE");
			pay.put("amount", amount);
			Map order = new HashMap();
			order.put("customer", customer("stock" + SEQ.incrementAndGet() + "@example.com"));
			order.put("payment", pay);
			order.put("currency", "CAD");
			ResponseEntity<String> r = testRestTemplate.postForEntity("/api/v1/cart/" + cartCode + "/checkout?store=DEFAULT",
					new HttpEntity<>(order, getHeader()), String.class);
			last = r.getStatusCode();
			Matcher m = CALCULATED.matcher(String.valueOf(r.getBody()));
			if (r.getStatusCode().is2xxSuccessful() || !m.find()) {
				return last;
			}
			amount = m.group(1);
		}
		return last;
	}

	private Map<String, Integer> cartQuantities(String code) {
		ResponseEntity<Map> r = testRestTemplate.exchange("/api/v1/cart/" + code + "?store=DEFAULT", HttpMethod.GET,
				new HttpEntity<>(getHeader()), Map.class);
		assertEquals(HttpStatus.OK, r.getStatusCode(), "reading cart " + code);
		Map<String, Integer> q = new LinkedHashMap<>();
		Object products = r.getBody().get("products");
		if (products != null) {
			for (Object o : (List) products) {
				Map p = (Map) o;
				q.put((String) p.get("sku"), ((Number) p.get("quantity")).intValue());
			}
		}
		return q;
	}

	private long orderCount() {
		ResponseEntity<Map> r = testRestTemplate.exchange("/api/v1/private/orders?store=DEFAULT&count=1000", HttpMethod.GET,
				new HttpEntity<>(getHeader()), Map.class);
		assertEquals(HttpStatus.OK, r.getStatusCode());
		return ((Number) r.getBody().get("recordsTotal")).longValue();
	}

	private HttpStatus setStatus(long orderId, String status) {
		return testRestTemplate.exchange("/api/v1/private/orders/" + orderId + "/status?store=DEFAULT", HttpMethod.PUT,
				new HttpEntity<>(status, getHeader()), String.class).getStatusCode();
	}

	private Map readProduct(String sku) {
		ResponseEntity<Map> r = testRestTemplate.exchange("/api/v2/product/" + sku + "?store=DEFAULT", HttpMethod.GET,
				new HttpEntity<>(getHeader()), Map.class);
		assertEquals(HttpStatus.OK, r.getStatusCode(), "reading product " + sku);
		return r.getBody();
	}

	/** A few products made first, so that product ids and order line ids don't line up by chance. */
	private void spread() {
		for (int i = 0; i < 3; i++) {
			createProduct(uniqueSku("spread"), "1.00", 100);
		}
	}

	// ---- tests

	@Test
	public void checkoutTakesTheOrderedQuantityFromEachProductOrdered() {
		spread();
		String a = uniqueSku("sta");
		String b = uniqueSku("stb");
		createProduct(a, "10.00", 20);
		createProduct(b, "4.00", 15);
		placeOrder(lines(a, 2, b, 5));
		assertEquals(18, stockOf(a));
		assertEquals(10, stockOf(b));
	}

	@Test
	public void checkoutChangesNoOtherProductsStock() {
		spread();
		String[] others = new String[6];
		for (int i = 0; i < others.length; i++) {
			others[i] = uniqueSku("sto");
			createProduct(others[i], "2.00", 40);
		}
		String a = uniqueSku("stx");
		createProduct(a, "3.00", 30);
		placeOrder(lines(a, 3));
		placeOrder(lines(a, 1));
		assertEquals(26, stockOf(a));
		for (String o : others) {
			assertEquals(40, stockOf(o), "stock of " + o + ", which was not ordered");
		}
	}

	@Test
	public void checkoutIsRefusedWhenStockRanOutAfterTheCartWasFilled() {
		String a = uniqueSku("str");
		createProduct(a, "7.00", 5);
		String first = cartWith(lines(a, 3));
		String second = cartWith(lines(a, 3));
		assertTrue(checkoutStatus(first).is2xxSuccessful(), "the first cart can be filled");
		assertEquals(2, stockOf(a));
		long orders = orderCount();
		assertEquals(HttpStatus.CONFLICT, checkoutStatus(second));
		assertEquals(orders, orderCount(), "no order is created");
		assertEquals(2, stockOf(a), "no stock changes");
		assertEquals(Integer.valueOf(3), cartQuantities(second).get(a), "the cart stays as it was");
	}

	@Test
	public void aRefusedCheckoutTakesNoStockFromTheOtherProducts() {
		String a = uniqueSku("stp");
		String b = uniqueSku("stq");
		createProduct(a, "5.00", 10);
		createProduct(b, "5.00", 2);
		String rival = cartWith(lines(b, 2));
		String cart = cartWith(lines(a, 4, b, 1));
		assertTrue(checkoutStatus(rival).is2xxSuccessful());
		assertEquals(HttpStatus.CONFLICT, checkoutStatus(cart));
		assertEquals(10, stockOf(a));
		assertEquals(0, stockOf(b));
	}

	@Test
	public void aNewCartCantHoldMoreThanTheStock() {
		String a = uniqueSku("stc");
		createProduct(a, "1.00", 3);
		ResponseEntity<String> r = testRestTemplate.postForEntity("/api/v1/cart/?store=DEFAULT",
				new HttpEntity<>(item(a, 4), getHeader()), String.class);
		assertEquals(HttpStatus.CONFLICT, r.getStatusCode());
		ResponseEntity<Map> ok = testRestTemplate.postForEntity("/api/v1/cart/?store=DEFAULT",
				new HttpEntity<>(item(a, 3), getHeader()), Map.class);
		assertEquals(HttpStatus.CREATED, ok.getStatusCode(), "exactly the stock is allowed");
	}

	@Test
	public void changingAQuantityAboveTheStockIsRefusedAndTheCartKept() {
		String a = uniqueSku("stu");
		String b = uniqueSku("stv");
		createProduct(a, "1.00", 4);
		createProduct(b, "1.00", 9);
		String code = cartWith(lines(a, 2, b, 1));
		ResponseEntity<String> r = testRestTemplate.exchange("/api/v1/cart/" + code + "?store=DEFAULT", HttpMethod.PUT,
				new HttpEntity<>(item(a, 5), getHeader()), String.class);
		assertEquals(HttpStatus.CONFLICT, r.getStatusCode());
		Map<String, Integer> q = cartQuantities(code);
		assertEquals(Integer.valueOf(2), q.get(a));
		assertEquals(Integer.valueOf(1), q.get(b));
		ResponseEntity<String> lower = testRestTemplate.exchange("/api/v1/cart/" + code + "?store=DEFAULT", HttpMethod.PUT,
				new HttpEntity<>(item(a, 1), getHeader()), String.class);
		assertTrue(lower.getStatusCode().is2xxSuccessful(), "lowering is always allowed");
		assertEquals(Integer.valueOf(1), cartQuantities(code).get(a));
	}

	@Test
	public void aMultiChangeIsAllOrNothing() {
		String a = uniqueSku("stm");
		String b = uniqueSku("stn");
		createProduct(a, "1.00", 10);
		createProduct(b, "1.00", 2);
		String code = cartWith(lines(a, 1, b, 1));
		ResponseEntity<String> r = testRestTemplate.postForEntity("/api/v1/cart/" + code + "/multi?store=DEFAULT",
				new HttpEntity<>(new Map[] { item(a, 6), item(b, 3) }, getHeader()), String.class);
		assertEquals(HttpStatus.CONFLICT, r.getStatusCode());
		Map<String, Integer> q = cartQuantities(code);
		assertEquals(Integer.valueOf(1), q.get(a), "no change is made when one change is refused");
		assertEquals(Integer.valueOf(1), q.get(b));
		ResponseEntity<String> ok = testRestTemplate.postForEntity("/api/v1/cart/" + code + "/multi?store=DEFAULT",
				new HttpEntity<>(new Map[] { item(a, 6), item(b, 2) }, getHeader()), String.class);
		assertTrue(ok.getStatusCode().is2xxSuccessful());
		q = cartQuantities(code);
		assertEquals(Integer.valueOf(6), q.get(a));
		assertEquals(Integer.valueOf(2), q.get(b));
	}

	@Test
	public void aProductWithNoStockCantBeAdded() {
		String a = uniqueSku("stz");
		String b = uniqueSku("sty");
		createProduct(a, "1.00", 0);
		createProduct(b, "1.00", 5);
		assertEquals(HttpStatus.CONFLICT, testRestTemplate.postForEntity("/api/v1/cart/?store=DEFAULT",
				new HttpEntity<>(item(a, 1), getHeader()), String.class).getStatusCode());
		String code = cartWith(lines(b, 1));
		assertEquals(HttpStatus.CONFLICT, testRestTemplate.exchange("/api/v1/cart/" + code + "?store=DEFAULT",
				HttpMethod.PUT, new HttpEntity<>(item(a, 1), getHeader()), String.class).getStatusCode());
		assertEquals(1, cartQuantities(code).size());
	}

	@Test
	public void cancelingAnOrderPutsTheStockBackOnce() {
		spread();
		String a = uniqueSku("stk");
		String b = uniqueSku("stl");
		createProduct(a, "6.00", 12);
		createProduct(b, "6.00", 12);
		long id = placeOrder(lines(a, 3, b, 4));
		assertEquals(9, stockOf(a));
		assertEquals(8, stockOf(b));
		assertTrue(setStatus(id, "CANCELED").is2xxSuccessful());
		assertEquals(12, stockOf(a));
		assertEquals(12, stockOf(b));
		assertTrue(setStatus(id, "CANCELED").is2xxSuccessful(), "canceling again is allowed but changes nothing");
		assertEquals(12, stockOf(a));
		assertEquals(12, stockOf(b));
	}

	@Test
	public void aCanceledOrderCantBeReopened() {
		String a = uniqueSku("sto2");
		createProduct(a, "6.00", 5);
		long id = placeOrder(lines(a, 2));
		assertTrue(setStatus(id, "CANCELED").is2xxSuccessful());
		assertEquals(5, stockOf(a));
		assertEquals(HttpStatus.CONFLICT, setStatus(id, "ORDERED"));
		assertEquals(HttpStatus.CONFLICT, setStatus(id, "PROCESSED"));
		assertEquals(5, stockOf(a));
		assertEquals("CANCELED", getOrder(id).get("orderStatus"));
	}

	@Test
	public void otherStatusChangesLeaveStockAlone() {
		String a = uniqueSku("sts");
		createProduct(a, "6.00", 10);
		long id = placeOrder(lines(a, 4));
		assertEquals(6, stockOf(a));
		assertTrue(setStatus(id, "PROCESSED").is2xxSuccessful());
		assertTrue(setStatus(id, "DELIVERED").is2xxSuccessful());
		assertEquals(6, stockOf(a));
	}

	@Test
	public void aProductWithNoStockShowsAsUnavailableUntilItHasStockAgain() {
		String a = uniqueSku("stw");
		createProduct(a, "9.00", 2);
		Map before = readProduct(a);
		assertEquals(Boolean.TRUE, before.get("available"));
		long id = placeOrder(lines(a, 2));
		Map empty = readProduct(a);
		assertEquals(0, ((Number) empty.get("quantity")).intValue());
		assertEquals(Boolean.FALSE, empty.get("available"));
		assertEquals(Boolean.FALSE, empty.get("canBePurchased"));
		assertTrue(setStatus(id, "CANCELED").is2xxSuccessful());
		Map again = readProduct(a);
		assertEquals(2, ((Number) again.get("quantity")).intValue());
		assertEquals(Boolean.TRUE, again.get("available"));
		assertEquals(Boolean.TRUE, again.get("canBePurchased"));
	}

	@Test
	public void aProductMarkedUnavailableStaysUnavailable() {
		String sku = uniqueSku("stmk");
		PersistableProduct product = new PersistableProduct();
		PersistableProductInventory inventory = new PersistableProductInventory();
		inventory.setQuantity(10);
		inventory.setSku(sku);
		PersistableProductPrice price = new PersistableProductPrice();
		price.setDefaultPrice(true);
		price.setPrice(new BigDecimal("5.00"));
		inventory.setPrice(price);
		product.setInventory(inventory);
		ProductDescription d = new ProductDescription();
		d.setName(sku);
		d.setLanguage("en");
		product.getDescriptions().add(d);
		product.setSku(sku);
		product.setPrice(new BigDecimal("5.00"));
		product.setQuantity(10);
		product.setAvailable(false);
		ResponseEntity<Entity> r = testRestTemplate.postForEntity("/api/v1/private/product?store=DEFAULT",
				new HttpEntity<>(product, getHeader()), Entity.class);
		assertEquals(HttpStatus.CREATED, r.getStatusCode());
		Map p = readProduct(sku);
		assertEquals(10, ((Number) p.get("quantity")).intValue());
		assertEquals(Boolean.FALSE, p.get("available"));
		assertFalse(Boolean.TRUE.equals(p.get("canBePurchased")));
	}

	@Test
	public void theWholeStockCanBeSoldAndNoMore() {
		String a = uniqueSku("sta2");
		createProduct(a, "2.00", 4);
		placeOrder(lines(a, 1));
		placeOrder(lines(a, 3));
		assertEquals(0, stockOf(a));
		assertEquals(HttpStatus.CONFLICT, testRestTemplate.postForEntity("/api/v1/cart/?store=DEFAULT",
				new HttpEntity<>(item(a, 1), getHeader()), String.class).getStatusCode());
	}

	@Test
	public void checkingOutAsACustomerTakesStockToo() {
		String a = uniqueSku("stcu");
		createProduct(a, "3.00", 10);
		Map c = customer("stockcust" + SEQ.incrementAndGet() + "@example.com");
		String email = (String) c.get("emailAddress");
		c.put("password", "Passw0rd!s");
		c.put("repeatPassword", "Passw0rd!s");
		c.put("storeCode", "DEFAULT");
		c.put("gender", "F");
		ResponseEntity<String> reg = testRestTemplate.postForEntity("/api/v1/customer/register?store=DEFAULT",
				new HttpEntity<>(c, noAuth()), String.class);
		assertTrue(reg.getStatusCode().is2xxSuccessful(), "registering: " + reg.getBody());
		Map login = new HashMap();
		login.put("username", email);
		login.put("password", "Passw0rd!s");
		ResponseEntity<Map> lr = testRestTemplate.postForEntity("/api/v1/customer/login?store=DEFAULT",
				new HttpEntity<>(login, noAuth()), Map.class);
		assertEquals(HttpStatus.OK, lr.getStatusCode());
		org.springframework.http.HttpHeaders h = noAuth();
		h.add("Authorization", "Bearer " + lr.getBody().get("token"));
		ResponseEntity<Map> cart = testRestTemplate.postForEntity("/api/v1/cart/?store=DEFAULT",
				new HttpEntity<>(item(a, 4), h), Map.class);
		assertEquals(HttpStatus.CREATED, cart.getStatusCode());
		String code = (String) cart.getBody().get("code");
		ensurePayment();
		ensureTax();
		// 4 x 3.00, with or without the 13% tax: this ticket is not about tax, and logged-in checkout doesn't name the
		// right amount when it is given a wrong one
		String[] amounts = { "12.00", "13.56" };
		ResponseEntity<String> r = null;
		for (String amount : amounts) {
			Map pay = new HashMap();
			pay.put("paymentModule", "moneyorder");
			pay.put("paymentType", "MONEYORDER");
			pay.put("transactionType", "AUTHORIZECAPTURE");
			pay.put("amount", amount);
			Map order = new HashMap();
			order.put("payment", pay);
			order.put("currency", "CAD");
			r = testRestTemplate.postForEntity("/api/v1/auth/cart/" + code + "/checkout?store=DEFAULT",
					new HttpEntity<>(order, h), String.class);
			if (r.getStatusCode().is2xxSuccessful()) {
				break;
			}
		}
		assertNotNull(r);
		assertTrue(r.getStatusCode().is2xxSuccessful(), "customer checkout: " + r.getBody());
		assertEquals(6, stockOf(a));
	}
}
