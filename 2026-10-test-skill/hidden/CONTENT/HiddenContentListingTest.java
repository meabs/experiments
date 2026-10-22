package com.salesmanager.test.shop.hidden;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.junit.jupiter.api.Test;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import com.salesmanager.test.shop.common.ServicesTestSupport;

/** Hidden acceptance test for task CONTENT: content pages and boxes can be listed without paging parameters. */
public class HiddenContentListingTest extends ServicesTestSupport {

	private Map<String, Object> content(String code, String type) {
		Map<String, Object> d = new HashMap<>();
		d.put("language", "en");
		d.put("name", code + " name");
		d.put("title", code + " title");
		d.put("friendlyUrl", code + "-url");
		d.put("description", "<p>" + code + "</p>");
		List<Map<String, Object>> ds = new ArrayList<>();
		ds.add(d);
		Map<String, Object> c = new HashMap<>();
		c.put("code", code);
		c.put("visible", true);
		c.put("linkToMenu", true);
		c.put("contentType", type);
		c.put("descriptions", ds);
		return c;
	}

	private void create(String path, String code, String type) {
		ResponseEntity<String> r = testRestTemplate.exchange(path, HttpMethod.POST, new HttpEntity<>(content(code, type), getHeader()),
				String.class);
		assertTrue(r.getStatusCode().is2xxSuccessful(), "create " + code + ": " + r.getStatusCode() + " " + r.getBody());
	}

	private String get(String url) {
		ResponseEntity<String> r = testRestTemplate.exchange(url, HttpMethod.GET, new HttpEntity<>(getHeader()), String.class);
		assertEquals(HttpStatus.OK, r.getStatusCode(), url + ": " + r.getBody());
		return r.getBody();
	}

	@Test
	public void pagesCanBeListedWithAndWithoutPaging() {
		create("/api/v1/private/content/page", "hcpagea", "PAGE");
		assertTrue(get("/api/v1/content/pages").contains("hcpagea"));
		assertTrue(get("/api/v1/content/pages?page=0&count=50").contains("hcpagea"));
		assertTrue(get("/api/v1/private/content/pages").contains("hcpagea"));
	}

	@Test
	public void boxesCanBeListedWithAndWithoutPaging() {
		create("/api/v1/private/content/box", "hcboxa", "BOX");
		assertTrue(get("/api/v1/content/boxes").contains("hcboxa"));
		assertTrue(get("/api/v1/content/boxes?page=0&count=50").contains("hcboxa"));
	}
}
