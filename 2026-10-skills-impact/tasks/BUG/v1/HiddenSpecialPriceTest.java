package com.salesmanager.test.hidden;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.math.BigDecimal;
import java.util.Date;
import java.util.HashSet;
import java.util.Set;

import org.junit.jupiter.api.Test;

import com.salesmanager.core.business.utils.ProductPriceUtils;
import com.salesmanager.core.model.catalog.product.availability.ProductAvailability;
import com.salesmanager.core.model.catalog.product.price.FinalPrice;
import com.salesmanager.core.model.catalog.product.price.ProductPrice;

public class HiddenSpecialPriceTest {

	private static final long DAY = 24L * 60 * 60 * 1000;

	private FinalPrice price(Date start, Date end) throws Exception {
		ProductPrice p = new ProductPrice();
		p.setDefaultPrice(true);
		p.setProductPriceAmount(new BigDecimal("100.00"));
		p.setProductPriceSpecialAmount(new BigDecimal("80.00"));
		p.setProductPriceSpecialStartDate(start);
		p.setProductPriceSpecialEndDate(end);
		Set<ProductPrice> prices = new HashSet<>();
		prices.add(p);
		ProductAvailability a = new ProductAvailability();
		a.setPrices(prices);
		return new ProductPriceUtils().getFinalPrice(a);
	}

	private Date days(int n) {
		return new Date(System.currentTimeMillis() + n * DAY);
	}

	@Test
	public void specialWithStartAndEndAppliesInsideWindow() throws Exception {
		FinalPrice f = price(days(-1), days(1));
		assertTrue(f.isDiscounted());
		assertEquals(0, new BigDecimal("80.00").compareTo(f.getFinalPrice()));
		assertEquals(20, f.getDiscountPercent());
	}

	@Test
	public void specialAfterEndDoesNotApply() throws Exception {
		FinalPrice f = price(days(-7), days(-1));
		assertFalse(f.isDiscounted());
		assertEquals(0, new BigDecimal("100.00").compareTo(f.getFinalPrice()));
	}

	@Test
	public void specialBeforeStartDoesNotApply() throws Exception {
		FinalPrice f = price(days(1), days(7));
		assertFalse(f.isDiscounted());
		assertEquals(0, new BigDecimal("100.00").compareTo(f.getFinalPrice()));
	}

	@Test
	public void specialWithOnlyEndStillApplies() throws Exception {
		FinalPrice f = price(null, days(1));
		assertTrue(f.isDiscounted());
		assertEquals(0, new BigDecimal("80.00").compareTo(f.getFinalPrice()));
	}
}
