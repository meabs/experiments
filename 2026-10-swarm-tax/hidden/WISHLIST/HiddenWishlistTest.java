package com.salesmanager.test.shop.hidden;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.math.BigDecimal;
import java.nio.charset.Charset;
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

import com.salesmanager.core.model.customer.CustomerGender;
import com.salesmanager.shop.model.catalog.product.product.PersistableProduct;
import com.salesmanager.shop.model.customer.PersistableCustomer;
import com.salesmanager.shop.model.customer.address.Address;
import com.salesmanager.shop.model.entity.Entity;
import com.salesmanager.shop.store.security.AuthenticationRequest;
import com.salesmanager.shop.store.security.AuthenticationResponse;
import com.salesmanager.test.shop.common.ServicesTestSupport;

/**
 * Hidden acceptance test for feature WISHLIST: a logged-in customer's wishlist, moving an item to a cart, and the
 * store's most wished products. Every product made here costs 125 (the test helper's discounted price).
 */
@SuppressWarnings({ "rawtypes", "unchecked" })
public class HiddenWishlistTest extends ServicesTestSupport {

	private static final AtomicInteger SEQ = new AtomicInteger();
	private static final String WISHLIST = "/api/v1/auth/customer/wishlist";

	// ---- helpers

	private String sku() {
		return "wish" + SEQ.incrementAndGet() + "x" + System.nanoTime() % 100000;
	}

	private long newProduct(String sku, int quantity) {
		PersistableProduct p = product(sku);
		p.setSku(sku);
		p.setQuantity(quantity);
		p.getInventory().setQuantity(quantity);
		ResponseEntity<Entity> r = testRestTemplate.postForEntity("/api/v1/private/product?store=DEFAULT",
				new HttpEntity<>(p, getHeader()), Entity.class);
		assertEquals(HttpStatus.CREATED, r.getStatusCode(), "creating product " + sku);
		return r.getBody().getId();
	}

	private String newSku() {
		String s = sku();
		newProduct(s, 100);
		return s;
	}

	/** Registers a new customer and returns headers carrying their token. */
	private HttpHeaders customer() {
		String email = "wish" + SEQ.incrementAndGet() + "_" + System.nanoTime() + "@test.com";
		PersistableCustomer c = new PersistableCustomer();
		c.setEmailAddress(email);
		c.setPassword("clear123");
		c.setGender(CustomerGender.M.name());
		c.setLanguage("en");
		Address billing = new Address();
		billing.setFirstName("wish");
		billing.setLastName("list");
		billing.setCountry("BE");
		c.setBilling(billing);
		c.setStoreCode("DEFAULT");
		ResponseEntity<PersistableCustomer> r = testRestTemplate.postForEntity("/api/v1/customer/register",
				new HttpEntity<>(c, getHeader()), PersistableCustomer.class);
		assertEquals(HttpStatus.OK, r.getStatusCode(), "registering " + email);
		ResponseEntity<AuthenticationResponse> login = testRestTemplate.postForEntity("/api/v1/customer/login",
				new HttpEntity<>(new AuthenticationRequest(email, "clear123")), AuthenticationResponse.class);
		assertEquals(HttpStatus.OK, login.getStatusCode());
		HttpHeaders h = new HttpHeaders();
		h.setContentType(new MediaType("application", "json", Charset.forName("UTF-8")));
		h.add("Authorization", "Bearer " + login.getBody().getToken());
		return h;
	}

	private static Map<String, Object> body(String sku) {
		Map<String, Object> b = new HashMap<>();
		b.put("product", sku);
		return b;
	}

	private ResponseEntity<Map> add(HttpHeaders who, String sku) {
		return testRestTemplate.exchange(WISHLIST, HttpMethod.POST, new HttpEntity<>(body(sku), who), Map.class);
	}

	private Map list(HttpHeaders who) {
		ResponseEntity<Map> r = testRestTemplate.exchange(WISHLIST, HttpMethod.GET, new HttpEntity<>(who), Map.class);
		assertEquals(HttpStatus.OK, r.getStatusCode());
		return r.getBody();
	}

	private static List<Map> items(Map wishlist) {
		return (List<Map>) wishlist.get("items");
	}

	private static List<String> skus(Map wishlist) {
		List<String> s = new ArrayList<>();
		for (Map i : items(wishlist)) {
			s.add((String) i.get("sku"));
		}
		return s;
	}

	private ResponseEntity<Map> move(HttpHeaders who, String sku, String cart) {
		return testRestTemplate.exchange(WISHLIST + "/" + sku + "/cart/" + cart, HttpMethod.POST, new HttpEntity<>(who),
				Map.class);
	}

	private String cart(String sku, int qty) {
		Map<String, Object> i = new HashMap<>();
		i.put("product", sku);
		i.put("quantity", qty);
		ResponseEntity<Map> c = testRestTemplate.exchange("/api/v1/cart/", HttpMethod.POST, new HttpEntity<>(i, getHeader()),
				Map.class);
		assertEquals(HttpStatus.CREATED, c.getStatusCode());
		return (String) c.getBody().get("code");
	}

	private int quantityInCart(String cart, String sku) {
		ResponseEntity<Map> g = testRestTemplate.exchange("/api/v1/cart/" + cart, HttpMethod.GET,
				new HttpEntity<>(getHeader()), Map.class);
		assertEquals(HttpStatus.OK, g.getStatusCode());
		int q = 0;
		for (Map p : (List<Map>) g.getBody().get("products")) {
			if (sku.equals(p.get("sku"))) {
				q += ((Number) p.get("quantity")).intValue();
			}
		}
		return q;
	}

	// ---- the customer's wishlist

	@Test
	public void addingAProductShowsItWithItsDetails() {
		HttpHeaders me = customer();
		String s = newSku();
		ResponseEntity<Map> r = add(me, s);
		assertEquals(HttpStatus.CREATED, r.getStatusCode());
		for (Map w : java.util.Arrays.asList(r.getBody(), list(me))) {
			assertEquals(1, ((Number) w.get("count")).intValue(), "count: " + w);
			Map i = items(w).get(0);
			assertEquals(s, i.get("sku"));
			assertEquals(s, i.get("name"));
			assertEquals(0, new BigDecimal("125").compareTo(new BigDecimal(String.valueOf(i.get("price")))), "price " + i.get("price"));
			assertEquals(Boolean.TRUE, i.get("available"));
			assertNotNull(i.get("addedAt"));
		}
	}

	@Test
	public void addingTheSameProductTwiceKeepsOneEntry() {
		HttpHeaders me = customer();
		String s = newSku();
		assertEquals(HttpStatus.CREATED, add(me, s).getStatusCode());
		ResponseEntity<Map> again = add(me, s);
		assertEquals(HttpStatus.OK, again.getStatusCode());
		assertEquals(1, ((Number) again.getBody().get("count")).intValue());
		assertEquals(1, items(list(me)).size());
	}

	@Test
	public void newestFirst() {
		HttpHeaders me = customer();
		String a = newSku(), b = newSku(), c = newSku();
		add(me, a);
		add(me, b);
		add(me, c);
		assertEquals(java.util.Arrays.asList(c, b, a), skus(list(me)));
	}

	@Test
	public void unknownOrMissingProduct() {
		HttpHeaders me = customer();
		assertEquals(HttpStatus.NOT_FOUND, testRestTemplate.exchange(WISHLIST, HttpMethod.POST,
				new HttpEntity<>(body("no-such-sku-" + System.nanoTime()), me), String.class).getStatusCode());
		assertEquals(HttpStatus.BAD_REQUEST, testRestTemplate.exchange(WISHLIST, HttpMethod.POST,
				new HttpEntity<>(new HashMap<>(), me), String.class).getStatusCode());
		assertEquals(0, ((Number) list(me).get("count")).intValue());
	}

	@Test
	public void removingAProduct() {
		HttpHeaders me = customer();
		String a = newSku(), b = newSku();
		add(me, a);
		add(me, b);
		assertEquals(HttpStatus.NO_CONTENT, testRestTemplate.exchange(WISHLIST + "/" + a, HttpMethod.DELETE,
				new HttpEntity<>(me), String.class).getStatusCode());
		assertEquals(java.util.Arrays.asList(b), skus(list(me)));
		assertEquals(HttpStatus.NOT_FOUND, testRestTemplate.exchange(WISHLIST + "/" + a, HttpMethod.DELETE,
				new HttpEntity<>(me), String.class).getStatusCode());
	}

	@Test
	public void eachCustomerHasTheirOwnWishlist() {
		HttpHeaders one = customer(), two = customer();
		String s = newSku();
		add(one, s);
		assertEquals(0, ((Number) list(two).get("count")).intValue());
		assertEquals(HttpStatus.NOT_FOUND, testRestTemplate.exchange(WISHLIST + "/" + s, HttpMethod.DELETE,
				new HttpEntity<>(two), String.class).getStatusCode());
		assertEquals(1, ((Number) list(one).get("count")).intValue());
	}

	@Test
	public void atMostFiftyProducts() {
		HttpHeaders me = customer();
		for (int i = 0; i < 50; i++) {
			assertEquals(HttpStatus.CREATED, add(me, newSku()).getStatusCode(), "product " + (i + 1));
		}
		assertEquals(HttpStatus.BAD_REQUEST, testRestTemplate.exchange(WISHLIST, HttpMethod.POST,
				new HttpEntity<>(body(newSku()), me), String.class).getStatusCode());
		assertEquals(50, ((Number) list(me).get("count")).intValue());
	}

	@Test
	public void theWishlistNeedsALoggedInCustomer() {
		HttpHeaders anonymous = new HttpHeaders();
		anonymous.setContentType(MediaType.APPLICATION_JSON);
		HttpStatus s = testRestTemplate.exchange(WISHLIST, HttpMethod.GET, new HttpEntity<>(anonymous), String.class).getStatusCode();
		assertTrue(s == HttpStatus.UNAUTHORIZED || s == HttpStatus.FORBIDDEN, "without a token: " + s);
	}

	@Test
	public void aDeletedProductLeavesTheWishlist() {
		HttpHeaders me = customer();
		String s = sku();
		long id = newProduct(s, 100);
		String keep = newSku();
		add(me, s);
		add(me, keep);
		ResponseEntity<String> d = testRestTemplate.exchange("/api/v1/private/product/" + id + "?store=DEFAULT",
				HttpMethod.DELETE, new HttpEntity<>(getHeader()), String.class);
		assertTrue(d.getStatusCode().is2xxSuccessful(), "deleting the product: " + d.getStatusCode());
		Map w = list(me);
		assertEquals(java.util.Arrays.asList(keep), skus(w));
		assertEquals(1, ((Number) w.get("count")).intValue());
	}

	// ---- moving to a cart

	@Test
	public void movingToACartAddsOneUnitAndLeavesTheWishlist() {
		HttpHeaders me = customer();
		String s = newSku(), other = newSku();
		add(me, s);
		String c = cart(other, 1);
		ResponseEntity<Map> r = move(me, s, c);
		assertEquals(HttpStatus.OK, r.getStatusCode());
		assertEquals(1, quantityInCart(c, s));
		assertEquals(1, quantityInCart(c, other));
		assertFalse(skus(list(me)).contains(s));
	}

	@Test
	public void movingAProductAlreadyInTheCartAddsOneMore() {
		HttpHeaders me = customer();
		String s = newSku();
		add(me, s);
		String c = cart(s, 2);
		assertEquals(HttpStatus.OK, move(me, s, c).getStatusCode());
		assertEquals(3, quantityInCart(c, s));
	}

	@Test
	public void anOutOfStockProductShowsAsUnavailableAndCannotBeMoved() {
		HttpHeaders me = customer();
		String s = sku();
		newProduct(s, 0);
		String other = newSku();
		assertEquals(HttpStatus.CREATED, add(me, s).getStatusCode());
		assertEquals(Boolean.FALSE, items(list(me)).get(0).get("available"));
		String c = cart(other, 1);
		assertEquals(HttpStatus.CONFLICT, testRestTemplate.exchange(WISHLIST + "/" + s + "/cart/" + c, HttpMethod.POST,
				new HttpEntity<>(me), String.class).getStatusCode());
		assertEquals(0, quantityInCart(c, s));
		assertTrue(skus(list(me)).contains(s), "still on the wishlist");
	}

	@Test
	public void movingSomethingNotOnTheWishlistOrToAnUnknownCart() {
		HttpHeaders me = customer();
		String s = newSku(), on = newSku();
		add(me, on);
		String c = cart(s, 1);
		assertEquals(HttpStatus.NOT_FOUND, testRestTemplate.exchange(WISHLIST + "/" + s + "/cart/" + c, HttpMethod.POST,
				new HttpEntity<>(me), String.class).getStatusCode());
		assertEquals(HttpStatus.NOT_FOUND, testRestTemplate.exchange(WISHLIST + "/" + on + "/cart/nosuchcart" + System.nanoTime(),
				HttpMethod.POST, new HttpEntity<>(me), String.class).getStatusCode());
		assertTrue(skus(list(me)).contains(on), "still on the wishlist");
	}

	// ---- the store's most wished products

	@Test
	public void theMostWishedProducts() {
		String x = newSku(), y = newSku(), z = newSku();
		for (int i = 0; i < 3; i++) {
			HttpHeaders c = customer();
			add(c, x);
			if (i < 2) {
				add(c, y);
			}
			if (i < 1) {
				add(c, z);
			}
		}
		ResponseEntity<List> r = testRestTemplate.exchange("/api/v1/private/wishlists/popular?store=DEFAULT", HttpMethod.GET,
				new HttpEntity<>(getHeader()), List.class);
		assertEquals(HttpStatus.OK, r.getStatusCode());
		List<Map> top = r.getBody();
		assertTrue(top.size() <= 10, "at most 10: " + top.size());
		assertEquals(x, top.get(0).get("sku"), "most wished first: " + top);
		assertEquals(3, ((Number) top.get(0).get("count")).intValue());
		assertEquals(y, top.get(1).get("sku"), "then: " + top);
		assertEquals(2, ((Number) top.get(1).get("count")).intValue());
		for (int i = 1; i < top.size(); i++) {
			int prev = ((Number) top.get(i - 1).get("count")).intValue(), cur = ((Number) top.get(i).get("count")).intValue();
			assertTrue(prev > cur || (prev == cur && ((String) top.get(i - 1).get("sku")).compareTo((String) top.get(i).get("sku")) < 0),
					"ordered by count, then sku: " + top);
		}
	}

	@Test
	public void theMostWishedListNeedsAnAdmin() {
		HttpHeaders me = customer();
		HttpStatus s = testRestTemplate.exchange("/api/v1/private/wishlists/popular?store=DEFAULT", HttpMethod.GET,
				new HttpEntity<>(me), String.class).getStatusCode();
		assertTrue(s == HttpStatus.UNAUTHORIZED || s == HttpStatus.FORBIDDEN, "with a customer's token: " + s);
	}
}
