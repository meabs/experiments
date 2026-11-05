package com.salesmanager.test.shop.hidden;

import static org.junit.jupiter.api.Assertions.assertEquals;
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
 * Hidden acceptance tests for ticket LIMITS: minimum and maximum order quantities are stored on create and update,
 * shown, validated, enforced on every cart change, and checked again at checkout.
 */
@SuppressWarnings({ "rawtypes", "unchecked" })
public class HiddenLimitsTest extends HiddenOrderSupport {

	private static final Pattern CALCULATED = Pattern.compile("calculated ([0-9]+(?:\\.[0-9]+)?)");

	// ---- helpers

	private PersistableProduct definition(String sku, Integer min, Integer max) {
		PersistableProduct product = new PersistableProduct();
		PersistableProductInventory inventory = new PersistableProductInventory();
		inventory.setQuantity(50);
		inventory.setSku(sku);
		PersistableProductPrice price = new PersistableProductPrice();
		price.setDefaultPrice(true);
		price.setPrice(new BigDecimal("2.00"));
		inventory.setPrice(price);
		product.setInventory(inventory);
		ProductDescription d = new ProductDescription();
		d.setName(sku);
		d.setLanguage("en");
		product.getDescriptions().add(d);
		product.setSku(sku);
		product.setPrice(new BigDecimal("2.00"));
		product.setQuantity(50);
		product.setAvailable(true);
		if (min != null) {
			product.setQuantityOrderMinimum(min);
		}
		if (max != null) {
			product.setQuantityOrderMaximum(max);
		}
		return product;
	}

	private ResponseEntity<Entity> create(String sku, Integer min, Integer max) {
		return testRestTemplate.postForEntity("/api/v1/private/product?store=DEFAULT",
				new HttpEntity<>(definition(sku, min, max), getHeader()), Entity.class);
	}

	private long created(String sku, Integer min, Integer max) {
		ResponseEntity<Entity> r = create(sku, min, max);
		assertEquals(HttpStatus.CREATED, r.getStatusCode(), "creating " + sku);
		return r.getBody().getId();
	}

	private HttpStatus replace(long id, String sku, Integer min, Integer max) {
		PersistableProduct p = definition(sku, min, max);
		p.setId(id);
		return testRestTemplate.exchange("/api/v1/private/product/" + id + "?store=DEFAULT", HttpMethod.PUT,
				new HttpEntity<>(p, getHeader()), String.class).getStatusCode();
	}

	private int[] limits(String sku) {
		ResponseEntity<Map> r = testRestTemplate.exchange("/api/v2/product/" + sku + "?store=DEFAULT", HttpMethod.GET,
				new HttpEntity<>(getHeader()), Map.class);
		assertEquals(HttpStatus.OK, r.getStatusCode(), "reading " + sku);
		return new int[] { ((Number) r.getBody().get("quantityOrderMinimum")).intValue(),
				((Number) r.getBody().get("quantityOrderMaximum")).intValue() };
	}

	private Map item(String sku, int qty) {
		Map m = new HashMap();
		m.put("product", sku);
		m.put("quantity", qty);
		return m;
	}

	private HttpStatus newCart(String sku, int qty) {
		return testRestTemplate.postForEntity("/api/v1/cart/?store=DEFAULT", new HttpEntity<>(item(sku, qty), getHeader()),
				String.class).getStatusCode();
	}

	private HttpStatus put(String code, String sku, int qty) {
		return testRestTemplate.exchange("/api/v1/cart/" + code + "?store=DEFAULT", HttpMethod.PUT,
				new HttpEntity<>(item(sku, qty), getHeader()), String.class).getStatusCode();
	}

	private Map<String, Integer> quantities(String code) {
		ResponseEntity<Map> r = testRestTemplate.exchange("/api/v1/cart/" + code + "?store=DEFAULT", HttpMethod.GET,
				new HttpEntity<>(getHeader()), Map.class);
		assertEquals(HttpStatus.OK, r.getStatusCode());
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

	private HttpStatus checkoutStatus(String cartCode) {
		ensurePayment();
		String amount = "0";
		HttpStatus last = null;
		for (int attempt = 0; attempt < 2; attempt++) {
			Map pay = new HashMap();
			pay.put("paymentModule", "moneyorder");
			pay.put("paymentType", "MONEYORDER");
			pay.put("transactionType", "AUTHORIZECAPTURE");
			pay.put("amount", amount);
			Map order = new HashMap();
			order.put("customer", customer("lim" + SEQ.incrementAndGet() + "@example.com"));
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

	private long orderCount() {
		ResponseEntity<Map> r = testRestTemplate.exchange("/api/v1/private/orders?store=DEFAULT&count=1000", HttpMethod.GET,
				new HttpEntity<>(getHeader()), Map.class);
		return ((Number) r.getBody().get("recordsTotal")).longValue();
	}

	// ---- tests

	@Test
	public void limitsSentOnCreationAreStoredAndShown() {
		String a = uniqueSku("lca");
		created(a, 2, 4);
		int[] l = limits(a);
		assertEquals(2, l[0]);
		assertEquals(4, l[1]);
	}

	@Test
	public void aProductWithoutLimitsHasMinimumOneAndNoMaximum() {
		String a = uniqueSku("lcb");
		created(a, null, null);
		int[] l = limits(a);
		assertEquals(1, l[0]);
		assertEquals(-1, l[1]);
	}

	@Test
	public void replacingAProductStoresItsNewLimits() {
		String a = uniqueSku("lcc");
		long id = created(a, 2, 4);
		assertTrue(replace(id, a, 3, 6).is2xxSuccessful());
		int[] l = limits(a);
		assertEquals(3, l[0]);
		assertEquals(6, l[1]);
		assertTrue(replace(id, a, 1, -1).is2xxSuccessful());
		l = limits(a);
		assertEquals(1, l[0]);
		assertEquals(-1, l[1]);
	}

	@Test
	public void invalidLimitsAreRejectedOnCreation() {
		String a = uniqueSku("lcd");
		assertEquals(HttpStatus.BAD_REQUEST, create(a, 0, 5).getStatusCode());
		String b = uniqueSku("lce");
		assertEquals(HttpStatus.BAD_REQUEST, create(b, 3, 2).getStatusCode());
		for (String sku : new String[] { a, b }) {
			// not stored: the product can't be read (which error Shopizer gives for an unknown sku is not this ticket's concern)
			assertTrue(testRestTemplate.exchange("/api/v2/product/" + sku + "?store=DEFAULT", HttpMethod.GET,
					new HttpEntity<>(getHeader()), String.class).getStatusCode().isError(), sku + " is not stored");
		}
		String c = uniqueSku("lcf");
		assertEquals(HttpStatus.CREATED, create(c, 3, -1).getStatusCode(), "-1 is no maximum");
	}

	@Test
	public void invalidLimitsAreRejectedOnReplaceAndNothingChanges() {
		String a = uniqueSku("lcg");
		long id = created(a, 2, 4);
		assertEquals(HttpStatus.BAD_REQUEST, replace(id, a, 5, 2));
		assertEquals(HttpStatus.BAD_REQUEST, replace(id, a, 0, -1));
		int[] l = limits(a);
		assertEquals(2, l[0]);
		assertEquals(4, l[1]);
	}

	@Test
	public void aNewCartMustRespectTheLimits() {
		String a = uniqueSku("lch");
		created(a, 2, 4);
		assertEquals(HttpStatus.BAD_REQUEST, newCart(a, 1), "below the minimum");
		assertEquals(HttpStatus.BAD_REQUEST, newCart(a, 5), "above the maximum");
		assertEquals(HttpStatus.CREATED, newCart(a, 2));
		assertEquals(HttpStatus.CREATED, newCart(a, 4));
	}

	@Test
	public void changingAQuantityOutsideTheLimitsIsRefusedAndTheCartKept() {
		String a = uniqueSku("lci");
		String b = uniqueSku("lcj");
		created(a, 2, 4);
		created(b, null, null);
		String code = cartWith(lines(a, 3, b, 1));
		assertEquals(HttpStatus.BAD_REQUEST, put(code, a, 5));
		assertEquals(HttpStatus.BAD_REQUEST, put(code, a, 1));
		Map<String, Integer> q = quantities(code);
		assertEquals(Integer.valueOf(3), q.get(a));
		assertEquals(Integer.valueOf(1), q.get(b));
		assertTrue(put(code, a, 4).is2xxSuccessful());
		assertEquals(Integer.valueOf(4), quantities(code).get(a));
	}

	@Test
	public void aMultiChangeOutsideTheLimitsChangesNothing() {
		String a = uniqueSku("lck");
		String b = uniqueSku("lcl");
		created(a, null, null);
		created(b, 1, 2);
		String code = cartWith(lines(a, 1, b, 1));
		ResponseEntity<String> r = testRestTemplate.postForEntity("/api/v1/cart/" + code + "/multi?store=DEFAULT",
				new HttpEntity<>(new Map[] { item(a, 7), item(b, 3) }, getHeader()), String.class);
		assertEquals(HttpStatus.BAD_REQUEST, r.getStatusCode());
		Map<String, Integer> q = quantities(code);
		assertEquals(Integer.valueOf(1), q.get(a));
		assertEquals(Integer.valueOf(1), q.get(b));
		ResponseEntity<String> ok = testRestTemplate.postForEntity("/api/v1/cart/" + code + "/multi?store=DEFAULT",
				new HttpEntity<>(new Map[] { item(a, 7), item(b, 2) }, getHeader()), String.class);
		assertTrue(ok.getStatusCode().is2xxSuccessful());
		assertEquals(Integer.valueOf(7), quantities(code).get(a));
	}

	@Test
	public void zeroStillRemovesAProduct() {
		String a = uniqueSku("lcm");
		String b = uniqueSku("lcn");
		created(a, 2, 4);
		created(b, null, null);
		String code = cartWith(lines(a, 2, b, 1));
		assertTrue(put(code, a, 0).is2xxSuccessful());
		Map<String, Integer> q = quantities(code);
		assertEquals(1, q.size());
		assertTrue(q.containsKey(b));
	}

	@Test
	public void checkoutRefusesACartThatBreaksLimitsChangedSinceItWasFilled() {
		String a = uniqueSku("lco");
		long id = created(a, 1, 4);
		String code = cartWith(lines(a, 4));
		assertTrue(replace(id, a, 1, 3).is2xxSuccessful());
		assertEquals(Integer.valueOf(4), quantities(code).get(a), "the cart keeps its quantity");
		int stock = stockOf(a);
		long orders = orderCount();
		assertEquals(HttpStatus.CONFLICT, checkoutStatus(code));
		assertEquals(orders, orderCount(), "no order is created");
		assertEquals(stock, stockOf(a));
		assertEquals(Integer.valueOf(4), quantities(code).get(a));
	}

	@Test
	public void checkoutRefusesACartBelowARaisedMinimum() {
		String a = uniqueSku("lcp");
		long id = created(a, 1, -1);
		String code = cartWith(lines(a, 2));
		assertTrue(replace(id, a, 3, -1).is2xxSuccessful());
		assertEquals(HttpStatus.CONFLICT, checkoutStatus(code));
	}

	@Test
	public void aCartWithinTheLimitsChecksOut() {
		String a = uniqueSku("lcq");
		String b = uniqueSku("lcr");
		created(a, 2, 4);
		created(b, null, null);
		String code = cartWith(lines(a, 3, b, 1));
		assertTrue(checkoutStatus(code).is2xxSuccessful());
	}

	@Test
	public void productsWithoutLimitsWorkAsBefore() {
		String a = uniqueSku("lcs");
		created(a, null, null);
		assertEquals(HttpStatus.CREATED, newCart(a, 1));
		String code = cartWith(lines(a, 25));
		assertTrue(put(code, a, 40).is2xxSuccessful());
		assertTrue(checkoutStatus(code).is2xxSuccessful());
	}

	@Test
	public void equalMinimumAndMaximumAllowExactlyThatQuantity() {
		String a = uniqueSku("lct");
		created(a, 3, 3);
		assertEquals(HttpStatus.BAD_REQUEST, newCart(a, 2));
		assertEquals(HttpStatus.BAD_REQUEST, newCart(a, 4));
		assertEquals(HttpStatus.CREATED, newCart(a, 3));
	}
}
