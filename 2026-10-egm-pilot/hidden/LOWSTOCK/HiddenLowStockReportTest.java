package com.salesmanager.test.shop.hidden;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

import org.junit.jupiter.api.Test;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;

import com.salesmanager.shop.model.catalog.product.product.PersistableProduct;
import com.salesmanager.shop.model.entity.Entity;
import com.salesmanager.shop.model.references.PersistableAddress;
import com.salesmanager.shop.model.store.PersistableMerchantStore;
import com.salesmanager.test.shop.common.ServicesTestSupport;

/** Hidden acceptance test for feature LOWSTOCK: GET /api/v1/private/products/low-stock. */
@SuppressWarnings({ "rawtypes", "unchecked" })
public class HiddenLowStockReportTest extends ServicesTestSupport {

	private static final String REPORT = "/api/v1/private/products/low-stock";

	private long create(String sku, int quantity, String store) {
		PersistableProduct p = product(sku);
		p.setSku(sku);
		p.getInventory().setQuantity(quantity);
		ResponseEntity<Entity> r = testRestTemplate.postForEntity("/api/v1/private/product?store=" + store,
				new HttpEntity<>(p, getHeader()), Entity.class);
		assertEquals(HttpStatus.CREATED, r.getStatusCode(), "creating " + sku);
		return r.getBody().getId();
	}

	private long create(String sku, int quantity) {
		return create(sku, quantity, "DEFAULT");
	}

	private ResponseEntity<Map> call(String query, HttpHeaders headers) {
		return testRestTemplate.exchange(REPORT + "?" + query, HttpMethod.GET, new HttpEntity<>(headers), Map.class);
	}

	private Map report(String query) {
		ResponseEntity<Map> r = call(query, getHeader());
		assertEquals(HttpStatus.OK, r.getStatusCode(), "report " + query);
		assertNotNull(r.getBody());
		return r.getBody();
	}

	private static List<Map> items(Map body) {
		Object items = body.get("items");
		assertNotNull(items, "items");
		return (List<Map>) items;
	}

	private static Map item(Map body, String sku) {
		return items(body).stream().filter(i -> sku.equals(i.get("sku"))).findFirst().orElse(null);
	}

	private static long num(Object o) {
		return ((Number) o).longValue();
	}

	@Test
	public void itemCarriesIdSkuAndStock() {
		long id = create("hlsitem", 4);
		Map i = item(report("store=DEFAULT&threshold=4&count=1000"), "hlsitem");
		assertNotNull(i, "a product with stock 4 is listed at threshold 4");
		assertEquals(4L, num(i.get("stock")));
		assertEquals(id, num(i.get("id")));
		assertEquals(null, item(report("store=DEFAULT&threshold=3&count=1000"), "hlsitem"),
				"a product with stock 4 is not listed at threshold 3");
	}

	@Test
	public void atThresholdIsListedAndAboveIsNot() {
		create("hlsat", 3);
		create("hlsabove", 4);
		Map body = report("store=DEFAULT&threshold=3&count=1000");
		assertEquals(3L, num(body.get("threshold")));
		assertNotNull(item(body, "hlsat"));
		assertEquals(null, item(body, "hlsabove"));
	}

	@Test
	public void thresholdDefaultsToFive() {
		create("hlsdeffive", 5);
		create("hlsdefsix", 6);
		Map body = report("store=DEFAULT&count=1000");
		assertEquals(5L, num(body.get("threshold")));
		assertNotNull(item(body, "hlsdeffive"));
		assertEquals(null, item(body, "hlsdefsix"));
	}

	@Test
	public void invalidThresholdIsRejected() {
		assertEquals(HttpStatus.BAD_REQUEST, call("store=DEFAULT&threshold=-1", getHeader()).getStatusCode());
		assertEquals(HttpStatus.BAD_REQUEST, call("store=DEFAULT&threshold=abc", getHeader()).getStatusCode());
	}

	@Test
	public void itemsAreOrderedByStockThenSku() {
		create("hlsordb", 1);
		create("hlsorda", 1);
		create("hlsordc", 0);
		List<Map> all = items(report("store=DEFAULT&threshold=1&count=1000"));
		for (int k = 1; k < all.size(); k++) {
			Map a = all.get(k - 1), b = all.get(k);
			long sa = num(a.get("stock")), sb = num(b.get("stock"));
			assertTrue(sa < sb || (sa == sb && String.valueOf(a.get("sku")).compareTo(String.valueOf(b.get("sku"))) <= 0),
					"order at position " + k + ": " + a + " then " + b);
		}
		List<String> ours = all.stream().map(i -> String.valueOf(i.get("sku"))).filter(s -> s.startsWith("hlsord"))
				.collect(Collectors.toList());
		assertEquals(Arrays.asList("hlsordc", "hlsorda", "hlsordb"), ours);
	}

	@Test
	public void pagesAreSlicesOfTheWholeReport() {
		create("hlspagea", 0);
		create("hlspageb", 0);
		create("hlspagec", 0);
		Map whole = report("store=DEFAULT&threshold=0&count=1000");
		List<Map> all = items(whole);
		assertTrue(all.size() >= 3);
		assertEquals((long) all.size(), num(whole.get("totalCount")));
		List<Object> paged = new ArrayList<>();
		for (int page = 0; page * 2 < all.size(); page++) {
			Map body = report("store=DEFAULT&threshold=0&count=2&page=" + page);
			assertEquals((long) all.size(), num(body.get("totalCount")), "totalCount counts every page");
			assertTrue(items(body).size() <= 2);
			items(body).forEach(i -> paged.add(i.get("sku")));
		}
		assertEquals(all.stream().map(i -> i.get("sku")).collect(Collectors.toList()), paged);
	}

	@Test
	public void defaultPageSizeIsTwenty() {
		for (int k = 0; k < 21; k++) {
			create(String.format("hlsdefpage%02d", k), 0);
		}
		Map body = report("store=DEFAULT&threshold=0");
		assertTrue(num(body.get("totalCount")) >= 21);
		assertEquals(20, items(body).size());
	}

	@Test
	public void otherStoresProductsAreNotListed() {
		PersistableAddress address = new PersistableAddress();
		address.setAddress("1 Low Stock Road");
		address.setPostalCode("12345");
		address.setCountry("US");
		address.setCity("FT LD");
		address.setStateProvince("FL");
		PersistableMerchantStore store = new PersistableMerchantStore();
		store.setCode("hlsstore");
		store.setCurrency("CAD");
		store.setDefaultLanguage("en");
		store.setEmail("hls@test.com");
		store.setName("hlsstore");
		store.setPhone("444-555-6666");
		store.setSupportedLanguages(Arrays.asList("en"));
		store.setAddress(address);
		ResponseEntity<Void> s = testRestTemplate.exchange("/api/v1/private/store/", HttpMethod.POST,
				new HttpEntity<>(store, getHeader()), Void.class);
		assertEquals(HttpStatus.OK, s.getStatusCode());
		create("hlsother", 0, "hlsstore");
		create("hlshome", 0);
		Map home = report("store=DEFAULT&threshold=0&count=1000");
		assertNotNull(item(home, "hlshome"));
		assertEquals(null, item(home, "hlsother"), "a product of another store is listed");
		Map other = report("store=hlsstore&threshold=0&count=1000");
		assertNotNull(item(other, "hlsother"));
		assertEquals(null, item(other, "hlshome"));
	}

	@Test
	public void requiresAnAdmin() {
		HttpHeaders anonymous = new HttpHeaders();
		anonymous.setContentType(MediaType.APPLICATION_JSON);
		HttpStatus status = call("store=DEFAULT", anonymous).getStatusCode();
		assertTrue(status == HttpStatus.UNAUTHORIZED || status == HttpStatus.FORBIDDEN, "got " + status);
		assertFalse(status.is2xxSuccessful());
	}
}
