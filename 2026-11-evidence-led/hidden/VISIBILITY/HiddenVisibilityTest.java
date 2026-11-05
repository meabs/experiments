package com.salesmanager.test.shop.hidden;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.math.BigDecimal;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import org.junit.jupiter.api.Test;
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

/**
 * Hidden acceptance tests for ticket VISIBILITY: "visible" and "available" stored separately; hidden products gone for
 * shoppers (reads, lists, carts, checkout) but listed for merchants; friendly URLs work; showing again restores.
 */
@SuppressWarnings({ "rawtypes", "unchecked" })
public class HiddenVisibilityTest extends HiddenOrderSupport {

	private static final Pattern CALCULATED = Pattern.compile("calculated ([0-9]+(?:\\.[0-9]+)?)");

	// ---- helpers

	private PersistableProduct definition(String sku, boolean visible, boolean available) {
		PersistableProduct product = new PersistableProduct();
		PersistableProductInventory inventory = new PersistableProductInventory();
		inventory.setQuantity(30);
		inventory.setSku(sku);
		PersistableProductPrice price = new PersistableProductPrice();
		price.setDefaultPrice(true);
		price.setPrice(new BigDecimal("6.50"));
		inventory.setPrice(price);
		product.setInventory(inventory);
		ProductDescription d = new ProductDescription();
		d.setName(sku);
		d.setLanguage("en");
		d.setFriendlyUrl(sku + "-page");
		product.getDescriptions().add(d);
		product.setSku(sku);
		product.setPrice(new BigDecimal("6.50"));
		product.setQuantity(30);
		product.setVisible(visible);
		product.setAvailable(available);
		return product;
	}

	private long create(String sku, boolean visible, boolean available) {
		ResponseEntity<Entity> r = testRestTemplate.postForEntity("/api/v1/private/product?store=DEFAULT",
				new HttpEntity<>(definition(sku, visible, available), getHeader()), Entity.class);
		assertEquals(HttpStatus.CREATED, r.getStatusCode(), "creating " + sku);
		return r.getBody().getId();
	}

	private void replace(long id, String sku, boolean visible, boolean available) {
		PersistableProduct p = definition(sku, visible, available);
		p.setId(id);
		ResponseEntity<String> r = testRestTemplate.exchange("/api/v1/private/product/" + id + "?store=DEFAULT",
				HttpMethod.PUT, new HttpEntity<>(p, getHeader()), String.class);
		assertTrue(r.getStatusCode().is2xxSuccessful(), "replacing " + sku + ": " + r.getStatusCode());
	}

	private ResponseEntity<Map> bySku(String sku, HttpHeaders h) {
		return testRestTemplate.exchange("/api/v2/product/" + sku + "?store=DEFAULT", HttpMethod.GET, new HttpEntity<>(h),
				Map.class);
	}

	private ResponseEntity<Map> byUrl(String sku, HttpHeaders h) {
		return testRestTemplate.exchange("/api/v2/product/name/" + sku + "-page?store=DEFAULT", HttpMethod.GET,
				new HttpEntity<>(h), Map.class);
	}

	/** The skus a product list shows (follows the response's "products" list). */
	private Map<String, Map> listed(String url, HttpHeaders h) {
		ResponseEntity<Map> r = testRestTemplate.exchange(url, HttpMethod.GET, new HttpEntity<>(h), Map.class);
		assertEquals(HttpStatus.OK, r.getStatusCode(), url);
		Map<String, Map> out = new HashMap<>();
		Object products = r.getBody().get("products");
		if (products != null) {
			for (Object o : (List) products) {
				Map p = (Map) o;
				out.put(String.valueOf(p.get("sku")), p);
			}
		}
		return out;
	}

	private static final String V1_LIST = "/api/v1/products?store=DEFAULT&count=1000";
	private static final String V2_LIST = "/api/v2/products?store=DEFAULT&count=1000";

	private Map item(String sku, int qty) {
		Map m = new HashMap();
		m.put("product", sku);
		m.put("quantity", qty);
		return m;
	}

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
			order.put("customer", customer("vis" + SEQ.incrementAndGet() + "@example.com"));
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

	// ---- tests

	@Test
	public void visibleAndAvailableAreStoredSeparately() {
		String a = uniqueSku("vsa");
		create(a, true, false);
		ResponseEntity<Map> r = bySku(a, noAuth());
		assertEquals(HttpStatus.OK, r.getStatusCode());
		assertEquals(Boolean.TRUE, r.getBody().get("visible"));
		assertEquals(Boolean.FALSE, r.getBody().get("available"));
		String b = uniqueSku("vsb");
		create(b, true, true);
		assertEquals(Boolean.TRUE, bySku(b, noAuth()).getBody().get("available"));
	}

	@Test
	public void aHiddenProductCantBeOpenedBySkuOrFriendlyUrl() {
		String a = uniqueSku("vsc");
		create(a, false, true);
		assertEquals(HttpStatus.NOT_FOUND, bySku(a, noAuth()).getStatusCode());
		assertEquals(HttpStatus.NOT_FOUND, byUrl(a, noAuth()).getStatusCode());
	}

	@Test
	public void aVisibleProductOpensByItsFriendlyUrl() {
		String a = uniqueSku("vsd");
		create(a, true, true);
		ResponseEntity<Map> r = byUrl(a, noAuth());
		assertEquals(HttpStatus.OK, r.getStatusCode());
		assertEquals(a, r.getBody().get("sku"));
		assertEquals(bySku(a, noAuth()).getBody().get("id"), r.getBody().get("id"));
	}

	@Test
	public void shoppersDontSeeHiddenProductsInLists() {
		String hidden = uniqueSku("vse");
		String shown = uniqueSku("vsf");
		create(hidden, false, true);
		create(shown, true, true);
		Map<String, Map> v1 = listed(V1_LIST, noAuth());
		assertFalse(v1.containsKey(hidden), "v1 list shows a hidden product");
		assertTrue(v1.containsKey(shown), "v1 list shows the visible product");
		assertFalse(listed(V2_LIST, noAuth()).containsKey(hidden), "v2 list shows a hidden product");
	}

	@Test
	public void merchantsStillSeeTheirHiddenProducts() {
		String hidden = uniqueSku("vsg");
		create(hidden, false, true);
		String shown = uniqueSku("vsg2");
		create(shown, true, true);
		Map<String, Map> admin = listed("/api/v1/private/products?store=DEFAULT&count=1000", getHeader());
		assertTrue(admin.containsKey(hidden), "the admin list includes the hidden product");
		assertEquals(Boolean.FALSE, admin.get(hidden).get("visible"));
		assertTrue(admin.containsKey(shown));
		assertEquals(Boolean.TRUE, admin.get(shown).get("visible"));
		assertFalse(testRestTemplate.exchange("/api/v1/private/products?store=DEFAULT", HttpMethod.GET,
				new HttpEntity<>(noAuth()), String.class).getStatusCode().is2xxSuccessful(), "the admin list needs an admin");
	}

	@Test
	public void aHiddenProductCantBeAddedToACart() {
		String hidden = uniqueSku("vsh");
		String shown = uniqueSku("vsi");
		create(hidden, false, true);
		create(shown, true, true);
		assertEquals(HttpStatus.NOT_FOUND, testRestTemplate.postForEntity("/api/v1/cart/?store=DEFAULT",
				new HttpEntity<>(item(hidden, 1), getHeader()), String.class).getStatusCode());
		String code = cartWith(lines(shown, 1));
		assertEquals(HttpStatus.NOT_FOUND, testRestTemplate.exchange("/api/v1/cart/" + code + "?store=DEFAULT",
				HttpMethod.PUT, new HttpEntity<>(item(hidden, 1), getHeader()), String.class).getStatusCode());
	}

	@Test
	public void aCartHoldingAProductHiddenLaterCantCheckOutUntilItIsShownAgain() {
		String a = uniqueSku("vsj");
		long id = create(a, true, true);
		String code = cartWith(lines(a, 2));
		replace(id, a, false, true);
		ResponseEntity<Map> before = testRestTemplate.exchange("/api/v1/private/orders?store=DEFAULT&count=1000",
				HttpMethod.GET, new HttpEntity<>(getHeader()), Map.class);
		assertEquals(HttpStatus.CONFLICT, checkoutStatus(code));
		ResponseEntity<Map> after = testRestTemplate.exchange("/api/v1/private/orders?store=DEFAULT&count=1000",
				HttpMethod.GET, new HttpEntity<>(getHeader()), Map.class);
		assertEquals(before.getBody().get("recordsTotal"), after.getBody().get("recordsTotal"), "no order is created");
		replace(id, a, true, true);
		assertTrue(checkoutStatus(code).is2xxSuccessful(), "shown again, the cart checks out");
	}

	@Test
	public void showingAHiddenProductAgainBringsItBack() {
		String a = uniqueSku("vsk");
		long id = create(a, false, true);
		replace(id, a, true, true);
		ResponseEntity<Map> r = bySku(a, noAuth());
		assertEquals(HttpStatus.OK, r.getStatusCode());
		assertEquals(Boolean.TRUE, r.getBody().get("visible"));
		assertEquals(30, ((Number) r.getBody().get("quantity")).intValue());
		assertEquals(m("6.50"), money(r.getBody().get("price")));
		assertTrue(listed(V1_LIST, noAuth()).containsKey(a));
		assertEquals(HttpStatus.CREATED, testRestTemplate.postForEntity("/api/v1/cart/?store=DEFAULT",
				new HttpEntity<>(item(a, 1), getHeader()), String.class).getStatusCode());
	}

	@Test
	public void aVisibleProductThatIsNotAvailableCantBeAddedToACart() {
		String a = uniqueSku("vsl");
		create(a, true, false);
		assertEquals(HttpStatus.OK, bySku(a, noAuth()).getStatusCode());
		assertTrue(testRestTemplate.postForEntity("/api/v1/cart/?store=DEFAULT",
				new HttpEntity<>(item(a, 1), getHeader()), String.class).getStatusCode().isError());
	}

	@Test
	public void hidingAProductLeavesItsOrdersAlone() {
		String a = uniqueSku("vsm");
		long pid = create(a, true, true);
		long order = placeOrder(lines(a, 3));
		replace(pid, a, false, true);
		Map o = getOrder(order);
		boolean found = false;
		for (Object x : (List) o.get("products")) {
			Map line = (Map) x;
			if (a.equals(line.get("sku"))) {
				found = true;
				assertEquals(3, ((Number) line.get("orderedQuantity")).intValue());
			}
		}
		assertTrue(found, "the order still lists the product");
	}

	@Test
	public void hidingLeavesOtherProductsVisible() {
		String a = uniqueSku("vsn");
		String b = uniqueSku("vso");
		long ida = create(a, true, true);
		create(b, true, true);
		replace(ida, a, false, true);
		assertEquals(HttpStatus.NOT_FOUND, bySku(a, noAuth()).getStatusCode());
		assertEquals(HttpStatus.OK, bySku(b, noAuth()).getStatusCode());
		assertTrue(listed(V1_LIST, noAuth()).containsKey(b));
	}
}
