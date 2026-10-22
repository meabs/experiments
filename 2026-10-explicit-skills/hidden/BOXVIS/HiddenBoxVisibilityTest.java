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

/** Hidden acceptance test for task BOXVIS: shoppers do not see hidden boxes; the back office still sees every box. */
public class HiddenBoxVisibilityTest extends ServicesTestSupport {

	private void box(String code, boolean visible) {
		Map<String, Object> d = new HashMap<>();
		d.put("language", "en");
		d.put("name", code);
		d.put("description", "<p>" + code + "</p>");
		Map<String, Object> b = new HashMap<>();
		b.put("code", code);
		b.put("visible", visible);
		b.put("descriptions", List.of(d));
		assertTrue(testRestTemplate.exchange("/api/v1/private/content/box", HttpMethod.POST, new HttpEntity<>(b, getHeader()), String.class)
				.getStatusCode().is2xxSuccessful());
	}

	@SuppressWarnings({ "rawtypes", "unchecked" })
	private Set<String> codes(String url, HttpHeaders headers) {
		ResponseEntity<Map> r = testRestTemplate.exchange(url, HttpMethod.GET, new HttpEntity<>(headers), Map.class);
		assertEquals(HttpStatus.OK, r.getStatusCode(), url);
		return ((List<Map>) r.getBody().get("items")).stream().map(i -> (String) i.get("code")).collect(Collectors.toSet());
	}

	@Test
	public void storefrontBoxListHidesHiddenBoxes() {
		box("bvshown1", true);
		box("bvhidden1", false);
		Set<String> c = codes("/api/v1/content/boxes?page=0&count=100", new HttpHeaders());
		assertTrue(c.contains("bvshown1"));
		assertFalse(c.contains("bvhidden1"), "hidden box must not reach the storefront");
	}

	@Test
	public void storefrontBoxByCodeHidesHiddenBoxes() {
		box("bvshown2", true);
		box("bvhidden2", false);
		assertEquals(HttpStatus.OK, testRestTemplate.exchange("/api/v1/content/boxes/bvshown2", HttpMethod.GET, new HttpEntity<>(new HttpHeaders()),
				String.class).getStatusCode());
		assertEquals(HttpStatus.NOT_FOUND, testRestTemplate.exchange("/api/v1/content/boxes/bvhidden2", HttpMethod.GET,
				new HttpEntity<>(new HttpHeaders()), String.class).getStatusCode());
	}

	@Test
	public void keepsBackOfficeListShowingEveryBox() {
		box("bvshown3", true);
		box("bvhidden3", false);
		Set<String> c = codes("/api/v1/private/content/boxes?page=0&count=100", getHeader());
		assertTrue(c.contains("bvshown3"));
		assertTrue(c.contains("bvhidden3"));
	}

	@Test
	public void keepsBackOfficeReadOfHiddenBoxes() {
		box("bvhidden4", false);
		assertEquals(HttpStatus.OK, testRestTemplate.exchange("/api/v1/private/content/boxes/bvhidden4", HttpMethod.GET,
				new HttpEntity<>(getHeader()), String.class).getStatusCode());
	}
}
