package com.salesmanager.test.shop.hidden;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

import org.junit.jupiter.api.Test;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import com.salesmanager.test.shop.common.ServicesTestSupport;

/** Hidden acceptance test for task CUSTPAGE: the admin customer list pages correctly and reports totals. */
public class HiddenCustomerPagingTest extends ServicesTestSupport {

	private void create(String email) {
		Map<String, Object> b = new HashMap<>();
		b.put("firstName", "Page");
		b.put("lastName", "Test");
		b.put("address", "1 Main Street");
		b.put("city", "Montreal");
		b.put("postalCode", "H1H1H1");
		b.put("country", "CA");
		Map<String, Object> c = new HashMap<>();
		c.put("emailAddress", email);
		c.put("password", "clear123");
		c.put("gender", "F");
		c.put("language", "en");
		c.put("storeCode", "DEFAULT");
		c.put("billing", b);
		assertTrue(testRestTemplate.exchange("/api/v1/private/customer", HttpMethod.POST, new HttpEntity<>(c, getHeader()), String.class)
				.getStatusCode().is2xxSuccessful());
	}

	@SuppressWarnings("rawtypes")
	private Map list(String query) {
		ResponseEntity<Map> r = testRestTemplate.exchange("/api/v1/private/customers?" + query, HttpMethod.GET,
				new HttpEntity<>(getHeader()), Map.class);
		assertEquals(HttpStatus.OK, r.getStatusCode());
		return r.getBody();
	}

	@SuppressWarnings({ "rawtypes", "unchecked" })
	private List<String> emails(Map body) {
		List<String> out = new ArrayList<>();
		for (Map c : (List<Map>) body.get("customers")) {
			out.add((String) c.get("emailAddress"));
		}
		return out;
	}

	@Test
	public void pagesCoverEveryCustomerOnceAndTotalsAreReported() {
		for (int i = 0; i < 5; i++) {
			create("hcpage" + i + "@test.com");
		}
		Set<String> all = new HashSet<>(emails(list("page=0&count=1000")));
		int total = all.size();
		assertTrue(total >= 5);

		Map first = list("page=0&count=2");
		assertEquals(total, ((Number) first.get("recordsTotal")).intValue(), "recordsTotal");
		int pages = ((Number) first.get("totalPages")).intValue();
		assertEquals((total + 1) / 2, pages, "totalPages for count=2");

		Set<String> seen = new HashSet<>();
		for (int p = 0; p < pages; p++) {
			List<String> page = emails(list("page=" + p + "&count=2"));
			int expected = (p < pages - 1) ? 2 : total - 2 * (pages - 1);
			assertEquals(expected, page.size(), "size of page " + p + ": " + page);
			for (String e : page) {
				assertTrue(seen.add(e), "customer " + e + " appears on more than one page");
			}
		}
		assertEquals(all, seen, "pages must cover every customer");
		assertTrue(emails(list("page=" + pages + "&count=2")).isEmpty(), "a page past the end is empty");
	}
}
