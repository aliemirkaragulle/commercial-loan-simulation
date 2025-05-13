import numpy as np
import pandas as pd
from decimal import Decimal, getcontext, ROUND_HALF_UP

from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import holidays

getcontext().prec = 15
getcontext().rounding = ROUND_HALF_UP



class PaymentCalendar:
    """
    PaymentCalendar generates a schedule of loan installment payment dates based on Turkish banking rules.

    Updated Rules Implemented:
    - Interest starts accruing on the loan's start date.
    - Each installment is scheduled for the same calendar day each month (e.g., always 2nd).
    - If the target calendar day falls on a weekend or Turkish national holiday,
      the payment date is deferred to the next valid business day — but only for that month.
    - Payment dates are calculated based on nominal date continuity (not adjusted dates).
    - Accrual days represent the number of days on which interest is accrued for each period (excluding payment day).
    - Accrual date ranges include a list of all actual days on which interest is accrued (excluding the payment date).

    Returns:
    - A dictionary of installment numbers mapped to valid payment dates.
    - A dictionary of installment numbers mapped to corresponding actual accrual day counts.
    - A dictionary of installment numbers mapped to a list of accrual dates (excluding payment date).
    - A dictionary of installment numbers mapped to Turkish banking fixed accrual days (30 days per month).
    """

    def __init__(self, start_date, term_in_months, payment_frequency="1m", country="Turkey"):
        self.start_date = start_date
        self.term_in_months = term_in_months
        self.payment_frequency = payment_frequency
        self.country = country
        self.holiday_calendar = holidays.Turkey() if country == "Turkey" else holidays.CountryHoliday(country)
        
        self.payment_dates = {}
        self.accrual_days = {}
        self.accrual_date_ranges = {}
        self.turkish_banking_accrual_days = {}

    def generate_schedule(self):
        if self.payment_frequency == "1m":
            delta = relativedelta(months=1)
        elif self.payment_frequency == "3m":
            delta = relativedelta(months=3)
        elif self.payment_frequency == "6m":
            delta = relativedelta(months=6)
        else:
            raise ValueError("Unsupported Payment Frequency: Must be '1m', '3m', or '6m'")

        current_payment_day = self.start_date.day
        nominal_base_date = self.start_date

        for i in range(1, self.term_in_months * 30 // self._frequency_to_days() + 1):
            scheduled_date = nominal_base_date + delta
            try:
                scheduled_date = scheduled_date.replace(day=current_payment_day)
            except ValueError:
                # Handle Months That Don't Have The Same Day (e.g. 31st)
                scheduled_date = scheduled_date + relativedelta(day=31)

            # Adjust Only For That Month (Not Future Offsets)
            while scheduled_date.weekday() >= 5 or scheduled_date in self.holiday_calendar:
                scheduled_date += timedelta(days=1)

            accrual_start = self.payment_dates[i - 1] if i > 1 else self.start_date
            self.payment_dates[i] = scheduled_date
            self.accrual_days[i] = (scheduled_date - accrual_start).days

            self.accrual_date_ranges[i] = [
                accrual_start + timedelta(days=d)
                for d in range(self.accrual_days[i])
            ]

            # Set Fixed Turkish Banking Accrual Days
            self.turkish_banking_accrual_days[i] = self._frequency_to_days()

            nominal_base_date += delta

        return self.payment_dates

    def get_accrual_days(self):
        if not self.accrual_days:
            self.generate_schedule()
        return self.accrual_days

    def get_total_accrual_days(self):
        if not self.accrual_days:
            self.generate_schedule()
        return sum(self.accrual_days.values())

    def get_accrual_date_ranges(self):
        if not self.accrual_date_ranges:
            self.generate_schedule()
        return self.accrual_date_ranges

    def _frequency_to_days(self):
        if self.payment_frequency == "1m":
            return 30
        elif self.payment_frequency == "3m":
            return 90
        elif self.payment_frequency == "6m":
            return 180
        else:
            raise ValueError("Unsupported Payment Frequency: Must be '1m', '3m', or '6m'")

    def to_dataframe(self):
        self.generate_schedule()

        data = []
        for k in sorted(self.payment_dates):
            date_range = self.accrual_date_ranges[k]
            data.append({
                "Installment": k,
                "Payment Date": self.payment_dates[k],
                "Turkish Banking Accrual Days": self.turkish_banking_accrual_days[k],
                "Accrual Days": self.accrual_days[k],
                "Accrual Start": date_range[0],
                "Accrual End": date_range[-1]
            })

        return pd.DataFrame(data)