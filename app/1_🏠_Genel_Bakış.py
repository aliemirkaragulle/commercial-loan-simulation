import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import io
from datetime import date
from decimal import Decimal

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loan_calculators import EqualPrincipalLoan, EqualInstallmentLoan

# Page Config
st.set_page_config(
    page_title="Genel Bakış",
    page_icon="🏠",
    layout="wide"
)

# Title
st.title("Ticari Kredi Ödeme Planı")

# User Inputs
st.subheader("Kullanıcı Girdileri")

with st.form("loan_form"):
    col1, col2 = st.columns(2)

    with col1:
        principal = st.number_input(
            "Kredi Tutarı",
            min_value=0.0,
            value=100000.0,
            step=1000.0,
            help="TL Cinsinden Kredi Tutarı"
        )
        
        monthly_interest_rate = st.number_input(
            "Aylık Faiz Oranı (%)",
            min_value=0.0,
            value=2.5,
            step=0.1,
            help="Aylık Nominal Faiz Oranı"
        ) / 100
        
        commission = st.number_input(
            "Komisyon Oranı (%)",
            min_value=0.0,
            value=1.0,
            step=0.1,
            help="Kredi Tutarı Üzerinden Alınan Komisyon Oranı"
        ) / 100

    with col2:
        start_date = st.date_input(
            "Kredi Başlangıç Tarihi",
            value=date.today(),
            help="Kredi Kullanım Tarihi"
        )
        
        term = st.number_input(
            "Vade (Ay)",
            min_value=0,
            value=12,
            step=1,
            help="Kredi Vadesi (Ay Cinsinden)"
        )
        
        payment_frequency = st.selectbox(
            "Ödeme Sıklığı",
            options=["1m", "3m", "6m"],
            format_func=lambda x: {
                "1m": "Aylık",
                "3m": "3 Aylık",
                "6m": "6 Aylık"
            }[x],
            help="Taksit Ödeme Sıklığı"
        )

    loan_type = st.selectbox(
        "Kredi Türü",
        options=["Eşit Ana Paralı Kredi", "Eşit Taksitli Kredi"],
        help="Kredi Geri Ödeme Tipi"
    )
    
    # Only Show Accrual Day Option If Equal Principal Loan Is Selected
    use_variable_accrual_days = False
    if loan_type == "Eşit Ana Paralı Kredi":
        accrual_day_type = st.selectbox(
            "Dönemsel Faiz Gün Sayısı",
            options=["Sabit", "Değişken"],
            help="Sabit: 30/90/180 Gün, Değişken: Gerçek Gün Sayısı"
        )
        use_variable_accrual_days = (accrual_day_type == "Değişken")

    submitted = st.form_submit_button("Hesapla")

if submitted:
    # Initialize Loan and Calculate Schedule
    if loan_type == "Eşit Ana Paralı Kredi":
        loan = EqualPrincipalLoan(
            principal=principal,
            monthly_interest_rate=monthly_interest_rate,
            commission=commission,
            start_date=start_date,
            term=term,
            payment_frequency=payment_frequency,
            use_variable_accrual_days=use_variable_accrual_days
        )
    else:
        loan = EqualInstallmentLoan(
            principal=principal,
            monthly_interest_rate=monthly_interest_rate,
            commission=commission,
            start_date=start_date,
            term=term,
            payment_frequency=payment_frequency
        )

    schedule = loan.calculate_schedule()
    maturity_stats = loan.calculate_average_maturity_and_all_in_rate(schedule)
    totals = loan.get_totals(schedule)
    
    # Store in Session State
    st.session_state.loan = loan
    st.session_state.schedule = schedule
    st.session_state.maturity_stats = maturity_stats
    st.session_state.totals = totals

# Use Session State Data If Available
if 'loan' in st.session_state:

    # Create Plotly Chart
    fig = go.Figure()

    # Get Payment Dates and Amounts
    df = pd.DataFrame(st.session_state.schedule)

    # Add Traces For Each Component
    fig.add_trace(go.Bar(
        name='Anapara',
        x=df['payment_date'],
        y=df['principal_payment'],
        marker_color='#2E86C1'
    ))

    fig.add_trace(go.Bar(
        name='Faiz',
        x=df['payment_date'],
        y=df['interest_payment'],
        marker_color='#E74C3C'
    ))

    fig.add_trace(go.Bar(
        name='BSMV',
        x=df['payment_date'],
        y=df['bsmv'],
        marker_color='#27AE60'
    ))

    # Add Commission If It Exists
    if st.session_state.loan.commission > 0:
        fig.add_trace(go.Bar(
            name='Komisyon',
            x=df['payment_date'],
            y=df['commission_payment'],
            marker_color='#8E44AD'  # Purple for Commission
        ))

    # Add Text Annotations for Total Amounts
    annotations = []
    for idx, row in df.iterrows():
        annotations.append(
            dict(
                x=row['payment_date'],
                y=row['installment_amount'],
                text=f"{row['installment_amount']:,.0f} TL",
                showarrow=False,
                yshift=10,  # Shift Text 10 Pixels Above the Bar
                font=dict(size=10)
            )
        )

    # Update Layout
    fig.update_layout(
        title='Ödeme Planı Grafiği',
        xaxis_title='Taksit Tarihi',
        yaxis_title='Taksit Tutarı (TL)',
        barmode='stack',
        showlegend=True,
        height=600,
        annotations=annotations
    )

    # Display Chart
    st.plotly_chart(fig, use_container_width=True)

    # Display Metrics Using Containers for Consistent Spacing
    metrics_container = st.container()
    
    # Create Three Rows with 4 Columns Each for Consistent Alignment
    row1, row2, row3 = st.columns(4), st.columns(4), st.columns(4)

    # First Row
    with row1[0]:
        st.metric(
            "Toplam Kredi Maliyeti",
            f"{st.session_state.totals['total_loan_cost']:,.2f} TL"
        )
    if loan_type == "Eşit Taksitli Kredi":
        first_installment = next(payment for payment in st.session_state.schedule if payment['installment_number'] == 1)
        with row1[1]:
            st.metric(
                "Taksit Tutarı",
                f"{first_installment['installment_amount']:,.2f} TL"
            )

    # Second Row
    with row2[0]:
        st.metric(
            "Toplam Ana Para",
            f"{principal:,.2f} TL"
        )
    with row2[1]:
        st.metric(
            "Toplam Faiz",
            f"{st.session_state.totals['total_interest_paid']:,.2f} TL"
        )
    with row2[2]:
        st.metric(
            "Toplam BSMV",
            f"{st.session_state.totals['total_bsmv_paid']:,.2f} TL"
        )
    with row2[3]:
        pure_commission = Decimal(str(principal)) * Decimal(str(commission))
        st.metric(
            "Toplam Komisyon",
            f"{pure_commission:,.2f} TL"
        )

    # Third Row
    with row3[0]:
        st.metric(
            "Ortalama Vade (Yıl)",
            f"{st.session_state.maturity_stats['ortalama_vade_yil']:.2f}"
        )
    with row3[1]:
        st.metric(
            "All-In Faiz Oranı (Yıllık %)",
            f"{st.session_state.maturity_stats['all_in_rate_percent']:.2f}"
        )

    # Excel Export
    df_export = pd.DataFrame(st.session_state.schedule)
    df_export['payment_date'] = pd.to_datetime(df_export['payment_date'])

    # Prepare Excel File
    buffer = io.BytesIO()
    df_export.to_excel(buffer, index=False)
    buffer.seek(0)

    # Download Button
    st.download_button(
        label="Ödeme Planı Excel Olarak İndir",
        data=buffer,
        file_name="kredi_taksit_tablosu.xlsx",
        mime="application/vnd.ms-excel"
    )

    # Excel Export - Payment Calendar
    calendar_df = st.session_state.loan.payment_calendar.to_dataframe()
    calendar_df['Payment Date'] = pd.to_datetime(calendar_df['Payment Date'])
    calendar_df['Accrual Start'] = pd.to_datetime(calendar_df['Accrual Start'])
    calendar_df['Accrual End'] = pd.to_datetime(calendar_df['Accrual End'])

    # Prepare Calendar Excel File
    calendar_buffer = io.BytesIO()
    calendar_df.to_excel(calendar_buffer, index=False)
    calendar_buffer.seek(0)

    # Download Button - Payment Calendar
    st.download_button(
        label="Ödeme Günlerini Excel Olarak İndir",
        data=calendar_buffer,
        file_name="odeme_gunleri.xlsx",
        mime="application/vnd.ms-excel",
        key="calendar_download"  # Unique key to avoid conflict with other download button
    )