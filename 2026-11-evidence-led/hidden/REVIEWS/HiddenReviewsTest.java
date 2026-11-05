package com.salesmanager.test.shop.hidden;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.math.BigDecimal;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.junit.jupiter.api.Test;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

/**
 * Hidden acceptance tests for ticket REVIEWS: the public list shows no personal details, reviews are validated, one per
 * customer and product, merchants can edit and delete them, and the product's rating always follows.
 */
@SuppressWarnings({ "rawtypes", "unchecked" })
public class HiddenReviewsTest extends HiddenOrderSupport {

	// ---- helpers

	private static final class Reviewer {
		final HttpHeaders headers;
		final long id;
		final String email;

		Reviewer(HttpHeaders headers, long id, String email) {
			this.headers = headers;
			this.id = id;
			this.email = email;
		}
	}

	private Reviewer reviewer() {
		String email = "rev" + SEQ.incrementAndGet() + "x" + System.nanoTime() % 100000 + "@example.com";
		HttpHeaders h = registerAndLogin(email, "Passw0rd!v");
		ResponseEntity<Map> me = testRestTemplate.exchange("/api/v1/auth/customer/profile?store=DEFAULT", HttpMethod.GET,
				new HttpEntity<>(h), Map.class);
		assertEquals(HttpStatus.OK, me.getStatusCode());
		return new Reviewer(h, ((Number) me.getBody().get("id")).longValue(), email);
	}

	private Map body(long productId, long customerId, Object rating, String text) {
		Map m = new HashMap();
		m.put("rating", rating);
		m.put("description", text);
		m.put("customerId", customerId);
		m.put("productId", productId);
		m.put("language", "en");
		return m;
	}

	private ResponseEntity<Map> review(Reviewer r, long productId, Object rating) {
		return testRestTemplate.postForEntity("/api/v1/auth/products/" + productId + "/reviews?store=DEFAULT",
				new HttpEntity<>(body(productId, r.id, rating, "review by " + r.id), r.headers), Map.class);
	}

	private long reviewed(Reviewer r, long productId, int rating) {
		ResponseEntity<Map> res = review(r, productId, rating);
		assertEquals(HttpStatus.CREATED, res.getStatusCode(), "reviewing: " + res.getBody());
		return ((Number) res.getBody().get("id")).longValue();
	}

	private ResponseEntity<String> publicList(long productId) {
		return testRestTemplate.exchange("/api/v1/product/" + productId + "/reviews?store=DEFAULT", HttpMethod.GET,
				new HttpEntity<>(noAuth()), String.class);
	}

	private List<Map> listed(long productId) {
		ResponseEntity<List> r = testRestTemplate.exchange("/api/v1/product/" + productId + "/reviews?store=DEFAULT",
				HttpMethod.GET, new HttpEntity<>(noAuth()), List.class);
		assertEquals(HttpStatus.OK, r.getStatusCode());
		return asList(r.getBody());
	}

	private String[] rating(String sku) {
		ResponseEntity<Map> r = testRestTemplate.exchange("/api/v2/product/" + sku + "?store=DEFAULT", HttpMethod.GET,
				new HttpEntity<>(getHeader()), Map.class);
		assertEquals(HttpStatus.OK, r.getStatusCode());
		BigDecimal avg = new BigDecimal(String.valueOf(r.getBody().get("rating"))).setScale(1, java.math.RoundingMode.HALF_UP);
		return new String[] { avg.toPlainString(), String.valueOf(((Number) r.getBody().get("ratingCount")).intValue()) };
	}

	private HttpStatus merchantUpdate(long productId, long reviewId, long customerId, int rating, String text) {
		return testRestTemplate.exchange("/api/v1/private/products/" + productId + "/reviews/" + reviewId + "?store=DEFAULT",
				HttpMethod.PUT, new HttpEntity<>(body(productId, customerId, rating, text), getHeader()), String.class)
				.getStatusCode();
	}

	private HttpStatus merchantDelete(long productId, long reviewId) {
		return testRestTemplate.exchange("/api/v1/private/products/" + productId + "/reviews/" + reviewId + "?store=DEFAULT",
				HttpMethod.DELETE, new HttpEntity<>(getHeader()), String.class).getStatusCode();
	}

	// ---- tests

	@Test
	public void thePublicListShowsNoPersonalDetails() {
		String a = uniqueSku("rva");
		long p = createProduct(a, "5.00", 10);
		Reviewer r = reviewer();
		reviewed(r, p, 4);
		ResponseEntity<String> list = publicList(p);
		assertEquals(HttpStatus.OK, list.getStatusCode());
		String text = String.valueOf(list.getBody());
		assertFalse(text.contains(r.email), "the reviewer's email is shown: " + text);
		assertFalse(text.contains("1 Main Street"), "the reviewer's street address is shown");
		assertFalse(text.contains("M5V 2T6"), "the reviewer's postal code is shown");
		assertFalse(text.contains("Lee"), "the reviewer's last name is shown");
		assertTrue(text.contains("Ann"), "the reviewer's first name is shown: " + text);
		Map entry = listed(p).get(0);
		assertEquals(4, ((Number) entry.get("rating")).intValue());
		assertTrue(entry.containsKey("id") && entry.containsKey("description") && entry.containsKey("date"));
	}

	@Test
	public void theRatingIsTheAverageOfTheReviews() {
		String a = uniqueSku("rvb");
		long p = createProduct(a, "5.00", 10);
		reviewed(reviewer(), p, 4);
		reviewed(reviewer(), p, 2);
		String[] r = rating(a);
		assertEquals("3.0", r[0]);
		assertEquals("2", r[1]);
	}

	@Test
	public void theAverageIsRoundedToOneDecimalHalvesUp() {
		String a = uniqueSku("rvc");
		long p = createProduct(a, "5.00", 10);
		reviewed(reviewer(), p, 5);
		reviewed(reviewer(), p, 5);
		reviewed(reviewer(), p, 4);
		assertEquals("4.7", rating(a)[0], "14 / 3 = 4.67");
		String b = uniqueSku("rvd");
		long q = createProduct(b, "5.00", 10);
		reviewed(reviewer(), q, 1);
		reviewed(reviewer(), q, 2);
		reviewed(reviewer(), q, 2);
		reviewed(reviewer(), q, 2);
		assertEquals("1.8", rating(b)[0], "7 / 4 = 1.75");
	}

	@Test
	public void aRatingOutsideOneToFiveIsRefused() {
		String a = uniqueSku("rve");
		long p = createProduct(a, "5.00", 10);
		Reviewer r = reviewer();
		for (Object bad : new Object[] { 0, 6, 9, -1, 3.5 }) {
			assertEquals(HttpStatus.BAD_REQUEST, review(r, p, bad).getStatusCode(), "rating " + bad);
		}
		assertEquals(0, listed(p).size(), "nothing is stored");
		assertEquals(HttpStatus.CREATED, review(r, p, 5).getStatusCode());
	}

	@Test
	public void aSecondReviewOfTheSameProductIsAConflict() {
		String a = uniqueSku("rvf");
		long p = createProduct(a, "5.00", 10);
		Reviewer r = reviewer();
		reviewed(r, p, 3);
		assertEquals(HttpStatus.CONFLICT, review(r, p, 5).getStatusCode());
		assertEquals(1, listed(p).size());
		assertEquals("3.0", rating(a)[0]);
	}

	@Test
	public void aReviewInAnotherCustomersNameIsForbidden() {
		String a = uniqueSku("rvg");
		long p = createProduct(a, "5.00", 10);
		Reviewer me = reviewer();
		Reviewer other = reviewer();
		ResponseEntity<Map> r = testRestTemplate.postForEntity("/api/v1/auth/products/" + p + "/reviews?store=DEFAULT",
				new HttpEntity<>(body(p, other.id, 1, "not mine"), me.headers), Map.class);
		assertEquals(HttpStatus.FORBIDDEN, r.getStatusCode());
		assertEquals(0, listed(p).size());
		assertEquals(HttpStatus.CREATED, review(other, p, 4).getStatusCode(), "the other customer can still review");
	}

	@Test
	public void aMerchantsChangeUpdatesTheRating() {
		String a = uniqueSku("rvh");
		long p = createProduct(a, "5.00", 10);
		Reviewer r = reviewer();
		long id = reviewed(r, p, 5);
		reviewed(reviewer(), p, 3);
		assertTrue(merchantUpdate(p, id, r.id, 1, "edited by the shop").is2xxSuccessful());
		assertEquals("2.0", rating(a)[0]);
		assertEquals("2", rating(a)[1]);
		boolean edited = false;
		for (Map e : listed(p)) {
			if ("edited by the shop".equals(e.get("description"))) {
				edited = true;
			}
		}
		assertTrue(edited, "the list shows the edited description");
	}

	@Test
	public void deletingAReviewUpdatesTheRating() {
		String a = uniqueSku("rvi");
		long p = createProduct(a, "5.00", 10);
		long first = reviewed(reviewer(), p, 5);
		long second = reviewed(reviewer(), p, 2);
		assertTrue(merchantDelete(p, first).is2xxSuccessful());
		assertEquals("2.0", rating(a)[0]);
		assertEquals("1", rating(a)[1]);
		assertTrue(merchantDelete(p, second).is2xxSuccessful());
		assertEquals("0.0", rating(a)[0]);
		assertEquals("0", rating(a)[1]);
		assertEquals(0, listed(p).size());
	}

	@Test
	public void changingOrDeletingAReviewThatIsNotThereIsNotFound() {
		String a = uniqueSku("rvj");
		String b = uniqueSku("rvk");
		long p = createProduct(a, "5.00", 10);
		long q = createProduct(b, "5.00", 10);
		Reviewer r = reviewer();
		long id = reviewed(r, p, 4);
		assertEquals(HttpStatus.NOT_FOUND, merchantUpdate(p, 987654321L, r.id, 3, "x"));
		assertEquals(HttpStatus.NOT_FOUND, merchantDelete(p, 987654321L));
		assertEquals(HttpStatus.NOT_FOUND, merchantUpdate(q, id, r.id, 3, "x"), "the review belongs to another product");
		assertEquals(HttpStatus.NOT_FOUND, merchantDelete(q, id));
		assertEquals(1, listed(p).size());
		assertEquals("4.0", rating(a)[0]);
	}

	@Test
	public void aProductWithNoReviewsShowsNoRating() {
		String a = uniqueSku("rvl");
		createProduct(a, "5.00", 10);
		String[] r = rating(a);
		assertEquals("0.0", r[0]);
		assertEquals("0", r[1]);
	}
}
