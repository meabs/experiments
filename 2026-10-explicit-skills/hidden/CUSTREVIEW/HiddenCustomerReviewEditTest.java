package com.salesmanager.test.shop.hidden;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.junit.jupiter.api.Test;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import com.salesmanager.test.shop.common.ServicesTestSupport;

/** Hidden acceptance test for task CUSTREVIEW: customer reviews can be edited; missing ones are 404; the rest keeps working. */
public class HiddenCustomerReviewEditTest extends ServicesTestSupport {

	@SuppressWarnings("rawtypes")
	private Long customer(String email) {
		Map<String, Object> b = new HashMap<>();
		b.put("firstName", "Cus");
		b.put("lastName", "Tomer");
		b.put("address", "1 Main Street");
		b.put("city", "Montreal");
		b.put("postalCode", "H1H1H1");
		b.put("stateProvince", "QC");
		b.put("country", "CA");
		Map<String, Object> c = new HashMap<>();
		c.put("emailAddress", email);
		c.put("password", "clear123");
		c.put("gender", "F");
		c.put("language", "en");
		c.put("billing", b);
		ResponseEntity<Map> r = testRestTemplate.exchange("/api/v1/private/customer", HttpMethod.POST, new HttpEntity<>(c, getHeader()), Map.class);
		assertTrue(r.getStatusCode().is2xxSuccessful());
		return ((Number) r.getBody().get("id")).longValue();
	}

	private Map<String, Object> body(Long reviewer, Long reviewed, double rating, String text) {
		Map<String, Object> rv = new HashMap<>();
		rv.put("customerId", reviewer);
		rv.put("reviewedCustomer", reviewed);
		rv.put("rating", rating);
		rv.put("description", text);
		rv.put("language", "en");
		rv.put("date", "2026-10-01");
		return rv;
	}

	@SuppressWarnings("rawtypes")
	private ResponseEntity<Map> review(Long reviewed, Long reviewer, double rating, String text) {
		return testRestTemplate.exchange("/api/v1/private/customers/" + reviewed + "/reviews", HttpMethod.POST,
				new HttpEntity<>(body(reviewer, reviewed, rating, text), getHeader()), Map.class);
	}

	@SuppressWarnings("rawtypes")
	private List<Map> reviews(Long reviewed) {
		ResponseEntity<List> r = testRestTemplate.exchange("/api/v1/customers/" + reviewed + "/reviews", HttpMethod.GET, new HttpEntity<>(getHeader()), List.class);
		assertEquals(HttpStatus.OK, r.getStatusCode());
		return r.getBody();
	}

	@SuppressWarnings({ "rawtypes", "unchecked" })
	@Test
	public void editingAReviewChangesIt() {
		Long seller = customer("crseller1@test.com");
		Long b1 = customer("crbuyer1@test.com");
		Long b2 = customer("crbuyer2@test.com");
		assertTrue(review(seller, b1, 5, "great buyer").getStatusCode().is2xxSuccessful());
		Long r2 = ((Number) review(seller, b2, 1, "slow payer").getBody().get("id")).longValue();
		ResponseEntity<String> e = testRestTemplate.exchange("/api/v1/private/customers/" + seller + "/reviews/" + r2, HttpMethod.PUT,
				new HttpEntity<>(body(b2, seller, 3, "paid in the end"), getHeader()), String.class);
		assertTrue(e.getStatusCode().is2xxSuccessful(), "edit: " + e.getStatusCode());
		List<Map> list = reviews(seller);
		assertEquals(2, list.size(), "editing must not add a review");
		Map edited = list.stream().filter(r -> ((Number) r.get("id")).longValue() == r2).findFirst().orElseThrow();
		assertEquals(3.0, ((Number) edited.get("rating")).doubleValue(), 0.001);
		assertEquals("paid in the end", edited.get("description"));
	}

	@Test
	public void missingReviewIsNotFound() {
		Long seller = customer("crseller2@test.com");
		Long b = customer("crbuyer3@test.com");
		assertEquals(HttpStatus.NOT_FOUND, testRestTemplate.exchange("/api/v1/private/customers/" + seller + "/reviews/987654", HttpMethod.PUT,
				new HttpEntity<>(body(b, seller, 3, "x"), getHeader()), String.class).getStatusCode());
		assertEquals(HttpStatus.NOT_FOUND, testRestTemplate.exchange("/api/v1/private/customers/" + seller + "/reviews/987654", HttpMethod.DELETE,
				new HttpEntity<>(getHeader()), String.class).getStatusCode());
	}

	@Test
	public void keepsRefusingASecondReviewFromTheSameCustomer() {
		Long seller = customer("crseller3@test.com");
		Long b = customer("crbuyer4@test.com");
		assertTrue(review(seller, b, 4, "first").getStatusCode().is2xxSuccessful());
		assertFalse(review(seller, b, 2, "second").getStatusCode().is2xxSuccessful(), "a second review by the same customer is refused");
		assertEquals(1, reviews(seller).size());
	}

	@SuppressWarnings("rawtypes")
	@Test
	public void keepsCreatingAndDeletingReviews() {
		Long seller = customer("crseller4@test.com");
		Long b = customer("crbuyer5@test.com");
		ResponseEntity<Map> r = review(seller, b, 4, "fine");
		assertTrue(r.getStatusCode().is2xxSuccessful());
		assertEquals(1, reviews(seller).size());
		assertTrue(testRestTemplate.exchange("/api/v1/private/customers/" + seller + "/reviews/" + r.getBody().get("id"), HttpMethod.DELETE,
				new HttpEntity<>(getHeader()), String.class).getStatusCode().is2xxSuccessful());
		assertEquals(0, reviews(seller).size());
	}
}
