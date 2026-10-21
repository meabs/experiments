package com.salesmanager.test.shop.hidden;

import static org.junit.jupiter.api.Assertions.assertEquals;

import java.math.BigDecimal;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.junit.jupiter.api.Test;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import com.salesmanager.shop.model.catalog.product.product.PersistableProduct;
import com.salesmanager.shop.model.entity.Entity;
import com.salesmanager.test.shop.common.ServicesTestSupport;

/** Hidden acceptance test for task CARTCALC: cart item count and totals account for quantities. */
public class HiddenCartTotalsTest extends ServicesTestSupport {

	private void product125(String sku) {
		PersistableProduct p = product(sku);
		p.setSku(sku);
		p.setQuantity(100);
		ResponseEntity<Entity> r = testRestTemplate.postForEntity("/api/v1/private/product?store=DEFAULT", new HttpEntity<>(p, getHeader()), Entity.class);
		assertEquals(HttpStatus.CREATED, r.getStatusCode());
	}

	private Map<String, Object> item(String sku, int qty) {
		Map<String, Object> i = new HashMap<>();
		i.put("product", sku);
		i.put("quantity", qty);
		return i;
	}

	private BigDecimal money(Object o) {
		return new BigDecimal(String.valueOf(o));
	}

	@SuppressWarnings({ "rawtypes", "unchecked" })
	@Test
	public void twoLinesWithQuantities() {
		product125("hcalca");
		product125("hcalcb");
		ResponseEntity<Map> c = testRestTemplate.exchange("/api/v1/cart/", HttpMethod.POST, new HttpEntity<>(item("hcalca", 2), getHeader()), Map.class);
		assertEquals(HttpStatus.CREATED, c.getStatusCode());
		String code = (String) c.getBody().get("code");
		testRestTemplate.exchange("/api/v1/cart/" + code, HttpMethod.PUT, new HttpEntity<>(item("hcalcb", 3), getHeader()), Map.class);
		ResponseEntity<Map> g = testRestTemplate.exchange("/api/v1/cart/" + code, HttpMethod.GET, new HttpEntity<>(getHeader()), Map.class);
		assertEquals(HttpStatus.OK, g.getStatusCode());
		Map cart = g.getBody();
		assertEquals(5, ((Number) cart.get("quantity")).intValue(), "cart quantity is the number of units");
		assertEquals(0, money(cart.get("subtotal")).compareTo(new BigDecimal("625")), "subtotal " + cart.get("subtotal"));
		assertEquals(0, money(cart.get("total")).compareTo(new BigDecimal("625")), "total " + cart.get("total"));
		for (Map line : (List<Map>) cart.get("products")) {
			int q = ((Number) line.get("quantity")).intValue();
			assertEquals(0, money(line.get("subTotal")).compareTo(new BigDecimal(125 * q)), "line " + line.get("sku"));
		}
	}

	@SuppressWarnings("rawtypes")
	@Test
	public void singleUnit() {
		product125("hcalcc");
		ResponseEntity<Map> c = testRestTemplate.exchange("/api/v1/cart/", HttpMethod.POST, new HttpEntity<>(item("hcalcc", 1), getHeader()), Map.class);
		assertEquals(HttpStatus.CREATED, c.getStatusCode());
		assertEquals(1, ((Number) c.getBody().get("quantity")).intValue());
		assertEquals(0, money(c.getBody().get("total")).compareTo(new BigDecimal("125")));
	}
}
