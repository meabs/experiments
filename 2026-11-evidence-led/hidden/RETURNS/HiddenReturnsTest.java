package com.salesmanager.test.shop.hidden;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.junit.jupiter.api.Test;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

/**
 * Hidden acceptance tests for ticket RETURNS: partial returns and refunds of orders, tax shared by subtotal with the
 * completing return taking the remainder, restock, status, history, transactions and the refunded total.
 */
@SuppressWarnings({ "rawtypes", "unchecked" })
public class HiddenReturnsTest extends HiddenOrderSupport {

	// ---- helpers

	private Map line(String sku, int qty) {
		Map l = new HashMap();
		l.put("sku", sku);
		l.put("quantity", qty);
		return l;
	}

	private Map body(boolean restock, String reason, Map... lines) {
		Map b = new HashMap();
		b.put("lines", Arrays.asList(lines));
		b.put("restock", restock);
		if (reason != null) {
			b.put("reason", reason);
		}
		return b;
	}

	private ResponseEntity<Map> postReturn(long orderId, Map body) {
		return testRestTemplate.postForEntity("/api/v1/private/orders/" + orderId + "/returns?store=DEFAULT",
				new HttpEntity<>(body, getHeader()), Map.class);
	}

	private Map returned(long orderId, Map body) {
		ResponseEntity<Map> r = postReturn(orderId, body);
		assertEquals(HttpStatus.CREATED, r.getStatusCode(), "recording a return: " + r.getBody());
		return r.getBody();
	}

	private HttpStatus postReturnStatus(long orderId, Map body) {
		return testRestTemplate.postForEntity("/api/v1/private/orders/" + orderId + "/returns?store=DEFAULT",
				new HttpEntity<>(body, getHeader()), String.class).getStatusCode();
	}

	private ResponseEntity<Map> refund(long orderId) {
		return testRestTemplate.postForEntity("/api/v1/private/orders/" + orderId + "/refund?store=DEFAULT",
				new HttpEntity<>(getHeader()), Map.class);
	}

	private List<Map> listReturns(long orderId) {
		ResponseEntity<List> r = testRestTemplate.exchange("/api/v1/private/orders/" + orderId + "/returns?store=DEFAULT",
				HttpMethod.GET, new HttpEntity<>(getHeader()), List.class);
		assertEquals(HttpStatus.OK, r.getStatusCode(), "listing returns");
		return asList(r.getBody());
	}

	private String status(long orderId) {
		return String.valueOf(getOrder(orderId).get("orderStatus"));
	}

	private static int quantityOf(Map ret, String sku) {
		int q = 0;
		for (Object o : (List) ret.get("lines")) {
			Map l = (Map) o;
			if (sku.equals(l.get("sku"))) {
				q += ((Number) l.get("quantity")).intValue();
			}
		}
		return q;
	}

	private static BigDecimal lineAmount(Map ret, String sku) {
		BigDecimal a = BigDecimal.ZERO.setScale(2);
		for (Object o : (List) ret.get("lines")) {
			Map l = (Map) o;
			if (sku.equals(l.get("sku"))) {
				a = a.add(money(l.get("amount")));
			}
		}
		return a;
	}

	private static BigDecimal share(BigDecimal tax, BigDecimal part, BigDecimal whole) {
		return tax.multiply(part).divide(whole, 2, RoundingMode.HALF_UP);
	}

	private static BigDecimal number(Object displayAmount) {
		String digits = String.valueOf(displayAmount).replaceAll("[^0-9.]", "");
		return new BigDecimal(digits).setScale(2, RoundingMode.HALF_UP);
	}

	private long order(String sku1, String price1, int qty1) {
		ensureTax();
		createProduct(sku1, price1, 50);
		return placeOrder(lines(sku1, qty1));
	}

	// ---- tests

	@Test
	public void aPartialReturnRefundsThePricePaidPlusItsShareOfTax() {
		String a = uniqueSku("ret");
		long id = order(a, "20.00", 3);
		Map before = getOrder(id);
		BigDecimal tax = taxOf(before);
		BigDecimal subtotal = totalLine(before, "order.total.subtotal");
		assertTrue(tax.signum() > 0, "the order should carry tax");

		Map r = returned(id, body(true, "damaged", line(a, 2)));
		assertNotNull(r.get("id"));
		assertEquals(id, ((Number) r.get("orderId")).longValue());
		assertEquals(2, quantityOf(r, a));
		assertEquals(m("40.00"), lineAmount(r, a));
		BigDecimal expectedTax = share(tax, m("40.00"), subtotal);
		assertEquals(expectedTax, money(r.get("tax")));
		assertEquals(m("40.00").add(expectedTax), money(r.get("amount")));
		assertEquals(Boolean.TRUE, r.get("restocked"));
		assertEquals("damaged", r.get("reason"));
		assertEquals(LocalDate.now().toString(), String.valueOf(r.get("date")));
	}

	@Test
	public void taxIsSharedAcrossProductsInProportionToTheirSubtotals() {
		ensureTax();
		String a = uniqueSku("reta");
		String b = uniqueSku("retb");
		createProduct(a, "10.00", 50);
		createProduct(b, "30.00", 50);
		long id = placeOrder(lines(a, 1, b, 1));
		Map before = getOrder(id);
		BigDecimal tax = taxOf(before);
		BigDecimal subtotal = totalLine(before, "order.total.subtotal");
		assertEquals(m("40.00"), subtotal);

		Map r = returned(id, body(false, null, line(b, 1)));
		assertEquals(m("30.00"), lineAmount(r, b));
		assertEquals(share(tax, m("30.00"), subtotal), money(r.get("tax")));
	}

	@Test
	public void theReturnThatCompletesTheOrderRefundsTheRestOfTheTax() {
		String a = uniqueSku("retr");
		long id = order(a, "3.33", 3);
		Map before = getOrder(id);
		BigDecimal tax = taxOf(before);
		BigDecimal subtotal = totalLine(before, "order.total.subtotal");

		Map r1 = returned(id, body(false, null, line(a, 1)));
		Map r2 = returned(id, body(false, null, line(a, 1)));
		Map r3 = returned(id, body(false, null, line(a, 1)));
		BigDecimal t1 = money(r1.get("tax"));
		BigDecimal t2 = money(r2.get("tax"));
		assertEquals(share(tax, m("3.33"), subtotal), t1);
		assertEquals(share(tax, m("3.33"), subtotal), t2);
		assertEquals(tax.subtract(t1).subtract(t2), money(r3.get("tax")), "the completing return takes the remainder");
		assertEquals(tax, t1.add(t2).add(money(r3.get("tax"))));
	}

	@Test
	public void aProductCannotBeReturnedMoreTimesThanItWasOrdered() {
		String a = uniqueSku("reto");
		long id = order(a, "12.00", 2);
		returned(id, body(false, null, line(a, 1)));
		assertEquals(HttpStatus.BAD_REQUEST, postReturnStatus(id, body(false, null, line(a, 2))));
		assertEquals(1, listReturns(id).size(), "a rejected return records nothing");
	}

	@Test
	public void linesWithTheSameSkuCountTogether() {
		String a = uniqueSku("retd");
		long id = order(a, "5.00", 3);
		assertEquals(HttpStatus.BAD_REQUEST, postReturnStatus(id, body(false, null, line(a, 2), line(a, 2))));
		assertEquals(0, listReturns(id).size());
		Map r = returned(id, body(false, null, line(a, 1), line(a, 1)));
		assertEquals(2, quantityOf(r, a));
		assertEquals(m("10.00"), lineAmount(r, a));
	}

	@Test
	public void invalidLinesAreRejected() {
		String a = uniqueSku("reti");
		long id = order(a, "8.00", 2);
		assertEquals(HttpStatus.BAD_REQUEST, postReturnStatus(id, body(false, null, line(uniqueSku("nothere"), 1))));
		assertEquals(HttpStatus.BAD_REQUEST, postReturnStatus(id, body(false, null, line(a, 0))));
		assertEquals(HttpStatus.BAD_REQUEST, postReturnStatus(id, body(false, null)));
		assertEquals(0, listReturns(id).size());
	}

	@Test
	public void anUnknownOrderGivesNotFound() {
		assertEquals(HttpStatus.NOT_FOUND, postReturnStatus(987654321L, body(false, null, line("x", 1))));
		assertEquals(HttpStatus.NOT_FOUND,
				testRestTemplate.postForEntity("/api/v1/private/orders/987654321/refund?store=DEFAULT",
						new HttpEntity<>(getHeader()), String.class).getStatusCode());
	}

	@Test
	public void restockPutsTheUnitsBackAndNoRestockLeavesStockAlone() {
		String a = uniqueSku("rets");
		long id = order(a, "7.00", 4);
		// relative to the stock after checkout: how checkout itself takes stock is not part of this ticket
		int afterOrder = stockOf(a);
		returned(id, body(true, null, line(a, 3)));
		assertEquals(afterOrder + 3, stockOf(a));
		returned(id, body(false, null, line(a, 1)));
		assertEquals(afterOrder + 3, stockOf(a));
	}

	@Test
	public void theOrderIsRefundedOnlyWhenEveryUnitHasBeenReturned() {
		ensureTax();
		String a = uniqueSku("retu");
		String b = uniqueSku("retv");
		createProduct(a, "4.00", 50);
		createProduct(b, "6.00", 50);
		long id = placeOrder(lines(a, 2, b, 1));
		String original = status(id);
		returned(id, body(false, null, line(a, 2)));
		assertEquals(original, status(id));
		returned(id, body(false, null, line(b, 1)));
		assertEquals("REFUNDED", status(id));
	}

	@Test
	public void aCanceledOrderCannotBeReturnedOrRefunded() {
		String a = uniqueSku("retc");
		long id = order(a, "9.00", 1);
		ResponseEntity<String> s = testRestTemplate.exchange("/api/v1/private/orders/" + id + "/status?store=DEFAULT",
				HttpMethod.PUT, new HttpEntity<>("CANCELED", getHeader()), String.class);
		assertTrue(s.getStatusCode().is2xxSuccessful(), "canceling the order: " + s.getBody());
		assertEquals(HttpStatus.CONFLICT, postReturnStatus(id, body(false, null, line(a, 1))));
		assertEquals(HttpStatus.CONFLICT, refund(id).getStatusCode());
	}

	@Test
	public void aRefundedOrderCannotBeReturnedAgain() {
		String a = uniqueSku("retf");
		long id = order(a, "9.50", 1);
		returned(id, body(false, null, line(a, 1)));
		assertEquals("REFUNDED", status(id));
		assertEquals(HttpStatus.CONFLICT, postReturnStatus(id, body(false, null, line(a, 1))));
		assertEquals(HttpStatus.CONFLICT, refund(id).getStatusCode());
	}

	@Test
	public void theRefundEndpointRefundsWhateverIsLeftWithoutRestocking() {
		ensureTax();
		String a = uniqueSku("retx");
		String b = uniqueSku("rety");
		createProduct(a, "11.00", 50);
		createProduct(b, "2.50", 50);
		long id = placeOrder(lines(a, 2, b, 3));
		Map before = getOrder(id);
		BigDecimal tax = taxOf(before);
		Map first = returned(id, body(true, null, line(a, 1)));
		int stockA = stockOf(a);
		int stockB = stockOf(b);

		ResponseEntity<Map> r = refund(id);
		assertEquals(HttpStatus.CREATED, r.getStatusCode(), "refund: " + r.getBody());
		Map rest = r.getBody();
		assertEquals(1, quantityOf(rest, a));
		assertEquals(3, quantityOf(rest, b));
		assertEquals(m("11.00"), lineAmount(rest, a));
		assertEquals(m("7.50"), lineAmount(rest, b));
		assertEquals(Boolean.FALSE, rest.get("restocked"));
		assertEquals("refund", rest.get("reason"));
		assertEquals(tax.subtract(money(first.get("tax"))), money(rest.get("tax")));
		assertEquals(m("18.50").add(money(rest.get("tax"))), money(rest.get("amount")));
		assertEquals("REFUNDED", status(id));
		assertEquals(stockA, stockOf(a));
		assertEquals(stockB, stockOf(b));
	}

	@Test
	public void returnsAreListedOldestFirst() {
		String a = uniqueSku("retl");
		long id = order(a, "1.25", 4);
		Map r1 = returned(id, body(false, "first", line(a, 1)));
		Map r2 = returned(id, body(false, "second", line(a, 2)));
		List<Map> list = listReturns(id);
		assertEquals(2, list.size());
		assertEquals(String.valueOf(r1.get("id")), String.valueOf(list.get(0).get("id")));
		assertEquals(String.valueOf(r2.get("id")), String.valueOf(list.get(1).get("id")));
		assertEquals("second", list.get(1).get("reason"));
		assertEquals(money(r2.get("amount")), money(list.get(1).get("amount")));
	}

	@Test
	public void theOrderShowsTheTotalRefundedAndKeepsItsOtherTotals() {
		String a = uniqueSku("rett");
		long id = order(a, "15.00", 3);
		Map before = getOrder(id);
		assertNull(totalLine(before, "order.total.refunded"), "nothing refunded yet");
		BigDecimal total = totalLine(before, "order.total.total");
		BigDecimal subtotal = totalLine(before, "order.total.subtotal");

		Map r1 = returned(id, body(false, null, line(a, 1)));
		Map r2 = returned(id, body(false, null, line(a, 1)));
		Map after = getOrder(id);
		assertEquals(money(r1.get("amount")).add(money(r2.get("amount"))), totalLine(after, "order.total.refunded"));
		assertEquals(total, totalLine(after, "order.total.total"));
		assertEquals(subtotal, totalLine(after, "order.total.subtotal"));
		assertEquals(taxOf(before), taxOf(after));
	}

	@Test
	public void everyReturnIsARefundTransaction() {
		String a = uniqueSku("retp");
		long id = order(a, "6.40", 2);
		Map r1 = returned(id, body(false, null, line(a, 1)));
		Map r2 = returned(id, body(false, null, line(a, 1)));
		ResponseEntity<List> t = testRestTemplate.exchange(
				"/api/v1/private/orders/" + id + "/payment/transactions?store=DEFAULT", HttpMethod.GET,
				new HttpEntity<>(getHeader()), List.class);
		assertEquals(HttpStatus.OK, t.getStatusCode());
		List<BigDecimal> refunds = new ArrayList<>();
		for (Map tx : asList(t.getBody())) {
			if ("REFUND".equals(tx.get("transactionType"))) {
				refunds.add(number(tx.get("amount")));
			}
		}
		refunds.sort(null);
		List<BigDecimal> expected = new ArrayList<>(Arrays.asList(money(r1.get("amount")), money(r2.get("amount"))));
		expected.sort(null);
		assertEquals(expected, refunds);
	}

	@Test
	public void everyReturnAddsAHistoryEntryNamingTheAmount() {
		String a = uniqueSku("reth");
		long id = order(a, "21.00", 2);
		ResponseEntity<List> h0 = testRestTemplate.exchange("/api/v1/private/orders/" + id + "/history?store=DEFAULT",
				HttpMethod.GET, new HttpEntity<>(getHeader()), List.class);
		int n0 = h0.getBody() == null ? 0 : h0.getBody().size();
		Map r1 = returned(id, body(false, null, line(a, 1)));
		Map r2 = returned(id, body(false, null, line(a, 1)));
		List<Map> h = asList(testRestTemplate.exchange("/api/v1/private/orders/" + id + "/history?store=DEFAULT",
				HttpMethod.GET, new HttpEntity<>(getHeader()), List.class).getBody());
		assertEquals(n0 + 2, h.size());
		String a1 = money(r1.get("amount")).toPlainString();
		String a2 = money(r2.get("amount")).toPlainString();
		boolean first = false;
		boolean second = false;
		for (Map e : h) {
			String c = String.valueOf(e.get("comments"));
			if (c.contains(a1) && !"REFUNDED".equals(e.get("orderStatus"))) {
				first = true;
			}
			if (c.contains(a2) && "REFUNDED".equals(e.get("orderStatus"))) {
				second = true;
			}
		}
		assertTrue(first, "an entry for the first return, status unchanged, naming " + a1 + ": " + h);
		assertTrue(second, "an entry for the completing return, status REFUNDED, naming " + a2 + ": " + h);
	}

	@Test
	public void returnsNeedAnAdmin() {
		String a = uniqueSku("retz");
		long id = order(a, "3.00", 1);
		ResponseEntity<String> r = testRestTemplate.postForEntity("/api/v1/private/orders/" + id + "/returns?store=DEFAULT",
				new HttpEntity<>(body(false, null, line(a, 1)), noAuth()), String.class);
		assertFalse(r.getStatusCode().is2xxSuccessful(), "no token: " + r.getStatusCode());
		assertEquals(0, listReturns(id).size());
		assertFalse(testRestTemplate.postForEntity("/api/v1/private/orders/" + id + "/refund?store=DEFAULT",
				new HttpEntity<>(noAuth()), String.class).getStatusCode().is2xxSuccessful());
		assertFalse("REFUNDED".equals(status(id)));
	}
}
