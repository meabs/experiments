package com.salesmanager.test.shop.hidden;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

import org.junit.jupiter.api.Test;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import com.salesmanager.test.shop.common.ServicesTestSupport;

/** Hidden acceptance test for task PAGEVIS: shoppers do not see hidden pages; the back office still sees every page. */
public class HiddenPageVisibilityTest extends ServicesTestSupport {

	private void page(String code, boolean visible) {
		Map<String, Object> d = new HashMap<>();
		d.put("language", "en");
		d.put("name", code);
		d.put("title", code);
		d.put("description", "<p>" + code + "</p>");
		d.put("friendlyUrl", code);
		Map<String, Object> p = new HashMap<>();
		p.put("code", code);
		p.put("visible", visible);
		p.put("linkToMenu", true);
		p.put("descriptions", List.of(d));
		ResponseEntity<String> r = testRestTemplate.exchange("/api/v1/private/content/page", HttpMethod.POST, new HttpEntity<>(p, getHeader()), String.class);
		assertTrue(r.getStatusCode().is2xxSuccessful(), "create page: " + r.getStatusCode());
	}

	@SuppressWarnings({ "rawtypes", "unchecked" })
	private Set<String> codes(String url, HttpHeaders headers) {
		ResponseEntity<Map> r = testRestTemplate.exchange(url, HttpMethod.GET, new HttpEntity<>(headers), Map.class);
		assertEquals(HttpStatus.OK, r.getStatusCode(), url);
		List<Map> items = (List<Map>) r.getBody().get("items");
		return items.stream().map(i -> (String) i.get("code")).collect(Collectors.toSet());
	}

	@Test
	public void publicPageListHidesInvisiblePages() {
		page("pvshown1", true);
		page("pvhidden1", false);
		Set<String> c = codes("/api/v1/content/pages?page=0&count=100", new HttpHeaders());
		assertTrue(c.contains("pvshown1"), "visible page listed");
		assertFalse(c.contains("pvhidden1"), "invisible page must not be listed for shoppers");
	}

	@Test
	public void publicPageByCodeHidesInvisiblePages() {
		page("pvshown2", true);
		page("pvhidden2", false);
		assertEquals(HttpStatus.OK, testRestTemplate.exchange("/api/v1/content/pages/pvshown2", HttpMethod.GET,
				new HttpEntity<>(new HttpHeaders()), String.class).getStatusCode());
		assertEquals(HttpStatus.NOT_FOUND, testRestTemplate.exchange("/api/v1/content/pages/pvhidden2", HttpMethod.GET,
				new HttpEntity<>(new HttpHeaders()), String.class).getStatusCode());
	}

	@Test
	public void keepsAdminPageListShowingEveryPage() {
		page("pvshown3", true);
		page("pvhidden3", false);
		Set<String> c = codes("/api/v1/private/content/pages?page=0&count=100", getHeader());
		assertTrue(c.contains("pvshown3"));
		assertTrue(c.contains("pvhidden3"), "the back office must still list invisible pages");
	}

	@Test
	public void keepsAdminReadOfInvisiblePages() {
		page("pvhidden4", false);
		assertEquals(HttpStatus.OK, testRestTemplate.exchange("/api/v1/private/content/any/pvhidden4", HttpMethod.GET,
				new HttpEntity<>(getHeader()), String.class).getStatusCode());
	}
}
