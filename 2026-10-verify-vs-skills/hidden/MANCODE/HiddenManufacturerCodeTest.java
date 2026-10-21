package com.salesmanager.test.shop.hidden;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.List;
import java.util.Map;

import org.junit.jupiter.api.Test;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import com.salesmanager.shop.model.catalog.manufacturer.PersistableManufacturer;
import com.salesmanager.test.shop.common.ServicesTestSupport;

/** Hidden acceptance test for task MANCODE: manufacturer code format (400) and uniqueness (409) on create and update. */
public class HiddenManufacturerCodeTest extends ServicesTestSupport {

	@SuppressWarnings("rawtypes")
	private ResponseEntity<Map> create(String code) {
		return testRestTemplate.exchange("/api/v1/private/manufacturer", HttpMethod.POST, new HttpEntity<>(manufacturer(code), getHeader()), Map.class);
	}

	private HttpStatus update(Object id, String code) {
		PersistableManufacturer m = manufacturer(code);
		return testRestTemplate.exchange("/api/v1/private/manufacturer/" + id, HttpMethod.PUT, new HttpEntity<>(m, getHeader()), String.class)
				.getStatusCode();
	}

	@SuppressWarnings({ "rawtypes", "unchecked" })
	private boolean listed(String code) {
		ResponseEntity<Map> r = testRestTemplate.exchange("/api/v1/manufacturers?count=500", HttpMethod.GET, new HttpEntity<>(getHeader()), Map.class);
		return ((List<Map>) r.getBody().get("manufacturers")).stream().anyMatch(m -> code.equals(m.get("code")));
	}

	@Test
	public void validCodesAreAccepted() {
		for (String c : new String[] { "hm", "hmc_valid-1", "HMC-Brand_2" }) {
			assertTrue(create(c).getStatusCode().is2xxSuccessful(), c);
			assertTrue(listed(c), c + " must be stored");
		}
	}

	@Test
	public void badCodesAreRejectedAndNotStored() {
		for (String c : new String[] { "hmc bad", "hmc!", "h", "hmcxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" }) {
			assertEquals(HttpStatus.BAD_REQUEST, create(c).getStatusCode(), "code [" + c + "]");
			assertFalse(listed(c), c + " must not be stored");
		}
	}

	@Test
	public void duplicateCodeIsAConflict() {
		assertTrue(create("hmcdup").getStatusCode().is2xxSuccessful());
		assertEquals(HttpStatus.CONFLICT, create("hmcdup").getStatusCode());
	}

	@Test
	public void updateRulesMatchCreateRules() {
		Object a = create("hmcupda").getBody().get("id");
		create("hmcupdb");
		assertEquals(HttpStatus.BAD_REQUEST, update(a, "hmc upd!"));
		assertEquals(HttpStatus.CONFLICT, update(a, "hmcupdb"));
		assertTrue(listed("hmcupda"), "a rejected update must leave the code unchanged");
		assertTrue(update(a, "hmcupda").is2xxSuccessful(), "keeping its own code is fine");
		assertTrue(update(a, "hmcupdc").is2xxSuccessful(), "changing to a free valid code is fine");
		assertTrue(listed("hmcupdc"));
	}
}
