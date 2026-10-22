package com.salesmanager.test.shop.hidden;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.junit.jupiter.api.Test;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import com.salesmanager.test.shop.common.ServicesTestSupport;

/** Hidden acceptance test for task BOXGET: a content box read by code comes back as it was stored. */
public class HiddenContentBoxTest extends ServicesTestSupport {

	private void box(String code, String html) {
		Map<String, Object> d = new HashMap<>();
		d.put("language", "en");
		d.put("name", code);
		d.put("description", html);
		Map<String, Object> b = new HashMap<>();
		b.put("code", code);
		b.put("visible", true);
		b.put("descriptions", List.of(d));
		assertTrue(testRestTemplate.exchange("/api/v1/private/content/box", HttpMethod.POST, new HttpEntity<>(b, getHeader()), String.class)
				.getStatusCode().is2xxSuccessful());
	}

	@SuppressWarnings({ "rawtypes" })
	private Map read(String code) {
		ResponseEntity<Map> r = testRestTemplate.exchange("/api/v1/content/boxes/" + code, HttpMethod.GET, new HttpEntity<>(new HttpHeaders()), Map.class);
		assertEquals(HttpStatus.OK, r.getStatusCode());
		return r.getBody();
	}

	@SuppressWarnings("rawtypes")
	@Test
	public void boxReadByCodeHasItsCodeIdAndVisibility() {
		box("bgfooter", "<p>Free shipping over $50</p>");
		Map b = read("bgfooter");
		assertEquals("bgfooter", b.get("code"));
		assertTrue(((Number) b.get("id")).longValue() > 0, "id");
		assertEquals(Boolean.TRUE, b.get("visible"));
	}

	@SuppressWarnings("rawtypes")
	@Test
	public void boxTextComesBackAsWritten() {
		box("bgpromo", "<p>Sale <b>today</b></p>");
		Map b = read("bgpromo");
		assertEquals("<p>Sale <b>today</b></p>", ((Map) b.get("description")).get("description"));
	}

	@SuppressWarnings({ "rawtypes", "unchecked" })
	@Test
	public void keepsBoxListAndUnknownBox() {
		box("bglist", "<p>listed</p>");
		ResponseEntity<Map> r = testRestTemplate.exchange("/api/v1/content/boxes?page=0&count=100", HttpMethod.GET, new HttpEntity<>(new HttpHeaders()), Map.class);
		assertEquals(HttpStatus.OK, r.getStatusCode());
		assertTrue(((List<Map>) r.getBody().get("items")).stream().anyMatch(i -> "bglist".equals(i.get("code"))));
		assertEquals(HttpStatus.NOT_FOUND, testRestTemplate.exchange("/api/v1/content/boxes/bgnosuchbox", HttpMethod.GET,
				new HttpEntity<>(new HttpHeaders()), String.class).getStatusCode());
	}
}
