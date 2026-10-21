package com.salesmanager.test.shop.hidden;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.math.BigDecimal;
import java.util.Map;

import org.junit.jupiter.api.Test;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import com.salesmanager.shop.model.tax.PersistableTaxRate;
import com.salesmanager.shop.model.tax.TaxRateDescription;
import com.salesmanager.test.shop.common.ServicesTestSupport;

/** Hidden acceptance test for task TAXRATE: tax rates must lie between 0 and 100. */
public class HiddenTaxRateRangeTest extends ServicesTestSupport {

	private PersistableTaxRate rate(String code, BigDecimal value) {
		PersistableTaxRate r = new PersistableTaxRate();
		r.setCode(code);
		r.setCountry("US");
		r.setZone("NY");
		r.setPriority(0);
		r.setRate(value);
		r.setStore("DEFAULT");
		r.setTaxClass("DEFAULT");
		TaxRateDescription en = new TaxRateDescription();
		en.setLanguage("en");
		en.setName(code);
		r.getDescriptions().add(en);
		return r;
	}

	@SuppressWarnings("rawtypes")
	private ResponseEntity<Map> create(PersistableTaxRate r) {
		return testRestTemplate.exchange("/api/v1/private/tax/rate", HttpMethod.POST, new HttpEntity<>(r, getHeader()), Map.class);
	}

	@SuppressWarnings("rawtypes")
	private boolean exists(String code) {
		ResponseEntity<Map> r = testRestTemplate.exchange("/api/v1/private/tax/rate/unique?code=" + code, HttpMethod.GET,
				new HttpEntity<>(getHeader()), Map.class);
		return Boolean.TRUE.equals(r.getBody().get("exists"));
	}

	@Test
	public void ratesFromZeroToHundredAreAccepted() {
		for (String v : new String[] { "0", "7.5", "100" }) {
			String code = "hrok" + v.replace(".", "");
			assertTrue(create(rate(code, new BigDecimal(v))).getStatusCode().is2xxSuccessful(), "rate " + v);
			assertTrue(exists(code), "rate " + v + " should be stored");
		}
	}

	@Test
	public void rateAboveHundredIsRejected() {
		assertEquals(HttpStatus.BAD_REQUEST, create(rate("hrhigh", new BigDecimal("150"))).getStatusCode());
		assertFalse(exists("hrhigh"));
	}

	@Test
	public void negativeRateIsRejected() {
		assertEquals(HttpStatus.BAD_REQUEST, create(rate("hrneg", new BigDecimal("-1"))).getStatusCode());
		assertFalse(exists("hrneg"));
	}

	@Test
	public void missingRateIsRejected() {
		assertEquals(HttpStatus.BAD_REQUEST, create(rate("hrnull", null)).getStatusCode());
		assertFalse(exists("hrnull"));
	}

	@SuppressWarnings("rawtypes")
	@Test
	public void updateOutOfRangeIsRejectedAndLeavesRateUnchanged() {
		ResponseEntity<Map> created = create(rate("hrupd", new BigDecimal("5")));
		assertTrue(created.getStatusCode().is2xxSuccessful());
		Object id = created.getBody().get("id");
		ResponseEntity<Map> upd = testRestTemplate.exchange("/api/v1/private/tax/rate/" + id, HttpMethod.PUT,
				new HttpEntity<>(rate("hrupd", new BigDecimal("101")), getHeader()), Map.class);
		assertEquals(HttpStatus.BAD_REQUEST, upd.getStatusCode());
		ResponseEntity<Map> got = testRestTemplate.exchange("/api/v1/private/tax/rate/" + id, HttpMethod.GET,
				new HttpEntity<>(getHeader()), Map.class);
		assertEquals(0, new BigDecimal(String.valueOf(got.getBody().get("rate")).replaceAll("[^0-9.\\-]", ""))
				.compareTo(new BigDecimal("5")), "stored rate changed: " + got.getBody().get("rate"));
	}
}
