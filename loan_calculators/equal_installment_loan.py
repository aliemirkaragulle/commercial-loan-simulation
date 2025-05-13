import numpy as np
import pandas as pd
from decimal import Decimal, getcontext, ROUND_HALF_UP

from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import holidays

from .payment_calendar import PaymentCalendar

getcontext().prec = 15
getcontext().rounding = ROUND_HALF_UP



# Eşit Taksitli Kredi
class EqualInstallmentLoan:
    """
    EqualInstallmentLoan calculates the payment schedule for a commercial loan with fixed total installment amounts
    ("Eşit Taksitli Kredi") under Turkish banking rules.

    Features:
    - Fixed total installment amount over the loan term.
    - Interest is calculated using simple interest method:
      * Monthly rate (r_m) is scaled linearly for longer periods (3m, 6m)
      * Uses fixed periods (30/90/180 days) per Turkish banking convention
    - Each installment splits into decreasing interest and increasing principal.
    - BSMV (5%) applies to all interest payments and to the upfront commission.
    - One-time commission is paid at the loan's start date.

    Formulas:
    - Period rate based on frequency (simple interest):
        r_period = r_m × (period_days / 30)  # period_days is 30/90/180
        Example: For 3-month payments, rate = monthly_rate × (90/30) = 3 × monthly_rate
    - Period rate with BSMV:
        r_period_prime = r_period + (r_period × bsmv_rate)
    - Installment amount (fixed): 
        T = P · [r_period_prime (1 + r_period_prime)^n] / [(1 + r_period_prime)^n - 1]
    - For each installment:
        interest_k = remaining_principal × r_period
        bsmv_k = interest_k × bsmv_rate
        principal_k = T - interest_k - bsmv_k

    Commission:
    - Paid upfront: commission = P × commission_rate
    - BSMV on commission = commission × bsmv_rate

    Outputs:
    - A list of dicts with:
        - installment_number
        - payment_date
        - accrual_days
        - principal_payment
        - interest_payment
        - bsmv
        - installment_amount
        - remaining_principal
    """

    def __init__(self, principal, monthly_interest_rate, commission, start_date, term, payment_frequency, bsmv_rate=Decimal("0.05"), country="Turkey"):
        self.principal = Decimal(str(principal)) # Miktar
        self.monthly_interest_rate = Decimal(str(monthly_interest_rate)) # Aylık Faiz
        self.commission = Decimal(str(commission)) # Banka Komisyonu
        self.start_date = start_date # Başlangıç Tarihi
        self.term = term # Vade
        self.payment_frequency = payment_frequency # Ödeme Sıklığı
        self.bsmv_rate = bsmv_rate # BSMV Oranı
        self.country = country

        self.payment_calendar = PaymentCalendar(start_date, term, payment_frequency, country)
        self.payment_dates = self.payment_calendar.generate_schedule()
        self.num_payments = len(self.payment_dates)
        
        # Use PaymentCalendar's pre-calculated fixed accrual days
        self.fixed_accrual_days = self.payment_calendar.turkish_banking_accrual_days

        # Fixed Installment T Using Period Rate with BSMV
        r_m = self.monthly_interest_rate
        # Use payment_calendar's frequency_to_days to Get the Period Multiplier
        days_in_period = Decimal(str(self.payment_calendar._frequency_to_days()))
        period_multiplier = days_in_period / Decimal("30")
        period_rate = r_m * period_multiplier
            
        period_rate_prime = period_rate + (period_rate * self.bsmv_rate)
        n = Decimal(str(self.num_payments))
        one_plus_r_pow_n = (Decimal("1.0") + period_rate_prime) ** n
        self.fixed_installment = self.principal * period_rate_prime * one_plus_r_pow_n / (one_plus_r_pow_n - Decimal("1.0"))

    def calculate_schedule(self):
        CENTS = Decimal("0.01")
        schedule = []
        remaining_principal = self.principal

        # Commission Payment at Start
        if self.commission > 0:
            commission_amount = (self.principal * self.commission).quantize(CENTS)
            commission_bsmv = (commission_amount * self.bsmv_rate).quantize(CENTS)
            schedule.append({
                "installment_number": 0,
                "payment_date": self.start_date,
                "accrual_days": 0,
                "principal_payment": Decimal("0.00"),
                "interest_payment": Decimal("0.00"),
                "commission_payment": commission_amount,
                "bsmv": commission_bsmv,
                "installment_amount": (commission_amount + commission_bsmv).quantize(CENTS),
                "remaining_principal": remaining_principal.quantize(CENTS)
            })

        # Regular Installments
        for k in range(1, self.num_payments + 1):
            # Use Fixed Banking Periods per Turkish Banking Convention (30/90/180 Days)
            if self.payment_frequency == "1m":
                period_rate = self.monthly_interest_rate
            elif self.payment_frequency == "3m":
                period_rate = self.monthly_interest_rate * Decimal("3")
            else:  # 6m
                period_rate = self.monthly_interest_rate * Decimal("6")
            interest_payment = (remaining_principal * period_rate).quantize(CENTS)  # Calculate Interest Using Period Rate
            bsmv = (interest_payment * self.bsmv_rate).quantize(CENTS)
            principal_payment = (self.fixed_installment - interest_payment - bsmv).quantize(CENTS)
            installment = (principal_payment + interest_payment + bsmv).quantize(CENTS)
            payment_date = self.payment_dates[k]

            schedule.append({
                "installment_number": k,
                "payment_date": payment_date,
                "accrual_days": int(self.fixed_accrual_days[k]),
                "principal_payment": principal_payment,
                "interest_payment": interest_payment,
                "commission_payment": Decimal("0.00"),
                "bsmv": bsmv,
                "installment_amount": installment,
                "remaining_principal": (remaining_principal - principal_payment).quantize(CENTS)
            })

            remaining_principal -= principal_payment

        return schedule

    def get_totals(self, schedule):
        total_commission_payment = Decimal("0.00")
        total_bsmv = Decimal("0.00")
        total_installments = Decimal("0.00")
        total_interest = Decimal("0.00")

        for row in schedule:
            total_bsmv += row["bsmv"]
            if row["installment_number"] == 0:
                total_commission_payment += row["installment_amount"]
            else:
                total_interest += row["interest_payment"]
                total_installments += row["installment_amount"]

        total_loan_cost = total_installments + total_commission_payment

        return {
            "total_loan_cost": total_loan_cost.quantize(Decimal("0.01")),
            "total_interest_paid": total_interest.quantize(Decimal("0.01")),
            "total_bsmv_paid": total_bsmv.quantize(Decimal("0.01")),
            "total_installments_paid": total_installments.quantize(Decimal("0.01")),
            "total_commission_paid": total_commission_payment.quantize(Decimal("0.01"))
        }

    def calculate_average_maturity_and_all_in_rate(self, schedule):

        total_weighted_days = Decimal("0.00")
        total_principal_paid = Decimal("0.00")
        start_date = self.start_date

        total_interest = Decimal("0.00")
        total_bsmv = Decimal("0.00")
        total_commission_payment = Decimal("0.00")

        for row in schedule:
            if row["installment_number"] == 0:
                total_commission_payment += row["installment_amount"]
                total_bsmv += row["bsmv"]
            else:
                days_from_start = Decimal((row["payment_date"] - start_date).days)
                weighted = days_from_start * row["principal_payment"]
                total_weighted_days += weighted
                total_principal_paid += row["principal_payment"]

                total_interest += row["interest_payment"]
                total_bsmv += row["bsmv"]

        ortalama_vade_gun = total_weighted_days / total_principal_paid
        ortalama_vade_yil = ortalama_vade_gun / Decimal("365")

        toplam_maliyet = total_interest + total_bsmv + total_commission_payment
        all_in_rate = (toplam_maliyet / (ortalama_vade_yil * self.principal)) * Decimal("100")

        return {
            "ortalama_vade_yil": ortalama_vade_yil.quantize(Decimal("0.01")),
            "all_in_rate_percent": all_in_rate.quantize(Decimal("0.01"))
        }

    def _frequency_to_days(self):
        """Returns the fixed number of days for interest calculation per Turkish banking convention"""
        if self.payment_frequency == "1m":
            return Decimal("30")
        elif self.payment_frequency == "3m":
            return Decimal("90")
        elif self.payment_frequency == "6m":
            return Decimal("180")
        else:
            raise ValueError("Unsupported Payment Frequency: Must be '1m', '3m', or '6m'")

    def to_dataframe(self):
        """
        Returns the full amortization schedule as a pandas DataFrame.
        Useful for analysis, reporting, or exporting to Excel.
        """
        schedule = self.calculate_schedule()
        return pd.DataFrame(schedule)