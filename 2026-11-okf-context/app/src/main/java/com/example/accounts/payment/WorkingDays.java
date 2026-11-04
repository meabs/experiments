package com.example.accounts.payment;

import java.time.DayOfWeek;
import java.time.LocalDate;

/** Monday to Friday. */
final class WorkingDays {

    private WorkingDays() {
    }

    static boolean isWorkingDay(LocalDate date) {
        return date.getDayOfWeek() != DayOfWeek.SATURDAY && date.getDayOfWeek() != DayOfWeek.SUNDAY;
    }

    /** The first working day after {@code date}. */
    static LocalDate next(LocalDate date) {
        LocalDate d = date.plusDays(1);
        while (!isWorkingDay(d)) {
            d = d.plusDays(1);
        }
        return d;
    }
}
