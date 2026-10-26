package com.salesmanager.test.shop.hidden;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.nio.charset.Charset;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;

import org.junit.jupiter.api.Test;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;

import com.salesmanager.core.model.customer.CustomerGender;
import com.salesmanager.shop.model.catalog.product.product.PersistableProduct;
import com.salesmanager.shop.model.customer.PersistableCustomer;
import com.salesmanager.shop.model.customer.address.Address;
import com.salesmanager.shop.model.entity.Entity;
import com.salesmanager.shop.store.security.AuthenticationRequest;
import com.salesmanager.shop.store.security.AuthenticationResponse;
import com.salesmanager.test.shop.common.ServicesTestSupport;

/**
 * Hidden acceptance test for feature PRODUCTQA: customers ask questions about products, admins answer (publish) or
 * reject them, and anyone can read the answered ones.
 */
@SuppressWarnings({ "rawtypes", "unchecked" })
public class HiddenProductQuestionsTest extends ServicesTestSupport {

	private static final AtomicInteger SEQ = new AtomicInteger();

	// ---- helpers

	private static final class P {
		final long id;
		final String sku;

		P(long id, String sku) {
			this.id = id;
			this.sku = sku;
		}
	}

	private P newProduct() {
		String sku = "qa" + SEQ.incrementAndGet() + "x" + System.nanoTime() % 100000;
		PersistableProduct p = product(sku);
		p.setSku(sku);
		ResponseEntity<Entity> r = testRestTemplate.postForEntity("/api/v1/private/product?store=DEFAULT",
				new HttpEntity<>(p, getHeader()), Entity.class);
		assertEquals(HttpStatus.CREATED, r.getStatusCode(), "creating product " + sku);
		return new P(r.getBody().getId(), sku);
	}

	/** Registers a new customer with the given first name and returns headers carrying their token. */
	private HttpHeaders customer(String firstName) {
		String email = "qa" + SEQ.incrementAndGet() + "_" + System.nanoTime() + "@test.com";
		PersistableCustomer c = new PersistableCustomer();
		c.setEmailAddress(email);
		c.setPassword("clear123");
		c.setGender(CustomerGender.F.name());
		c.setLanguage("en");
		Address billing = new Address();
		billing.setFirstName(firstName);
		billing.setLastName("Asker");
		billing.setCountry("BE");
		c.setBilling(billing);
		c.setStoreCode("DEFAULT");
		ResponseEntity<PersistableCustomer> r = testRestTemplate.postForEntity("/api/v1/customer/register",
				new HttpEntity<>(c, getHeader()), PersistableCustomer.class);
		assertEquals(HttpStatus.OK, r.getStatusCode(), "registering " + email);
		ResponseEntity<AuthenticationResponse> login = testRestTemplate.postForEntity("/api/v1/customer/login",
				new HttpEntity<>(new AuthenticationRequest(email, "clear123")), AuthenticationResponse.class);
		assertEquals(HttpStatus.OK, login.getStatusCode());
		HttpHeaders h = new HttpHeaders();
		h.setContentType(new MediaType("application", "json", Charset.forName("UTF-8")));
		h.add("Authorization", "Bearer " + login.getBody().getToken());
		return h;
	}

	private HttpHeaders anonymous() {
		HttpHeaders h = new HttpHeaders();
		h.setContentType(MediaType.APPLICATION_JSON);
		return h;
	}

	private static Map<String, Object> one(String key, Object value) {
		Map<String, Object> m = new HashMap<>();
		m.put(key, value);
		return m;
	}

	private ResponseEntity<Map> ask(HttpHeaders who, String sku, String text) {
		return testRestTemplate.exchange("/api/v1/auth/products/" + sku + "/questions?store=DEFAULT", HttpMethod.POST,
				new HttpEntity<>(one("text", text), who), Map.class);
	}

	private HttpStatus askStatus(HttpHeaders who, String sku, String text) {
		return testRestTemplate.exchange("/api/v1/auth/products/" + sku + "/questions?store=DEFAULT", HttpMethod.POST,
				new HttpEntity<>(one("text", text), who), String.class).getStatusCode();
	}

	private long askId(HttpHeaders who, String sku, String text) {
		ResponseEntity<Map> r = ask(who, sku, text);
		assertEquals(HttpStatus.CREATED, r.getStatusCode(), "asking " + text);
		return ((Number) r.getBody().get("id")).longValue();
	}

	private ResponseEntity<Map> answer(long id, String answer) {
		return testRestTemplate.exchange("/api/v1/private/questions/" + id + "/answer?store=DEFAULT", HttpMethod.PUT,
				new HttpEntity<>(one("answer", answer), getHeader()), Map.class);
	}

	private HttpStatus answerStatus(long id, String answer) {
		return testRestTemplate.exchange("/api/v1/private/questions/" + id + "/answer?store=DEFAULT", HttpMethod.PUT,
				new HttpEntity<>(one("answer", answer), getHeader()), String.class).getStatusCode();
	}

	private HttpStatus reject(long id) {
		return testRestTemplate.exchange("/api/v1/private/questions/" + id + "/reject?store=DEFAULT", HttpMethod.PUT,
				new HttpEntity<>(getHeader()), String.class).getStatusCode();
	}

	private Map published(String sku) {
		ResponseEntity<Map> r = testRestTemplate.exchange("/api/v1/products/" + sku + "/questions?store=DEFAULT", HttpMethod.GET,
				new HttpEntity<>(anonymous()), Map.class);
		assertEquals(HttpStatus.OK, r.getStatusCode());
		return r.getBody();
	}

	private static List<Long> ids(List<Map> l) {
		List<Long> out = new ArrayList<>();
		for (Map m : l) {
			out.add(((Number) m.get("id")).longValue());
		}
		return out;
	}

	private List<Long> moderation(String status) {
		ResponseEntity<List> r = testRestTemplate.exchange("/api/v1/private/questions?store=DEFAULT" + (status == null ? "" : "&status=" + status),
				HttpMethod.GET, new HttpEntity<>(getHeader()), List.class);
		assertEquals(HttpStatus.OK, r.getStatusCode());
		return ids(r.getBody());
	}

	private List<Map> mine(HttpHeaders who) {
		ResponseEntity<List> r = testRestTemplate.exchange("/api/v1/auth/customer/questions?store=DEFAULT", HttpMethod.GET,
				new HttpEntity<>(who), List.class);
		assertEquals(HttpStatus.OK, r.getStatusCode());
		return r.getBody();
	}

	// ---- asking

	@Test
	public void aQuestionWaitsForModeration() {
		P p = newProduct();
		ResponseEntity<Map> r = ask(customer("Ada"), p.sku, "  Is this waterproof?  ");
		assertEquals(HttpStatus.CREATED, r.getStatusCode());
		Map q = r.getBody();
		assertNotNull(q.get("id"));
		assertEquals(p.sku, q.get("sku"));
		assertEquals("Is this waterproof?", q.get("text"));
		assertEquals("PENDING", q.get("status"));
		assertEquals("Ada", q.get("askedBy"));
		assertNull(q.get("answer"));
		long id = ((Number) q.get("id")).longValue();
		assertTrue(moderation(null).contains(id), "in the default (pending) moderation list");
		assertTrue(moderation("PENDING").contains(id));
		assertEquals(0, ((Number) published(p.sku).get("count")).intValue(), "not public before an answer");
	}

	@Test
	public void questionLength() {
		P p = newProduct();
		HttpHeaders me = customer("Len");
		assertEquals(HttpStatus.BAD_REQUEST, askStatus(me, p.sku, "Too short"));
		assertEquals(HttpStatus.BAD_REQUEST, askStatus(me, p.sku, "    short?     "));
		assertEquals(HttpStatus.BAD_REQUEST, askStatus(me, p.sku, null));
		StringBuilder longer = new StringBuilder();
		for (int i = 0; i < 501; i++) {
			longer.append('a');
		}
		assertEquals(HttpStatus.BAD_REQUEST, askStatus(me, p.sku, longer.toString()));
		assertEquals(HttpStatus.CREATED, askStatus(me, p.sku, "Ten chars."));
		assertEquals(HttpStatus.CREATED, askStatus(me, p.sku, longer.substring(1)));
	}

	@Test
	public void unknownProduct() {
		assertEquals(HttpStatus.NOT_FOUND, askStatus(customer("Una"), "no-such-sku-" + System.nanoTime(), "Is this a real product?"));
		assertEquals(HttpStatus.NOT_FOUND, testRestTemplate.exchange("/api/v1/products/no-such-sku-" + System.nanoTime()
				+ "/questions?store=DEFAULT", HttpMethod.GET, new HttpEntity<>(anonymous()), String.class).getStatusCode());
	}

	@Test
	public void askingNeedsALoggedInCustomer() {
		P p = newProduct();
		HttpStatus s = askStatus(anonymous(), p.sku, "Can I ask without logging in?");
		assertTrue(s == HttpStatus.UNAUTHORIZED || s == HttpStatus.FORBIDDEN, "without a token: " + s);
	}

	@Test
	public void atMostThreeQuestionsWaitingPerCustomer() {
		P p = newProduct();
		HttpHeaders me = customer("Max");
		long first = askId(me, p.sku, "First question here?");
		askId(me, p.sku, "Second question here?");
		askId(me, p.sku, "Third question here?");
		assertEquals(HttpStatus.BAD_REQUEST, askStatus(me, p.sku, "Fourth question here?"));
		assertEquals(HttpStatus.CREATED, askStatus(customer("Other"), p.sku, "Another customer asks?"));
		assertEquals(HttpStatus.OK, answer(first, "Yes.").getStatusCode());
		assertEquals(HttpStatus.CREATED, askStatus(me, p.sku, "Fourth question again?"));
	}

	// ---- moderation

	@Test
	public void answeringPublishesTheQuestion() {
		P p = newProduct();
		long id = askId(customer("Bea"), p.sku, "Does it come in blue?");
		ResponseEntity<Map> r = answer(id, "  Yes, and in red.  ");
		assertEquals(HttpStatus.OK, r.getStatusCode());
		assertEquals("PUBLISHED", r.getBody().get("status"));
		assertEquals("Yes, and in red.", r.getBody().get("answer"));
		Map pub = published(p.sku);
		assertEquals(1, ((Number) pub.get("count")).intValue());
		Map q = ((List<Map>) pub.get("items")).get(0);
		assertEquals(id, ((Number) q.get("id")).longValue());
		assertEquals("Does it come in blue?", q.get("text"));
		assertEquals("Yes, and in red.", q.get("answer"));
		assertEquals("Bea", q.get("askedBy"));
		assertNotNull(q.get("answeredAt"));
		assertTrue(moderation("PUBLISHED").contains(id));
		assertTrue(!moderation("PENDING").contains(id), "no longer pending");
	}

	@Test
	public void aBlankAnswerIsRejected() {
		P p = newProduct();
		long id = askId(customer("Cy"), p.sku, "What size is the box?");
		assertEquals(HttpStatus.BAD_REQUEST, answerStatus(id, "   "));
		assertEquals(HttpStatus.BAD_REQUEST, answerStatus(id, null));
		assertTrue(moderation("PENDING").contains(id), "still pending");
	}

	@Test
	public void editingAnAnswerReplacesIt() {
		P p = newProduct();
		long id = askId(customer("Dee"), p.sku, "How heavy is it really?");
		answer(id, "Two kilos.");
		answer(id, "Two and a half kilos.");
		Map pub = published(p.sku);
		assertEquals(1, ((Number) pub.get("count")).intValue());
		assertEquals("Two and a half kilos.", ((List<Map>) pub.get("items")).get(0).get("answer"));
	}

	@Test
	public void rejectedQuestionsAreHiddenAndCannotBeAnswered() {
		P p = newProduct();
		HttpHeaders me = customer("Eve");
		long pending = askId(me, p.sku, "Is this question rude?");
		long answered = askId(me, p.sku, "Is this question fine?");
		answer(answered, "It is fine.");
		assertEquals(HttpStatus.OK, reject(pending));
		assertEquals(HttpStatus.OK, reject(answered));
		assertEquals(0, ((Number) published(p.sku).get("count")).intValue(), "rejecting removes a published question");
		assertTrue(moderation("REJECTED").containsAll(Arrays.asList(pending, answered)));
		assertEquals(HttpStatus.CONFLICT, answerStatus(pending, "Too late."));
	}

	@Test
	public void publicQuestionsShowTheMostRecentlyAnsweredFirst() throws Exception {
		P p = newProduct();
		HttpHeaders a = customer("Fay"), b = customer("Gus");
		long q1 = askId(a, p.sku, "Question number one?");
		long q2 = askId(b, p.sku, "Question number two?");
		long q3 = askId(a, p.sku, "Question number three?");
		long unanswered = askId(b, p.sku, "Question number four?");
		answer(q2, "Two.");
		Thread.sleep(20);
		answer(q1, "One.");
		Thread.sleep(20);
		answer(q3, "Three.");
		Map pub = published(p.sku);
		assertEquals(Arrays.asList(q3, q1, q2), ids((List<Map>) pub.get("items")));
		assertTrue(!ids((List<Map>) pub.get("items")).contains(unanswered));
	}

	@Test
	public void unknownQuestion() {
		assertEquals(HttpStatus.NOT_FOUND, answerStatus(987654321L, "Hello."));
		assertEquals(HttpStatus.NOT_FOUND, reject(987654321L));
	}

	@Test
	public void moderationNeedsAnAdminAndAKnownStatus() {
		HttpStatus s = testRestTemplate.exchange("/api/v1/private/questions?store=DEFAULT", HttpMethod.GET,
				new HttpEntity<>(customer("Hal")), String.class).getStatusCode();
		assertTrue(s == HttpStatus.UNAUTHORIZED || s == HttpStatus.FORBIDDEN, "with a customer's token: " + s);
		assertEquals(HttpStatus.BAD_REQUEST, testRestTemplate.exchange("/api/v1/private/questions?store=DEFAULT&status=LOST",
				HttpMethod.GET, new HttpEntity<>(getHeader()), String.class).getStatusCode());
	}

	// ---- the customer's own questions

	@Test
	public void customersSeeTheirOwnQuestionsNewestFirst() throws Exception {
		P p = newProduct(), q = newProduct();
		HttpHeaders me = customer("Ivy"), other = customer("Jo");
		long a = askId(me, p.sku, "My first question?");
		Thread.sleep(20);
		long b = askId(me, q.sku, "My second question?");
		Thread.sleep(20);
		long c = askId(me, p.sku, "My third question?");
		askId(other, p.sku, "Someone else asks?");
		answer(a, "Answered.");
		reject(b);
		List<Map> l = mine(me);
		assertEquals(Arrays.asList(c, b, a), ids(l));
		Map byId = new HashMap();
		for (Map m : l) {
			byId.put(((Number) m.get("id")).longValue(), m);
		}
		assertEquals("PUBLISHED", ((Map) byId.get(a)).get("status"));
		assertEquals("Answered.", ((Map) byId.get(a)).get("answer"));
		assertEquals("REJECTED", ((Map) byId.get(b)).get("status"));
		assertEquals("PENDING", ((Map) byId.get(c)).get("status"));
		assertEquals(1, mine(other).size());
	}

	@Test
	public void aProductWithQuestionsCanStillBeDeleted() {
		P p = newProduct();
		long id = askId(customer("Kim"), p.sku, "Will this be deleted?");
		answer(id, "Maybe.");
		ResponseEntity<String> d = testRestTemplate.exchange("/api/v1/private/product/" + p.id + "?store=DEFAULT",
				HttpMethod.DELETE, new HttpEntity<>(getHeader()), String.class);
		assertTrue(d.getStatusCode().is2xxSuccessful(), "deleting the product: " + d.getStatusCode());
		assertTrue(!moderation("PUBLISHED").contains(id), "its questions go with it");
	}
}
