package com.salesmanager.test.shop.hidden;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import com.salesmanager.shop.model.catalog.product.PersistableProductPrice;
import com.salesmanager.shop.model.catalog.product.ProductDescription;
import com.salesmanager.shop.model.catalog.product.product.PersistableProduct;
import com.salesmanager.shop.model.catalog.product.product.PersistableProductInventory;
import com.salesmanager.shop.model.entity.Entity;
import com.salesmanager.test.shop.common.ServicesTestSupport;

/**
 * Shared set-up for the hidden tests (copied into every ticket's hidden folder, identical): products with a known price
 * and stock, the moneyorder payment module, a 13% tax for Ontario, and an anonymous checkout that pays exactly what the
 * shop calculates. Only existing endpoints are used here.
 */
@SuppressWarnings({ "rawtypes", "unchecked" })
public abstract class HiddenOrderSupport extends ServicesTestSupport {

	protected static final AtomicInteger SEQ = new AtomicInteger();
	private static volatile boolean paymentReady;
	private static volatile boolean taxReady;
	private static final Pattern CALCULATED = Pattern.compile("calculated ([0-9]+(?:\\.[0-9]+)?)");

	protected String uniqueSku(String prefix) {
		return prefix + SEQ.incrementAndGet() + "x" + (System.nanoTime() % 100000);
	}

	protected synchronized void ensurePayment() {
		if (paymentReady) {
			return;
		}
		Map mo = new HashMap();
		mo.put("code", "moneyorder");
		mo.put("active", true);
		mo.put("defaultSelected", true);
		Map keys = new HashMap();
		keys.put("address", "1 Bank Street");
		mo.put("integrationKeys", keys);
		ResponseEntity<String> r = testRestTemplate.postForEntity("/api/v1/private/modules/payment?store=DEFAULT",
				new HttpEntity<>(mo, getHeader()), String.class);
		assertEquals(HttpStatus.OK, r.getStatusCode(), "configuring moneyorder: " + r.getBody());
		paymentReady = true;
	}

	/** 13% on the DEFAULT tax class for Ontario, Canada, where every test order is delivered. */
	protected synchronized void ensureTax() {
		if (taxReady) {
			return;
		}
		Map tr = new HashMap();
		tr.put("code", "hiddenon13");
		tr.put("country", "CA");
		tr.put("zone", "ON");
		tr.put("priority", 0);
		tr.put("rate", 13);
		tr.put("store", "DEFAULT");
		tr.put("taxClass", "DEFAULT");
		Map d = new HashMap();
		d.put("language", "en");
		d.put("name", "HST");
		tr.put("descriptions", Arrays.asList(d));
		ResponseEntity<String> r = testRestTemplate.postForEntity("/api/v1/private/tax/rate/",
				new HttpEntity<>(tr, getHeader()), String.class);
		assertTrue(r.getStatusCode().is2xxSuccessful(), "creating the tax rate: " + r.getBody());
		taxReady = true;
	}

	/** Creates an available product at a plain price (no discount) with the given stock; returns its id. */
	protected long createProduct(String sku, String price, int stock) {
		PersistableProduct product = new PersistableProduct();
		PersistableProductInventory inventory = new PersistableProductInventory();
		inventory.setQuantity(stock);
		inventory.setSku(sku);
		PersistableProductPrice productPrice = new PersistableProductPrice();
		productPrice.setDefaultPrice(true);
		productPrice.setPrice(new BigDecimal(price));
		inventory.setPrice(productPrice);
		product.setInventory(inventory);
		ProductDescription description = new ProductDescription();
		description.setName(sku);
		description.setLanguage("en");
		product.getDescriptions().add(description);
		product.setSku(sku);
		product.setPrice(new BigDecimal(price));
		product.setQuantity(stock);
		product.setAvailable(true);
		ResponseEntity<Entity> r = testRestTemplate.postForEntity("/api/v1/private/product?store=DEFAULT",
				new HttpEntity<>(product, getHeader()), Entity.class);
		assertEquals(HttpStatus.CREATED, r.getStatusCode(), "creating product " + sku);
		return r.getBody().getId();
	}

	/**
	 * A few spare products before each checkout. Unchanged Shopizer looks the ordered product up by the order line's id
	 * during checkout, and fails outright when no product has that id; how many products other test classes happened
	 * to create would otherwise decide whether an unrelated checkout works. The spare products keep product ids ahead
	 * of order line ids. They are never ordered, and checkout's own behaviour is not changed by them.
	 */
	protected void fillers() {
		for (int i = 0; i < 4; i++) {
			createProduct(uniqueSku("filler"), "1.00", 1000);
		}
	}

	/** Stock as the catalogue reports it. */
	protected int stockOf(String sku) {
		ResponseEntity<Map> r = testRestTemplate.exchange("/api/v2/product/" + sku + "?store=DEFAULT", HttpMethod.GET,
				new HttpEntity<>(getHeader()), Map.class);
		assertEquals(HttpStatus.OK, r.getStatusCode(), "reading product " + sku);
		return ((Number) r.getBody().get("quantity")).intValue();
	}

	/** A cart holding the given skus and quantities, in order; returns the cart code. */
	protected String cartWith(LinkedHashMap<String, Integer> lines) {
		String code = null;
		for (Map.Entry<String, Integer> e : lines.entrySet()) {
			Map item = new HashMap();
			item.put("product", e.getKey());
			item.put("quantity", e.getValue());
			ResponseEntity<Map> r;
			if (code == null) {
				r = testRestTemplate.postForEntity("/api/v1/cart/?store=DEFAULT", new HttpEntity<>(item, getHeader()),
						Map.class);
				assertEquals(HttpStatus.CREATED, r.getStatusCode(), "creating cart with " + e.getKey());
				code = (String) r.getBody().get("code");
			} else {
				r = testRestTemplate.exchange("/api/v1/cart/" + code + "?store=DEFAULT", HttpMethod.PUT,
						new HttpEntity<>(item, getHeader()), Map.class);
				assertTrue(r.getStatusCode().is2xxSuccessful(), "adding " + e.getKey() + " to cart: " + r.getStatusCode());
			}
		}
		assertNotNull(code);
		return code;
	}

	protected Map customer(String email) {
		Map addr = new HashMap();
		addr.put("address", "1 Main Street");
		addr.put("city", "Toronto");
		addr.put("postalCode", "M5V 2T6");
		addr.put("country", "CA");
		addr.put("stateProvince", "ON");
		addr.put("firstName", "Ann");
		addr.put("lastName", "Lee");
		Map cust = new HashMap();
		cust.put("emailAddress", email);
		cust.put("billing", addr);
		cust.put("delivery", addr);
		cust.put("language", "en");
		return cust;
	}

	/**
	 * Anonymous checkout of a cart, paying exactly what the shop calculates (the shop rejects any other amount and names
	 * the right one). Returns the raw checkout response.
	 */
	protected ResponseEntity<Map> checkoutCart(String cartCode, String email) {
		ensurePayment();
		fillers();
		String amount = "0";
		ResponseEntity<String> first = null;
		for (int attempt = 0; attempt < 2; attempt++) {
			Map pay = new HashMap();
			pay.put("paymentModule", "moneyorder");
			pay.put("paymentType", "MONEYORDER");
			pay.put("transactionType", "AUTHORIZECAPTURE");
			pay.put("amount", amount);
			Map order = new HashMap();
			order.put("customer", customer(email));
			order.put("payment", pay);
			order.put("currency", "CAD");
			ResponseEntity<String> r = testRestTemplate.postForEntity("/api/v1/cart/" + cartCode + "/checkout?store=DEFAULT",
					new HttpEntity<>(order, getHeader()), String.class);
			if (r.getStatusCode().is2xxSuccessful()) {
				return asMap(r);
			}
			first = r;
			Matcher m = CALCULATED.matcher(String.valueOf(r.getBody()));
			if (!m.find()) {
				break;
			}
			amount = m.group(1);
		}
		throw new AssertionError("checkout failed: " + (first == null ? "" : first.getStatusCode() + " " + first.getBody()));
	}

	private ResponseEntity<Map> asMap(ResponseEntity<String> r) {
		try {
			Map body = new com.fasterxml.jackson.databind.ObjectMapper().readValue(r.getBody(), Map.class);
			return new ResponseEntity<>(body, r.getStatusCode());
		} catch (Exception e) {
			throw new AssertionError("checkout response is not JSON: " + r.getBody());
		}
	}

	/** Places an order for the given skus and quantities and returns the order id. */
	protected long placeOrder(LinkedHashMap<String, Integer> lines) {
		String cart = cartWith(lines);
		ResponseEntity<Map> r = checkoutCart(cart, "buyer" + SEQ.incrementAndGet() + "@example.com");
		assertNotNull(r, "checkout response");
		Object id = r.getBody().get("id");
		assertNotNull(id, "order id in " + r.getBody());
		return ((Number) id).longValue();
	}

	protected static LinkedHashMap<String, Integer> lines(Object... skuQty) {
		LinkedHashMap<String, Integer> m = new LinkedHashMap<>();
		for (int i = 0; i < skuQty.length; i += 2) {
			m.put((String) skuQty[i], (Integer) skuQty[i + 1]);
		}
		return m;
	}

	protected Map getOrder(long id) {
		ResponseEntity<Map> r = testRestTemplate.exchange("/api/v1/private/orders/" + id + "?store=DEFAULT", HttpMethod.GET,
				new HttpEntity<>(getHeader()), Map.class);
		assertEquals(HttpStatus.OK, r.getStatusCode(), "reading order " + id);
		return r.getBody();
	}

	/** The value of the order's totals line with this code, or null. */
	protected static BigDecimal totalLine(Map order, String code) {
		List totals = (List) order.get("totals");
		if (totals == null) {
			return null;
		}
		for (Object o : totals) {
			Map t = (Map) o;
			if (code.equals(t.get("code"))) {
				return money(t.get("value"));
			}
		}
		return null;
	}

	/** The sum of the order's tax lines (any line whose module or code is not a known non-tax total). */
	protected static BigDecimal taxOf(Map order) {
		BigDecimal sum = BigDecimal.ZERO.setScale(2);
		List totals = (List) order.get("totals");
		for (Object o : totals) {
			Map t = (Map) o;
			if ("tax".equals(t.get("module"))) {
				sum = sum.add(money(t.get("value")));
			}
		}
		return sum;
	}

	protected static BigDecimal money(Object v) {
		if (v == null) {
			return null;
		}
		return new BigDecimal(String.valueOf(v)).setScale(2, java.math.RoundingMode.HALF_UP);
	}

	protected static BigDecimal m(String v) {
		return new BigDecimal(v).setScale(2);
	}

	protected HttpHeaders noAuth() {
		HttpHeaders h = new HttpHeaders();
		h.setContentType(org.springframework.http.MediaType.APPLICATION_JSON);
		return h;
	}

	protected List<Map> asList(Object o) {
		List<Map> out = new ArrayList<>();
		if (o instanceof List) {
			for (Object x : (List) o) {
				out.add((Map) x);
			}
		}
		return out;
	}

	/** Registers a customer (delivery in Ontario) and logs in; returns headers carrying the customer's token. */
	protected HttpHeaders registerAndLogin(String email, String password) {
		Map c = customer(email);
		c.put("password", password);
		c.put("repeatPassword", password);
		c.put("storeCode", "DEFAULT");
		c.put("gender", "F");
		ResponseEntity<String> reg = testRestTemplate.postForEntity("/api/v1/customer/register?store=DEFAULT",
				new HttpEntity<>(c, noAuth()), String.class);
		assertTrue(reg.getStatusCode().is2xxSuccessful(), "registering " + email + ": " + reg.getBody());
		Map login = new HashMap();
		login.put("username", email);
		login.put("password", password);
		ResponseEntity<Map> lr = testRestTemplate.postForEntity("/api/v1/customer/login?store=DEFAULT",
				new HttpEntity<>(login, noAuth()), Map.class);
		assertEquals(HttpStatus.OK, lr.getStatusCode(), "logging in " + email);
		HttpHeaders h = noAuth();
		h.add("Authorization", "Bearer " + lr.getBody().get("token"));
		return h;
	}

	/**
	 * Logged-in checkout of a cart. Logged-in checkout doesn't name the right amount when it is given a wrong one, so
	 * the caller passes the amounts the order can cost (for example with and without tax); the first accepted wins.
	 */
	protected ResponseEntity<String> customerCheckout(HttpHeaders customer, String cartCode, String... amounts) {
		ensurePayment();
		fillers();
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
			r = testRestTemplate.postForEntity("/api/v1/auth/cart/" + cartCode + "/checkout?store=DEFAULT",
					new HttpEntity<>(order, customer), String.class);
			if (r.getStatusCode().is2xxSuccessful()) {
				return r;
			}
		}
		return r;
	}
}
