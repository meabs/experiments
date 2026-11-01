package com.example.accounts.account;

import java.time.Clock;
import java.time.YearMonth;

/** Which monthly statements a customer can still download. */
public final class StatementPeriods {

    private StatementPeriods() {
    }

    /** Only last month's statement can be downloaded; older ones are requested from the archive. */
    public static boolean isDownloadable(YearMonth period) {
        return isDownloadable(period, Clock.systemUTC());
    }

    static boolean isDownloadable(YearMonth period, Clock clock) {
        return period.equals(YearMonth.now(clock).minusMonths(1));
    }
}
