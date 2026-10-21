package com.salesmanager.test.shop.hidden;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.math.BigDecimal;
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
public class HiddenManufacturerWebsiteTest extends ServicesTestSupport {

	private Map<String, Object> manufacturerJson(String code, String website) {
		Map<String, Object> desc = new HashMap<>();
		desc.put("language", "en");
		desc.put("name", code);
		List<Object> descs = new ArrayList<>();
		descs.add(desc);
		Map<String, Object> m = new HashMap<>();
		m.put("code", code);
		m.put("order", 0);
		m.put("descriptions", descs);
		if (website != null) {
			m.put("website", website);
		}
		return m;
	}

	private ResponseEntity<Map> create(String code, String website) {
		return testRestTemplate.postForEntity("/api/v1/private/manufacturer", new HttpEntity<>(manufacturerJson(code, website), getHeader()), Map.class);
	}

	private Map get(String url) {
		ResponseEntity<Map> r = testRestTemplate.exchange(url, HttpMethod.GET, new HttpEntity<>(getHeader()), Map.class);
		assertEquals(HttpStatus.OK, r.getStatusCode(), url);
		return r.getBody();
	}

	private Map fromList(String code) {
		List<Map> all = (List<Map>) get("/api/v1/manufacturers?count=1000").get("manufacturers");
		for (Map m : all) {
			if (code.equals(m.get("code"))) {
				return m;
			}
		}
		throw new AssertionError("manufacturer " + code + " not in list");
	}

	private long idOf(String code) {
		return ((Number) fromList(code).get("id")).longValue();
	}

	@Test
	public void websiteIsStoredAndReturnedByDetailAndList() throws Exception {
		assertEquals(HttpStatus.CREATED, create("hmwA", "https://acme.example.com").getStatusCode());
		long id = idOf("hmwA");
		assertEquals("https://acme.example.com", get("/api/v1/manufacturer/" + id).get("website"));
		assertEquals("https://acme.example.com", fromList("hmwA").get("website"));
	}

	@Test
	public void websiteIsOptional() throws Exception {
		assertEquals(HttpStatus.CREATED, create("hmwB", null).getStatusCode());
		assertEquals(null, get("/api/v1/manufacturer/" + idOf("hmwB")).get("website"));
	}

	@Test
	public void updateChangesWebsite() throws Exception {
		create("hmwC", "http://old.example.com");
		long id = idOf("hmwC");
		Map<String, Object> body = manufacturerJson("hmwC", "https://new.example.com");
		body.put("id", id);
		ResponseEntity<String> r = testRestTemplate.exchange("/api/v1/private/manufacturer/" + id, HttpMethod.PUT, new HttpEntity<>(body, getHeader()), String.class);
		assertTrue(r.getStatusCode().is2xxSuccessful());
		assertEquals("https://new.example.com", get("/api/v1/manufacturer/" + id).get("website"));
	}

	@Test
	public void invalidWebsiteIsRejectedAndNotStored() throws Exception {
		assertEquals(HttpStatus.BAD_REQUEST, create("hmwD", "acme.example.com").getStatusCode());
		List<Map> all = (List<Map>) get("/api/v1/manufacturers?count=1000").get("manufacturers");
		assertTrue(all.stream().noneMatch(m -> "hmwD".equals(m.get("code"))));
		create("hmwE", "https://ok.example.com");
		long id = idOf("hmwE");
		Map<String, Object> body = manufacturerJson("hmwE", "ftp://files.example.com");
		body.put("id", id);
		ResponseEntity<String> r = testRestTemplate.exchange("/api/v1/private/manufacturer/" + id, HttpMethod.PUT, new HttpEntity<>(body, getHeader()), String.class);
		assertEquals(HttpStatus.BAD_REQUEST, r.getStatusCode());
		assertEquals("https://ok.example.com", get("/api/v1/manufacturer/" + id).get("website"));
	}

	@Test
	public void productResponseCarriesManufacturerWebsite() throws Exception {
		create("hmwF", "https://maker.example.com");
		Map<String, Object> inventory = new HashMap<>();
		inventory.put("quantity", 5);
		inventory.put("sku", "hmwProd");
		Map<String, Object> price = new HashMap<>();
		price.put("defaultPrice", true);
		price.put("price", new BigDecimal(250));
		inventory.put("price", price);
		Map<String, Object> desc = new HashMap<>();
		desc.put("language", "en");
		desc.put("name", "hmwProd");
		List<Object> descs = new ArrayList<>();
		descs.add(desc);
		Map<String, Object> spec = new HashMap<>();
		spec.put("manufacturer", "hmwF");
		Map<String, Object> p = new HashMap<>();
		p.put("sku", "hmwProd");
		p.put("available", true);
		p.put("price", BigDecimal.TEN);
		p.put("quantity", 100);
		p.put("inventory", inventory);
		p.put("descriptions", descs);
		p.put("productSpecifications", spec);
		ResponseEntity<Map> created = testRestTemplate.postForEntity("/api/v1/private/product?store=DEFAULT", new HttpEntity<>(p, getHeader()), Map.class);
		assertTrue(created.getStatusCode().is2xxSuccessful(), "product create: " + created.getStatusCode());
		Map product = get("/api/v2/product/hmwProd");
		Map manufacturer = (Map) product.get("manufacturer");
		assertNotNull(manufacturer);
		assertEquals("https://maker.example.com", manufacturer.get("website"));
	}
}
