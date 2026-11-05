package com.salesmanager.test.shop.hidden;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import org.junit.jupiter.api.Test;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

/**
 * Hidden acceptance tests for ticket PRODUCTDELETE: deleting a product leaves carts usable without it and orders
 * readable, by the merchant and the customer, exactly as bought.
 */
@SuppressWarnings({ "rawtypes", "unchecked" })
public class HiddenProductDeleteTest extends HiddenOrderSupport {

	// ---- helpers

	private Map item(String sku, int qty) {
		Map m = new HashMap();
		m.put("product", sku);
		m.put("quantity", qty);
		return m;
	}

	private void delete(long productId) {
		ResponseEntity<String> r = testRestTemplate.exchange("/api/v1/private/product/" + productId + "?store=DEFAULT",
				HttpMethod.DELETE, new HttpEntity<>(getHeader()), String.class);
		assertTrue(r.getStatusCode().is2xxSuccessful(), "deleting product " + productId + ": " + r.getStatusCode());
	}

	private ResponseEntity<Map> cart(String code) {
		return testRestTemplate.exchange("/api/v1/cart/" + code + "?store=DEFAULT", HttpMethod.GET,
				new HttpEntity<>(getHeader()), Map.class);
	}

	private static Map<String, Integer> quantities(Map cart) {
		Map<String, Integer> q = new LinkedHashMap<>();
		Object products = cart.get("products");
		if (products != null) {
			for (Object o : (List) products) {
				Map p = (Map) o;
				q.put((String) p.get("sku"), ((Number) p.get("quantity")).intValue());
			}
		}
		return q;
	}

	/** What the order shows of each product: sku, name, quantity, price and subtotal. */
	private static Map<String, List<Object>> lines(Map order) {
		Map<String, List<Object>> out = new LinkedHashMap<>();
		Object products = order.get("products");
		assertNotNull(products, "the order lists its products: " + order);
		for (Object o : (List) products) {
			Map p = (Map) o;
			List<Object> l = new ArrayList<>();
			l.add(p.get("productName"));
			l.add(((Number) p.get("orderedQuantity")).intValue());
			l.add(p.get("price"));
			l.add(p.get("subTotal"));
			out.put((String) p.get("sku"), l);
		}
		return out;
	}

	private static Map<String, BigDecimal> totals(Map order) {
		Map<String, BigDecimal> t = new LinkedHashMap<>();
		for (Object o : (List) order.get("totals")) {
			Map m = (Map) o;
			t.put(String.valueOf(m.get("code")), money(m.get("value")));
		}
		return t;
	}

	private Map orderAsCustomer(HttpHeaders h, long id) {
		ResponseEntity<Map> r = testRestTemplate.exchange("/api/v1/auth/orders/" + id + "?store=DEFAULT", HttpMethod.GET,
				new HttpEntity<>(h), Map.class);
		assertEquals(HttpStatus.OK, r.getStatusCode(), "customer reading order " + id);
		return r.getBody();
	}

	private static boolean listsOrder(Map list, long id) {
		Object orders = list.get("orders");
		if (orders == null) {
			return false;
		}
		for (Object o : (List) orders) {
			if (((Number) ((Map) o).get("id")).longValue() == id) {
				return true;
			}
		}
		return false;
	}

	// ---- tests

	@Test
	public void aCartIsReadWithoutTheDeletedProduct() {
		String a = uniqueSku("pda");
		String b = uniqueSku("pdb");
		createProduct(a, "10.00", 20);
		long idb = createProduct(b, "5.00", 20);
		String code = cartWith(lines(a, 2, b, 1));
		delete(idb);
		ResponseEntity<Map> r = cart(code);
		assertEquals(HttpStatus.OK, r.getStatusCode());
		Map c = r.getBody();
		Map<String, Integer> q = quantities(c);
		assertEquals(1, q.size(), "only the product left: " + q);
		assertEquals(Integer.valueOf(2), q.get(a));
		assertEquals(m("20.00"), money(c.get("subtotal")));
		assertEquals(m("20.00"), money(c.get("total")));
		assertEquals(2, ((Number) c.get("quantity")).intValue());
	}

	@Test
	public void aCartWhoseOnlyProductWasDeletedIsEmpty() {
		String a = uniqueSku("pdo");
		long ida = createProduct(a, "9.00", 20);
		String code = cartWith(lines(a, 3));
		delete(ida);
		ResponseEntity<Map> r = cart(code);
		assertEquals(HttpStatus.OK, r.getStatusCode());
		assertEquals(0, quantities(r.getBody()).size());
		assertEquals(m("0.00"), money(r.getBody().get("total")));
	}

	@Test
	public void theCartCanStillBeChanged() {
		String a = uniqueSku("pdc");
		String b = uniqueSku("pdd");
		String c = uniqueSku("pde");
		createProduct(a, "3.00", 20);
		long idb = createProduct(b, "4.00", 20);
		createProduct(c, "6.00", 20);
		String code = cartWith(lines(a, 1, b, 1));
		delete(idb);
		ResponseEntity<String> put = testRestTemplate.exchange("/api/v1/cart/" + code + "?store=DEFAULT", HttpMethod.PUT,
				new HttpEntity<>(item(a, 3), getHeader()), String.class);
		assertTrue(put.getStatusCode().is2xxSuccessful(), "changing a quantity: " + put.getStatusCode());
		ResponseEntity<String> multi = testRestTemplate.postForEntity("/api/v1/cart/" + code + "/multi?store=DEFAULT",
				new HttpEntity<>(new Map[] { item(a, 2), item(c, 1) }, getHeader()), String.class);
		assertTrue(multi.getStatusCode().is2xxSuccessful(), "changing several: " + multi.getStatusCode());
		Map<String, Integer> q = quantities(cart(code).getBody());
		assertEquals(Integer.valueOf(2), q.get(a));
		assertEquals(Integer.valueOf(1), q.get(c));
		assertFalse(q.containsKey(b));
	}

	@Test
	public void theCartCanStillBeCheckedOutWithoutTheDeletedProduct() {
		ensureTax();
		String a = uniqueSku("pdf");
		String b = uniqueSku("pdg");
		createProduct(a, "10.00", 20);
		long idb = createProduct(b, "7.00", 20);
		String code = cartWith(lines(a, 2, b, 2));
		delete(idb);
		ResponseEntity<Map> r = checkoutCart(code, "pd" + SEQ.incrementAndGet() + "@example.com");
		long id = ((Number) r.getBody().get("id")).longValue();
		Map order = getOrder(id);
		Map<String, List<Object>> l = lines(order);
		assertEquals(1, l.size(), "only the product left is ordered: " + l.keySet());
		assertTrue(l.containsKey(a));
		assertEquals(m("20.00"), totalLine(order, "order.total.subtotal"));
	}

	@Test
	public void theDeletedProductCantBeAddedToACart() {
		String a = uniqueSku("pdh");
		String b = uniqueSku("pdi");
		createProduct(a, "1.00", 20);
		long idb = createProduct(b, "1.00", 20);
		delete(idb);
		assertEquals(HttpStatus.NOT_FOUND, testRestTemplate.postForEntity("/api/v1/cart/?store=DEFAULT",
				new HttpEntity<>(item(b, 1), getHeader()), String.class).getStatusCode());
		String code = cartWith(lines(a, 1));
		assertEquals(HttpStatus.NOT_FOUND, testRestTemplate.exchange("/api/v1/cart/" + code + "?store=DEFAULT",
				HttpMethod.PUT, new HttpEntity<>(item(b, 1), getHeader()), String.class).getStatusCode());
		assertEquals(1, quantities(cart(code).getBody()).size());
	}

	@Test
	public void theMerchantStillSeesTheOrderExactlyAsBought() {
		ensureTax();
		String a = uniqueSku("pdj");
		String b = uniqueSku("pdk");
		createProduct(a, "12.00", 20);
		long idb = createProduct(b, "3.50", 20);
		long id = placeOrder(lines(a, 1, b, 4));
		Map before = getOrder(id);
		delete(idb);
		ResponseEntity<Map> r = testRestTemplate.exchange("/api/v1/private/orders/" + id + "?store=DEFAULT",
				HttpMethod.GET, new HttpEntity<>(getHeader()), Map.class);
		assertEquals(HttpStatus.OK, r.getStatusCode(), "reading the order after the delete");
		Map after = r.getBody();
		assertEquals(lines(before), lines(after));
		assertEquals(totals(before), totals(after));
	}

	@Test
	public void theMerchantsOrderListStillWorks() {
		String a = uniqueSku("pdl");
		long ida = createProduct(a, "2.00", 20);
		long id = placeOrder(lines(a, 2));
		delete(ida);
		ResponseEntity<Map> r = testRestTemplate.exchange("/api/v1/private/orders?store=DEFAULT&count=1000",
				HttpMethod.GET, new HttpEntity<>(getHeader()), Map.class);
		assertEquals(HttpStatus.OK, r.getStatusCode());
		assertTrue(listsOrder(r.getBody(), id), "the list includes the order");
	}

	@Test
	public void theCustomerStillSeesTheirOrderExactlyAsBought() {
		String a = uniqueSku("pdm");
		String b = uniqueSku("pdn");
		createProduct(a, "5.00", 20);
		long idb = createProduct(b, "2.00", 20);
		HttpHeaders h = registerAndLogin("pdcust" + SEQ.incrementAndGet() + "@example.com", "Passw0rd!d");
		ResponseEntity<Map> c = testRestTemplate.postForEntity("/api/v1/cart/?store=DEFAULT",
				new HttpEntity<>(item(a, 1), h), Map.class);
		String code = (String) c.getBody().get("code");
		testRestTemplate.exchange("/api/v1/cart/" + code + "?store=DEFAULT", HttpMethod.PUT,
				new HttpEntity<>(item(b, 2), h), String.class);
		ensureTax();
		ResponseEntity<String> co = customerCheckout(h, code, "9.00", "10.17");
		assertTrue(co.getStatusCode().is2xxSuccessful(), "customer checkout: " + co.getBody());
		ResponseEntity<Map> list0 = testRestTemplate.exchange("/api/v1/auth/orders?store=DEFAULT", HttpMethod.GET,
				new HttpEntity<>(h), Map.class);
		long id = ((Number) ((Map) ((List) list0.getBody().get("orders")).get(0)).get("id")).longValue();
		Map before = orderAsCustomer(h, id);
		delete(idb);
		Map after = orderAsCustomer(h, id);
		assertEquals(lines(before), lines(after));
		assertEquals(totals(before), totals(after));
		ResponseEntity<Map> list = testRestTemplate.exchange("/api/v1/auth/orders?store=DEFAULT", HttpMethod.GET,
				new HttpEntity<>(h), Map.class);
		assertEquals(HttpStatus.OK, list.getStatusCode());
		assertTrue(listsOrder(list.getBody(), id));
	}

	@Test
	public void theOrdersStatusCanStillBeChanged() {
		String a = uniqueSku("pdp");
		long ida = createProduct(a, "4.00", 20);
		long id = placeOrder(lines(a, 1));
		delete(ida);
		ResponseEntity<String> s = testRestTemplate.exchange("/api/v1/private/orders/" + id + "/status?store=DEFAULT",
				HttpMethod.PUT, new HttpEntity<>("PROCESSED", getHeader()), String.class);
		assertTrue(s.getStatusCode().is2xxSuccessful(), "changing status: " + s.getStatusCode() + " " + s.getBody());
		assertEquals("PROCESSED", getOrder(id).get("orderStatus"));
	}

	@Test
	public void aDeletedProductIsNotFound() {
		String a = uniqueSku("pdq");
		long ida = createProduct(a, "4.00", 20);
		delete(ida);
		assertEquals(HttpStatus.NOT_FOUND, testRestTemplate.exchange("/api/v2/product/" + a + "?store=DEFAULT",
				HttpMethod.GET, new HttpEntity<>(getHeader()), String.class).getStatusCode());
	}

	@Test
	public void deletingAProductChangesNothingAboutTheOthers() {
		String a = uniqueSku("pdr");
		String b = uniqueSku("pds");
		createProduct(a, "8.25", 17);
		long idb = createProduct(b, "1.00", 20);
		String code = cartWith(lines(a, 2, b, 1));
		ResponseEntity<Map> before = testRestTemplate.exchange("/api/v2/product/" + a + "?store=DEFAULT", HttpMethod.GET,
				new HttpEntity<>(getHeader()), Map.class);
		delete(idb);
		ResponseEntity<Map> after = testRestTemplate.exchange("/api/v2/product/" + a + "?store=DEFAULT", HttpMethod.GET,
				new HttpEntity<>(getHeader()), Map.class);
		assertEquals(HttpStatus.OK, after.getStatusCode());
		for (String k : new String[] { "quantity", "price", "sku", "available", "finalPrice" }) {
			assertEquals(before.getBody().get(k), after.getBody().get(k), k);
		}
		assertEquals(Integer.valueOf(2), quantities(cart(code).getBody()).get(a));
	}
}
