import numpy as np
import pandas as pd
from decimal import Decimal, getcontext, ROUND_HALF_UP

from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import holidays

from .payment_calendar import PaymentCalendar

getcontext().prec = 15
getcontext().rounding = ROUND_HALF_UP



# Eşit Ana Paralı Kredi
class EqualPrincipalLoan:
    """
    EqualPrincipalLoan calculates the payment schedule for a commercial loan with equal principal repayments,
    structured according to Turkish banking practices.

    Key Features:
    - The loan is repaid in equal principal installments over the term.
    - Interest is calculated using simple interest method:
      * Monthly rate (r_m) is scaled linearly for longer periods (3m, 6m)
      * Uses fixed 30-day periods per Turkish banking convention
    - BSMV (Banking and Insurance Transaction Tax) of 5% is applied to every interest payment.
    - A one-time commission (as a percentage of the principal) is charged at loan initiation, along with its own BSMV.
    
    Calculation Rules:
    - Monthly principal payment (fixed): A = P / n
    - Interest for period k: Iₖ = (P - A·(k - 1)) × r_period
      where r_period = r_m × (period_days/30) for simple interest
      Example: For 3-month payments, rate = monthly_rate × (90/30) = 3 × monthly_rate
    - BSMV: BSMVₖ = Iₖ × 0.05 (5% of each interest payment)
    - Total installment: Installmentₖ = A + Iₖ + BSMVₖ
    - Remaining principal: Rₖ = Rₖ₋₁ - A
    - Commission: principal × commission rate (paid at the start date)
    - Commission BSMV: commission × BSMV rate (also paid at the start date)

    Inputs:
    - principal: Loan amount (Decimal or convertible to Decimal)
    - monthly_interest_rate: Monthly nominal interest rate (e.g., 0.025 for 2.5%)
    - commission: One-time commission rate applied on the principal (e.g., 0.01 for 1%)
    - start_date: Start date of the loan (datetime.date)
    - term: Loan term in months (integer)
    - payment_frequency: One of "1m", "3m", or "6m" (monthly, quarterly, semiannual)
    - bsmv_rate: BSMV tax rate (default 0.05 for 5%)
    - country: Country string to pass to PaymentCalendar (default "Turkey")
    - use_variable_accrual_days: Whether to use actual accrual days for interest calculation (default False)

    Commission:
    - Paid upfront: commission = total_principal × commission_rate
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

    def __init__(self, principal, monthly_interest_rate, commission, start_date, term, 
                 payment_frequency="1m", bsmv_rate=Decimal("0.05"), country="Turkey",
                 use_variable_accrual_days=False):
        self.principal = Decimal(str(principal)) # Miktar
        self.monthly_interest_rate = Decimal(str(monthly_interest_rate)) # Aylık Faiz
        self.commission = Decimal(str(commission)) # Banka Komisyonu
        self.start_date = start_date # Başlangıç Tarihi
        self.term = term # Vade
        self.payment_frequency = payment_frequency # Ödeme Sıklığı
        self.bsmv_rate = bsmv_rate # BSMV Oranı
        self.country = country
        self.use_variable_accrual_days = use_variable_accrual_days # Değişken Faiz Gün Sayısı

        self.payment_calendar = PaymentCalendar(start_date, term, payment_frequency, country)
        self.payment_dates = self.payment_calendar.generate_schedule()
        self.num_payments = len(self.payment_dates)
        
        # Get Both Accrual Day Calculations from PaymentCalendar
        self.actual_accrual_days = self.payment_calendar.get_accrual_days()
        
        # Turkish Banking Convention: Fixed periods (30/90/180 days)
        self.fixed_accrual_days = {}
        if payment_frequency == "1m":
            fixed_days = 30
        elif payment_frequency == "3m":
            fixed_days = 90
        else:  # 6m
            fixed_days = 180
        
        for k in range(1, self.num_payments + 1):
            self.fixed_accrual_days[k] = fixed_days

        # Fixed Principal Payment
        self.fixed_principal = self.principal / Decimal(str(self.num_payments))

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
            # Determine Which Accrual Days to Use Based on User Preference
            if self.use_variable_accrual_days:
                # Use Actual Accrual Days, Normalized to Match the Rate Calculation Basis
                days_ratio = Decimal(str(self.actual_accrual_days[k])) / Decimal("30")
                period_rate = self.monthly_interest_rate * days_ratio
                accrual_days = self.actual_accrual_days[k]
            else:
                # Use Fixed Banking Convention (30/90/180)
                if self.payment_frequency == "1m":
                    period_rate = self.monthly_interest_rate
                elif self.payment_frequency == "3m":
                    period_rate = self.monthly_interest_rate * Decimal("3")
                else:  # 6m
                    period_rate = self.monthly_interest_rate * Decimal("6")
                accrual_days = self.fixed_accrual_days[k]
            
            interest_payment = (remaining_principal * period_rate).quantize(CENTS)  # Simple Interest
            bsmv = (interest_payment * self.bsmv_rate).quantize(CENTS)
            installment = (self.fixed_principal + interest_payment + bsmv).quantize(CENTS)
            payment_date = self.payment_dates[k]

            schedule.append({
                "installment_number": k,
                "payment_date": payment_date,
                "accrual_days": int(accrual_days),
                "principal_payment": self.fixed_principal.quantize(CENTS),
                "interest_payment": interest_payment,
                "commission_payment": Decimal("0.00"),
                "bsmv": bsmv,
                "installment_amount": installment,
                "remaining_principal": (remaining_principal - self.fixed_principal).quantize(CENTS)
            })

            remaining_principal -= self.fixed_principal

        return schedule
    
    def get_totals(self, schedule):
        CENTS = Decimal("0.01")
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
            "total_loan_cost": total_loan_cost.quantize(CENTS),
            "total_interest_paid": total_interest.quantize(CENTS),
            "total_bsmv_paid": total_bsmv.quantize(CENTS),
            "total_installments_paid": total_installments.quantize(CENTS),
            "total_commission_paid": total_commission_payment.quantize(CENTS)
        }
    
    def calculate_average_maturity_and_all_in_rate(self, schedule):
        """
        Calculates the average maturity (Ortalama Vade) in years and the All-In Rate (%).

        Average Maturity (Ortalama Vade):
        - Weighted average number of days over which the principal is repaid.
        - Weights are based on principal paid per installment.
        - Returned as a float in years: total weighted days / 365.

        All-In Rate:
        - Total cost of the loan including interest, BSMV, and commission-related costs.
        - Expressed as an annualized percentage over the average maturity.
        - Formula:
            All-In Rate (%) = [(Total Cost Paid - Principal) / (Average Maturity (years) × Principal)] × 100

        Returns:
            dict:
                {
                    "ortalama_vade_yil": ...,
                    "all_in_rate_percent": ...
                }
        """
        from datetime import timedelta

        CENTS = Decimal("0.01")
        total_weighted_days = Decimal("0.00")
        total_principal_paid = Decimal("0.00")
        total_interest = Decimal("0.00")
        total_bsmv = Decimal("0.00")
        total_commission_payment = Decimal("0.00")

        for row in schedule:
            if row["installment_number"] == 0:
                total_commission_payment += row["installment_amount"]
                continue

            days_from_start = (row["payment_date"] - self.start_date).days
            weighted = row["principal_payment"] * Decimal(str(days_from_start))
            total_weighted_days += weighted
            total_principal_paid += row["principal_payment"]

            total_interest += row["interest_payment"]
            total_bsmv += row["bsmv"]

        ortalama_vade_gun = total_weighted_days / total_principal_paid
        ortalama_vade_yil = (ortalama_vade_gun / Decimal("365")).quantize(CENTS)

        toplam_maliyet = total_interest + total_bsmv + total_commission_payment
        all_in_rate = ((toplam_maliyet / (ortalama_vade_yil * self.principal)) * Decimal("100")).quantize(CENTS)

        return {
            "ortalama_vade_yil": ortalama_vade_yil,
            "all_in_rate_percent": all_in_rate
        }
    
    def to_dataframe(self):
        """
        Returns the full amortization schedule as a pandas DataFrame.
        Useful for analysis, reporting, or exporting to Excel.
        """
        schedule = self.calculate_schedule()
        return pd.DataFrame(schedule)
