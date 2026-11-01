package com.example.accounts.account;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.time.YearMonth;

import org.junit.jupiter.api.Test;

class StatementPeriodsTest {

    @Test
    void lastMonthsStatementIsDownloadable() {
        assertTrue(StatementPeriods.isDownloadable(YearMonth.of(2026, 9)));
    }

    @Test
    void olderStatementsComeFromTheArchive() {
        assertFalse(StatementPeriods.isDownloadable(YearMonth.of(2026, 7)));
    }
}
