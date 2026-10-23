package com.salesmanager.test.shop.hidden;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.junit.jupiter.api.Test;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;

import com.salesmanager.shop.model.catalog.category.Category;
import com.salesmanager.shop.model.catalog.category.PersistableCategory;
import com.salesmanager.shop.model.catalog.product.product.PersistableProduct;
import com.salesmanager.shop.model.entity.Entity;
import com.salesmanager.shop.model.references.PersistableAddress;
import com.salesmanager.shop.model.store.PersistableMerchantStore;
import com.salesmanager.test.shop.common.ServicesTestSupport;

/**
 * Hidden acceptance test for feature DISCOUNT: merchant-managed discount codes applied to carts. Every product made here
 * costs 125 (the test helper's discounted price).
 */
@SuppressWarnings({ "rawtypes", "unchecked" })
public class HiddenDiscountCodesTest extends ServicesTestSupport {

	private static final String DISCOUNTS = "/api/v1/private/discounts";

	// ---- catalogue and cart helpers

	private void product(String sku, Long categoryId) {
		PersistableProduct p = product(sku);
		p.setSku(sku);
		p.setQuantity(100);
		if (categoryId != null) {
			Category c = new Category();
			c.setId(categoryId);
			p.setCategories(new ArrayList<>(Arrays.asList(c)));
		}
		ResponseEntity<Entity> r = testRestTemplate.postForEntity("/api/v1/private/product?store=DEFAULT",
				new HttpEntity<>(p, getHeader()), Entity.class);
		assertEquals(HttpStatus.CREATED, r.getStatusCode(), "creating product " + sku);
	}

	private long newCategory(String code, Long parentId, String parentCode) {
		PersistableCategory c = category(code);
		if (parentId != null) {
			// shopizer only links a parent given by both its id and its code
			Category parent = new Category();
			parent.setId(parentId);
			parent.setCode(parentCode);
			c.setParent(parent);
			c.setDepth(2);
		}
		ResponseEntity<PersistableCategory> r = testRestTemplate.postForEntity("/api/v1/private/category?store=DEFAULT",
				new HttpEntity<>(c, getHeader()), PersistableCategory.class);
		assertEquals(HttpStatus.CREATED, r.getStatusCode(), "creating category " + code);
		return r.getBody().getId();
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

	private void add(String cart, String sku, int qty) {
		ResponseEntity<Map> r = testRestTemplate.exchange("/api/v1/cart/" + cart, HttpMethod.PUT,
				new HttpEntity<>(line(sku, qty), getHeader()), Map.class);
		assertTrue(r.getStatusCode().is2xxSuccessful(), "adding " + sku + ": " + r.getStatusCode());
	}

	private void remove(String cart, String sku) {
		ResponseEntity<Map> r = testRestTemplate.exchange("/api/v1/cart/" + cart + "/product/" + sku, HttpMethod.DELETE,
				new HttpEntity<>(getHeader()), Map.class);
		assertTrue(r.getStatusCode().is2xxSuccessful(), "removing " + sku + ": " + r.getStatusCode());
	}

	private Map read(String cart) {
		ResponseEntity<Map> g = testRestTemplate.exchange("/api/v1/cart/" + cart, HttpMethod.GET,
				new HttpEntity<>(getHeader()), Map.class);
		assertEquals(HttpStatus.OK, g.getStatusCode());
		return g.getBody();
	}

	private ResponseEntity<Map> apply(String cart, String code) {
		return testRestTemplate.exchange("/api/v1/cart/" + cart + "/promo/" + code, HttpMethod.POST,
				new HttpEntity<>(getHeader()), Map.class);
	}

	private void applies(String cart, String code) {
		ResponseEntity<Map> r = apply(cart, code);
		assertTrue(r.getStatusCode().is2xxSuccessful(), "applying " + code + ": " + r.getStatusCode());
	}

	private void rejected(String cart, String code) {
		assertEquals(HttpStatus.BAD_REQUEST, apply(cart, code).getStatusCode(), "applying " + code);
	}

	private static BigDecimal money(Object o) {
		return new BigDecimal(String.valueOf(o));
	}

	private static BigDecimal discountLine(Map cart) {
		Object totals = cart.get("totals");
		if (totals == null) {
			return null;
		}
		for (Map t : (List<Map>) totals) {
			if ("discount".equals(t.get("code"))) {
				return money(t.get("value"));
			}
		}
		return null;
	}

	private static void assertMoney(String expected, Object actual, String what) {
		assertNotNull(actual, what);
		assertEquals(0, new BigDecimal(expected).compareTo(actual instanceof BigDecimal ? (BigDecimal) actual : money(actual)),
				what + ": expected " + expected + " but was " + actual);
	}

	private static void assertDiscounted(Map cart, String code, String discount, String total) {
		assertEquals(code, cart.get("promoCode"), "promoCode");
		assertMoney(discount, discountLine(cart), "discount line");
		assertMoney(total, cart.get("total"), "total");
	}

	private static void assertNoDiscount(Map cart, String subtotal) {
		Object promo = cart.get("promoCode");
		assertTrue(promo == null || "".equals(promo), "promoCode should be empty, was " + promo);
		assertNull(discountLine(cart), "there should be no discount line");
		assertMoney(subtotal, cart.get("total"), "total");
	}

	// ---- admin API helpers

	private Map<String, Object> code(String code, String type, Object value) {
		Map<String, Object> d = new HashMap<>();
		d.put("code", code);
		d.put("type", type);
		d.put("value", value);
		return d;
	}

	private ResponseEntity<Map> create(Map<String, Object> d, String store) {
		return testRestTemplate.exchange(DISCOUNTS + "?store=" + store, HttpMethod.POST, new HttpEntity<>(d, getHeader()),
				Map.class);
	}

	private long created(Map<String, Object> d) {
		ResponseEntity<Map> r = create(d, "DEFAULT");
		assertEquals(HttpStatus.CREATED, r.getStatusCode(), "creating " + d);
		assertNotNull(r.getBody().get("id"), "the created code has an id");
		return ((Number) r.getBody().get("id")).longValue();
	}

	private ResponseEntity<Map> replace(long id, Map<String, Object> d) {
		return testRestTemplate.exchange(DISCOUNTS + "/" + id + "?store=DEFAULT", HttpMethod.PUT,
				new HttpEntity<>(d, getHeader()), Map.class);
	}

	// ---- applying codes

	@Test
	public void percentOffTheWholeCart() {
		product("hdpct", null);
		created(code("HDPCT10", "PERCENT", 10));
		String cart = cart("hdpct", 2);
		applies(cart, "HDPCT10");
		assertDiscounted(read(cart), "HDPCT10", "25.00", "225.00");
	}

	@Test
	public void codesMatchIgnoringCaseAndShowAsWritten() {
		product("hdcase", null);
		created(code("HdMixed5", "PERCENT", 5));
		String cart = cart("hdcase", 1);
		applies(cart, "hdmixed5");
		assertDiscounted(read(cart), "HdMixed5", "6.25", "118.75");
	}

	@Test
	public void amountNeverExceedsTheEligibleSubtotal() {
		product("hdamt", null);
		created(code("HDAMT500", "AMOUNT", 500));
		String cart = cart("hdamt", 1);
		applies(cart, "HDAMT500");
		assertDiscounted(read(cart), "HDAMT500", "125.00", "0.00");
	}

	@Test
	public void discountRoundsHalfUp() {
		product("hdround", null);
		created(code("HDROUND", "PERCENT", 12.5));
		String cart = cart("hdround", 1);
		applies(cart, "HDROUND");
		assertDiscounted(read(cart), "HDROUND", "15.63", "109.37");
	}

	@Test
	public void categoriesIncludeEveryCategoryBelowThem() {
		long top = newCategory("hdcattop", null, null);
		long below = newCategory("hdcatbelow", top, "hdcattop");
		product("hdcatin", below);
		product("hdcatout", null);
		Map<String, Object> d = code("HDCAT20", "PERCENT", 20);
		d.put("categories", Arrays.asList("hdcattop"));
		created(d);
		String cart = cart("hdcatin", 1);
		add(cart, "hdcatout", 1);
		applies(cart, "HDCAT20");
		assertDiscounted(read(cart), "HDCAT20", "25.00", "225.00");
		String other = cart("hdcatout", 2);
		rejected(other, "HDCAT20");
		assertNoDiscount(read(other), "250");
	}

	@Test
	public void minimumSubtotalIsCheckedAndTheCodeIsDroppedWhenTheCartFallsBelowIt() {
		product("hdmina", null);
		product("hdminb", null);
		Map<String, Object> d = code("HDMIN300", "AMOUNT", 30);
		d.put("minimumSubtotal", 300);
		created(d);
		String cart = cart("hdmina", 2);
		rejected(cart, "HDMIN300");
		add(cart, "hdminb", 1);
		applies(cart, "HDMIN300");
		assertDiscounted(read(cart), "HDMIN300", "30.00", "345.00");
		remove(cart, "hdminb");
		assertNoDiscount(read(cart), "250");
	}

	@Test
	public void inactiveExpiredAndFutureCodesDoNotApply() {
		product("hddates", null);
		Map<String, Object> inactive = code("HDOFF", "PERCENT", 10);
		inactive.put("active", false);
		created(inactive);
		Map<String, Object> expired = code("HDPAST", "PERCENT", 10);
		expired.put("startDate", "2020-01-01");
		expired.put("endDate", LocalDate.now().minusDays(1).toString());
		created(expired);
		Map<String, Object> future = code("HDSOON", "PERCENT", 10);
		future.put("startDate", LocalDate.now().plusDays(1).toString());
		created(future);
		Map<String, Object> lastDay = code("HDLASTDAY", "PERCENT", 10);
		lastDay.put("startDate", "2020-01-01");
		lastDay.put("endDate", LocalDate.now().toString());
		created(lastDay);
		String cart = cart("hddates", 1);
		rejected(cart, "HDOFF");
		rejected(cart, "HDPAST");
		rejected(cart, "HDSOON");
		rejected(cart, "HDNOSUCHCODE");
		applies(cart, "HDLASTDAY");
		assertDiscounted(read(cart), "HDLASTDAY", "12.50", "112.50");
	}

	@Test
	public void aRejectedCodeKeepsThePreviousOneAndANewCodeReplacesIt() {
		product("hdswap", null);
		created(code("HDFIRST", "PERCENT", 10));
		created(code("HDSECOND", "AMOUNT", 5));
		String cart = cart("hdswap", 1);
		applies(cart, "HDFIRST");
		rejected(cart, "HDNOTACODE");
		assertDiscounted(read(cart), "HDFIRST", "12.50", "112.50");
		applies(cart, "HDSECOND");
		assertDiscounted(read(cart), "HDSECOND", "5.00", "120.00");
	}

	@Test
	public void editingACodeChangesTheCartsDiscount() {
		product("hdedit", null);
		long id = created(code("HDEDIT", "PERCENT", 10));
		String cart = cart("hdedit", 1);
		applies(cart, "HDEDIT");
		assertEquals(HttpStatus.OK, replace(id, code("HDEDIT", "PERCENT", 20)).getStatusCode());
		assertDiscounted(read(cart), "HDEDIT", "25.00", "100.00");
	}

	@Test
	public void deactivatingOrDeletingACodeDropsItFromCarts() {
		product("hddrop", null);
		long off = created(code("HDDEACT", "PERCENT", 10));
		long gone = created(code("HDDELETE", "PERCENT", 10));
		String a = cart("hddrop", 1);
		applies(a, "HDDEACT");
		Map<String, Object> d = code("HDDEACT", "PERCENT", 10);
		d.put("active", false);
		assertEquals(HttpStatus.OK, replace(off, d).getStatusCode());
		assertNoDiscount(read(a), "125");
		String b = cart("hddrop", 1);
		applies(b, "HDDELETE");
		ResponseEntity<Map> del = testRestTemplate.exchange(DISCOUNTS + "/" + gone + "?store=DEFAULT", HttpMethod.DELETE,
				new HttpEntity<>(getHeader()), Map.class);
		assertTrue(del.getStatusCode().is2xxSuccessful(), "delete: " + del.getStatusCode());
		assertNoDiscount(read(b), "125");
	}

	@Test
	public void theOldHardCodedCodeNoLongerDiscounts() {
		product("hdold", null);
		String cart = cart("hdold", 1);
		rejected(cart, "Test1234");
		assertNoDiscount(read(cart), "125");
	}

	// ---- the admin API

	@Test
	public void invalidCodesAreRejected() {
		newCategory("hdvalidcat", null, null);
		Map<String, Object> noCode = code(null, "PERCENT", 10);
		noCode.remove("code");
		Map<String, Object> noValue = code("HDBADNOVALUE", "PERCENT", null);
		noValue.remove("value");
		Map<String, Object> backwards = code("HDBADDATES", "PERCENT", 10);
		backwards.put("startDate", "2026-06-10");
		backwards.put("endDate", "2026-06-09");
		Map<String, Object> unknownCategory = code("HDBADCAT", "PERCENT", 10);
		unknownCategory.put("categories", Arrays.asList("hdvalidcat", "hdnosuchcategory"));
		List<Map<String, Object>> bad = Arrays.asList(code("HDBADZERO", "PERCENT", 0), code("HDBAD101", "PERCENT", 101),
				code("HDBADNEG", "AMOUNT", -5), code("HDBADAMT0", "AMOUNT", 0), code("HDBADTYPE", "BOGUS", 10), noCode,
				noValue, backwards, unknownCategory);
		for (Map<String, Object> d : bad) {
			assertEquals(HttpStatus.BAD_REQUEST, create(d, "DEFAULT").getStatusCode(), "creating " + d);
		}
		assertEquals(HttpStatus.CREATED, create(code("HDOK100", "PERCENT", 100), "DEFAULT").getStatusCode());
	}

	@Test
	public void codesAreUniqueInAStoreIgnoringCase() {
		created(code("HDUNIQUE", "PERCENT", 10));
		assertEquals(HttpStatus.CONFLICT, create(code("hdunique", "AMOUNT", 5), "DEFAULT").getStatusCode());
		long other = created(code("HDUNIQUE2", "PERCENT", 10));
		assertEquals(HttpStatus.CONFLICT, replace(other, code("HdUnique", "PERCENT", 10)).getStatusCode());
	}

	@Test
	public void storesHaveTheirOwnCodes() {
		PersistableAddress address = new PersistableAddress();
		address.setAddress("1 Discount Road");
		address.setPostalCode("12345");
		address.setCountry("US");
		address.setCity("FT LD");
		address.setStateProvince("FL");
		PersistableMerchantStore store = new PersistableMerchantStore();
		store.setCode("hdstore");
		store.setCurrency("CAD");
		store.setDefaultLanguage("en");
		store.setEmail("hd@test.com");
		store.setName("hdstore");
		store.setPhone("444-555-6666");
		store.setSupportedLanguages(Arrays.asList("en"));
		store.setAddress(address);
		ResponseEntity<Void> s = testRestTemplate.exchange("/api/v1/private/store/", HttpMethod.POST,
				new HttpEntity<>(store, getHeader()), Void.class);
		assertEquals(HttpStatus.OK, s.getStatusCode());
		assertEquals(HttpStatus.CREATED, create(code("HDSHARED", "PERCENT", 10), "DEFAULT").getStatusCode());
		assertEquals(HttpStatus.CREATED, create(code("HDSHARED", "PERCENT", 50), "hdstore").getStatusCode(),
				"another store may use the same code");
		assertEquals(HttpStatus.CREATED, create(code("HDELSEWHERE", "PERCENT", 10), "hdstore").getStatusCode());
		product("hdstoreitem", null);
		String cart = cart("hdstoreitem", 1);
		rejected(cart, "HDELSEWHERE");
		applies(cart, "HDSHARED");
		assertDiscounted(read(cart), "HDSHARED", "12.50", "112.50");
	}

	@Test
	public void codesCanBeListed() {
		created(code("HDLISTED", "AMOUNT", 7));
		ResponseEntity<Object> r = testRestTemplate.exchange(DISCOUNTS + "?store=DEFAULT", HttpMethod.GET,
				new HttpEntity<>(getHeader()), Object.class);
		assertEquals(HttpStatus.OK, r.getStatusCode());
		// the task does not fix the list's shape: accept a JSON array, or an object holding the list
		List<Object> lists = new ArrayList<>();
		if (r.getBody() instanceof List) {
			lists.add(r.getBody());
		} else if (r.getBody() instanceof Map) {
			lists.addAll(((Map) r.getBody()).values());
		}
		assertTrue(lists.stream().filter(l -> l instanceof List).flatMap(l -> ((List<Object>) l).stream())
				.anyMatch(d -> d instanceof Map && "HDLISTED".equals(((Map) d).get("code"))), "HDLISTED is listed");
	}

	@Test
	public void theAdminApiRequiresAnAdmin() {
		HttpHeaders anonymous = new HttpHeaders();
		anonymous.setContentType(MediaType.APPLICATION_JSON);
		HttpStatus status = testRestTemplate.exchange(DISCOUNTS + "?store=DEFAULT", HttpMethod.POST,
				new HttpEntity<>(code("HDANON", "PERCENT", 10), anonymous), Map.class).getStatusCode();
		assertTrue(status == HttpStatus.UNAUTHORIZED || status == HttpStatus.FORBIDDEN, "got " + status);
	}
}
