package com.salesmanager.test.shop.hidden;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeSet;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import com.salesmanager.test.shop.common.ServicesTestSupport;

/** Hidden acceptance test for task HCUST: admin customer search (filters) with correct paging and totals. */
public class HiddenCustomerAdminSearchTest extends ServicesTestSupport {

	private static boolean created = false;

	private void create(String email, String first, String last, String country) {
		Map<String, Object> b = new HashMap<>();
		b.put("firstName", first);
		b.put("lastName", last);
		b.put("address", "1 Main Street");
		b.put("city", "Somewhere");
		b.put("postalCode", "12345");
		b.put("country", country);
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

	@BeforeEach
	public void customers() {
		if (!created) {
			for (int i = 0; i < 5; i++) create("quill" + i + "@hcu.test", "Ann", "Quillon", "CA");
			create("quillus1@hcu.test", "Bob", "Quillon", "US");
			create("zelda.quorn@hcu.test", "Zelda", "Quorn", "CA");
			create("yorick@hcu.test", "Yorick", "Bramble", "US");
			create("zelma.b@hcu.test", "Zelma", "Brambleton", "CA");
			created = true;
		}
	}

	@SuppressWarnings("rawtypes")
	private Map list(String query) {
		ResponseEntity<Map> r = testRestTemplate.exchange("/api/v1/private/customers?" + query, HttpMethod.GET, new HttpEntity<>(getHeader()), Map.class);
		assertEquals(HttpStatus.OK, r.getStatusCode());
		return r.getBody();
	}

	@SuppressWarnings({ "rawtypes", "unchecked" })
	private Set<String> emails(Map body) {
		Set<String> out = new TreeSet<>();
		for (Map c : (List<Map>) body.get("customers")) out.add((String) c.get("emailAddress"));
		return out;
	}

	private Set<String> set(String... v) {
		Set<String> s = new TreeSet<>();
		for (String x : v) s.add(x);
		return s;
	}

	@Test
	public void filtersMatchIgnoringCase() {
		assertEquals(set("zelda.quorn@hcu.test", "zelma.b@hcu.test"), emails(list("count=100&email=ZEL")));
		assertEquals(set("yorick@hcu.test", "zelma.b@hcu.test"), emails(list("count=100&name=bramble")));
		assertTrue(emails(list("count=100&country=US")).containsAll(set("yorick@hcu.test", "quillus1@hcu.test")));
	}

	@Test
	public void combinedFiltersMustAllMatch() {
		assertEquals(set("zelma.b@hcu.test"), emails(list("count=100&name=bramble&country=CA")));
		assertEquals(set(), emails(list("count=100&name=zel&country=US")));
		assertEquals(set(), emails(list("count=100&name=zel&email=yorick")));
	}

	@SuppressWarnings("rawtypes")
	@Test
	public void filteredResultsPageWithCorrectTotals() {
		String q = "name=quillon&country=CA&count=2";
		Map first = list(q + "&page=0");
		assertEquals(5, ((Number) first.get("recordsTotal")).intValue(), "recordsTotal counts matching customers");
		assertEquals(3, ((Number) first.get("totalPages")).intValue(), "totalPages");
		Set<String> seen = new TreeSet<>();
		int[] sizes = { 2, 2, 1 };
		for (int p = 0; p < 3; p++) {
			Set<String> page = emails(list(q + "&page=" + p));
			assertEquals(sizes[p], page.size(), "page " + p + ": " + page);
			for (String e : page) assertTrue(seen.add(e), e + " on two pages");
		}
		assertEquals(5, seen.size());
		assertTrue(emails(list(q + "&page=3")).isEmpty(), "page past the end is empty");
	}

	@SuppressWarnings("rawtypes")
	@Test
	public void unfilteredListPagesOverEveryone() {
		Set<String> all = emails(list("page=0&count=1000"));
		Map first = list("page=0&count=4");
		assertEquals(all.size(), ((Number) first.get("recordsTotal")).intValue());
		int pages = ((Number) first.get("totalPages")).intValue();
		assertEquals((all.size() + 3) / 4, pages);
		Set<String> seen = new TreeSet<>();
		for (int p = 0; p < pages; p++) seen.addAll(emails(list("page=" + p + "&count=4")));
		assertEquals(all, seen);
	}
}
