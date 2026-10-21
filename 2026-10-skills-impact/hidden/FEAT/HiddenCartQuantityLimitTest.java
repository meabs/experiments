package com.salesmanager.test.shop.hidden;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.context.SpringBootTest.WebEnvironment;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.test.context.junit.jupiter.SpringExtension;

import com.salesmanager.shop.application.ShopApplication;
import com.salesmanager.shop.model.catalog.product.ReadableProduct;
import com.salesmanager.shop.model.shoppingcart.PersistableShoppingCartItem;
import com.salesmanager.shop.model.shoppingcart.ReadableShoppingCart;
import com.salesmanager.shop.model.shoppingcart.ReadableShoppingCartItem;
import com.salesmanager.test.shop.common.ServicesTestSupport;

@SpringBootTest(classes = ShopApplication.class, webEnvironment = WebEnvironment.RANDOM_PORT)
@ExtendWith(SpringExtension.class)
public class HiddenCartQuantityLimitTest extends ServicesTestSupport {

	private PersistableShoppingCartItem item(String sku, int qty) {
		PersistableShoppingCartItem i = new PersistableShoppingCartItem();
		i.setProduct(sku);
		i.setQuantity(qty);
		return i;
	}

	private ResponseEntity<ReadableShoppingCart> create(String sku, int qty) {
		return testRestTemplate.postForEntity("/api/v1/cart/", new HttpEntity<>(item(sku, qty), getHeader()), ReadableShoppingCart.class);
	}

	private ResponseEntity<String> put(String code, String sku, int qty) {
		return testRestTemplate.exchange("/api/v1/cart/" + code, HttpMethod.PUT, new HttpEntity<>(item(sku, qty), getHeader()), String.class);
	}

	private ResponseEntity<String> multi(String code, PersistableShoppingCartItem... items) {
		return testRestTemplate.exchange("/api/v1/cart/" + code + "/multi", HttpMethod.POST, new HttpEntity<>(items, getHeader()), String.class);
	}

	private int qty(String code, String sku) {
		ReadableShoppingCart cart = testRestTemplate.exchange("/api/v1/cart/" + code, HttpMethod.GET, new HttpEntity<>(getHeader()), ReadableShoppingCart.class).getBody();
		if (cart == null || cart.getProducts() == null) {
			return 0;
		}
		for (ReadableShoppingCartItem i : cart.getProducts()) {
			if (sku.equals(i.getSku())) {
				return i.getQuantity();
			}
		}
		return 0;
	}

	@Test
	public void newCartAcceptsNinetyNineAndRejectsOneHundred() throws Exception {
		ReadableProduct p = sampleProduct("hqlNew");
		ResponseEntity<ReadableShoppingCart> ok = create(p.getSku(), 99);
		assertEquals(HttpStatus.CREATED, ok.getStatusCode());
		assertEquals(99, qty(ok.getBody().getCode(), p.getSku()));
		assertEquals(HttpStatus.BAD_REQUEST, create(p.getSku(), 100).getStatusCode());
	}

	@Test
	public void updateAboveLimitIsRejectedAndCartUnchanged() throws Exception {
		ReadableProduct a = sampleProduct("hqlPutA");
		ReadableProduct b = sampleProduct("hqlPutB");
		String code = create(a.getSku(), 5).getBody().getCode();
		assertEquals(HttpStatus.BAD_REQUEST, put(code, a.getSku(), 100).getStatusCode());
		assertEquals(5, qty(code, a.getSku()));
		assertEquals(HttpStatus.BAD_REQUEST, put(code, b.getSku(), 150).getStatusCode());
		assertEquals(0, qty(code, b.getSku()));
		assertTrue(put(code, a.getSku(), 99).getStatusCode().is2xxSuccessful());
		assertEquals(99, qty(code, a.getSku()));
	}

	@Test
	public void multiWithOneLineAboveLimitChangesNothing() throws Exception {
		ReadableProduct a = sampleProduct("hqlMulA");
		ReadableProduct b = sampleProduct("hqlMulB");
		String code = create(a.getSku(), 5).getBody().getCode();
		assertEquals(HttpStatus.BAD_REQUEST, multi(code, item(a.getSku(), 7), item(b.getSku(), 100)).getStatusCode());
		assertEquals(5, qty(code, a.getSku()));
		assertEquals(0, qty(code, b.getSku()));
	}

	@Test
	public void zeroStillRemovesTheLine() throws Exception {
		ReadableProduct a = sampleProduct("hqlZeroA");
		ReadableProduct b = sampleProduct("hqlZeroB");
		String code = create(a.getSku(), 5).getBody().getCode();
		assertTrue(put(code, b.getSku(), 2).getStatusCode().is2xxSuccessful());
		assertTrue(put(code, a.getSku(), 0).getStatusCode().is2xxSuccessful());
		assertEquals(0, qty(code, a.getSku()));
		assertEquals(2, qty(code, b.getSku()));
	}
}
