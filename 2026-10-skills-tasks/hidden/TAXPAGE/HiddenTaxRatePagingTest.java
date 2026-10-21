package com.salesmanager.test.shop.hidden;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import org.junit.jupiter.api.Test;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import com.salesmanager.shop.model.tax.PersistableTaxRate;
import com.salesmanager.shop.model.tax.TaxRateDescription;
import com.salesmanager.test.shop.common.ServicesTestSupport;

/** Hidden acceptance test for task TAXPAGE: the tax rate list honours page and count, sorted by code. */
public class HiddenTaxRatePagingTest extends ServicesTestSupport {

	private void create(String code) {
		PersistableTaxRate r = new PersistableTaxRate();
		r.setCode(code);
		r.setCountry("US");
		r.setZone("NY");
		r.setPriority(0);
		r.setRate(new BigDecimal("5"));
		r.setStore("DEFAULT");
		r.setTaxClass("DEFAULT");
		TaxRateDescription en = new TaxRateDescription();
		en.setLanguage("en");
		en.setName(code);
		r.getDescriptions().add(en);
		assertTrue(testRestTemplate.exchange("/api/v1/private/tax/rate", HttpMethod.POST, new HttpEntity<>(r, getHeader()), String.class)
				.getStatusCode().is2xxSuccessful());
	}

	@SuppressWarnings("rawtypes")
	private Map list(int page, int count) {
		ResponseEntity<Map> r = testRestTemplate.exchange("/api/v1/private/tax/rates?page=" + page + "&count=" + count, HttpMethod.GET,
				new HttpEntity<>(getHeader()), Map.class);
		assertEquals(HttpStatus.OK, r.getStatusCode());
		return r.getBody();
	}

	@SuppressWarnings({ "rawtypes", "unchecked" })
	private List<String> codes(Map body) {
		List<String> out = new ArrayList<>();
		for (Map i : (List<Map>) body.get("items")) out.add((String) i.get("code"));
		return out;
	}

	@Test
	public void pagesFollowCodeOrderAndTotalsAreReported() {
		create("htp-e");
		create("htp-a");
		create("htp-c");
		create("htp-b");
		create("htp-d");
		List<String> all = codes(list(0, 1000));
		int total = all.size();
		assertTrue(total >= 5);
		List<String> sorted = new ArrayList<>(all);
		sorted.sort(String::compareTo);
		assertEquals(sorted, all, "list must be sorted by code");

		Map first = list(0, 2);
		assertEquals(total, ((Number) first.get("recordsTotal")).intValue(), "recordsTotal");
		int pages = ((Number) first.get("totalPages")).intValue();
		assertEquals((total + 1) / 2, pages, "totalPages");
		List<String> joined = new ArrayList<>();
		for (int p = 0; p < pages; p++) {
			List<String> page = codes(list(p, 2));
			assertTrue(page.size() <= 2, "page " + p + " too big: " + page);
			joined.addAll(page);
		}
		assertEquals(sorted, joined, "pages joined must equal the full sorted list");
		assertTrue(codes(list(pages, 2)).isEmpty(), "page past the end is empty");
	}
}
