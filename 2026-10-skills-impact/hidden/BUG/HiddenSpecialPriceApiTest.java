package com.salesmanager.test.shop.hidden;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.context.SpringBootTest.WebEnvironment;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.test.context.junit.jupiter.SpringExtension;

import com.salesmanager.shop.application.ShopApplication;
import com.salesmanager.test.shop.common.ServicesTestSupport;

@SpringBootTest(classes = ShopApplication.class, webEnvironment = WebEnvironment.RANDOM_PORT)
@ExtendWith(SpringExtension.class)
@SuppressWarnings({ "unchecked", "rawtypes" })
public class HiddenSpecialPriceApiTest extends ServicesTestSupport {

	private Map product(String sku, Integer startOffset, Integer endOffset) {
		Map<String, Object> price = new HashMap<>();
		price.put("defaultPrice", true);
		price.put("price", new BigDecimal("100.00"));
		price.put("discounted", true);
		price.put("discountedPrice", new BigDecimal("80.00"));
		if (startOffset != null) {
			price.put("discountStartDate", LocalDate.now().plusDays(startOffset).toString());
		}
		if (endOffset != null) {
			price.put("discountEndDate", LocalDate.now().plusDays(endOffset).toString());
		}
		Map<String, Object> inventory = new HashMap<>();
		inventory.put("quantity", 5);
		inventory.put("sku", sku);
		inventory.put("price", price);
		Map<String, Object> desc = new HashMap<>();
		desc.put("language", "en");
		desc.put("name", sku);
		List<Object> descs = new ArrayList<>();
		descs.add(desc);
		Map<String, Object> spec = new HashMap<>();
		spec.put("manufacturer", com.salesmanager.core.model.catalog.product.manufacturer.Manufacturer.DEFAULT_MANUFACTURER);
		Map<String, Object> p = new HashMap<>();
		p.put("sku", sku);
		p.put("available", true);
		p.put("price", new BigDecimal("100.00"));
		p.put("quantity", 100);
		p.put("inventory", inventory);
		p.put("descriptions", descs);
		p.put("productSpecifications", spec);
		ResponseEntity<Map> created = testRestTemplate.postForEntity("/api/v1/private/product?store=DEFAULT", new HttpEntity<>(p, getHeader()), Map.class);
		assertTrue(created.getStatusCode().is2xxSuccessful(), "product create: " + created.getStatusCode());
		ResponseEntity<Map> r = testRestTemplate.exchange("/api/v2/product/" + sku, HttpMethod.GET, new HttpEntity<>(getHeader()), Map.class);
		assertEquals(HttpStatus.OK, r.getStatusCode());
		return r.getBody();
	}

	private boolean discounted(Map product) {
		return Boolean.TRUE.equals(product.get("discounted"));
	}

	@Test
	public void specialInsideItsWindowApplies() throws Exception {
		assertTrue(discounted(product("hspWindow", -1, 7)));
	}

	@Test
	public void specialWithOnlyAnEndDateApplies() throws Exception {
		assertTrue(discounted(product("hspEndOnly", null, 7)));
	}

	@Test
	public void expiredSpecialDoesNotApply() throws Exception {
		assertEquals(false, discounted(product("hspExpired", -10, -2)));
	}

	@Test
	public void futureSpecialDoesNotApply() throws Exception {
		assertEquals(false, discounted(product("hspFuture", 2, 9)));
	}

	@Test
	public void specialWithoutDatesApplies() throws Exception {
		assertTrue(discounted(product("hspNoDates", null, null)));
	}
}
