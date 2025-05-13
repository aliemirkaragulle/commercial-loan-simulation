import streamlit as st
import pandas as pd
from datetime import datetime
import io
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Get the Absolute Path to the Fonts Directory
fonts_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'fonts'))
font_path = os.path.join(fonts_dir, 'Arial Unicode.ttf')

# Register Arial Unicode Font for Turkish Characters
pdfmetrics.registerFont(TTFont('Arial-Unicode', font_path))

# Page Config
st.set_page_config(
    page_title="Ödeme Planı",
    page_icon="💰",
    layout="wide"
)

# Title
st.title("Ödeme Planı")

# Check If We Have Data In Session State
if 'schedule' in st.session_state:
    # Get The Payment Schedule
    df = pd.DataFrame(st.session_state.schedule)
    
    # Convert payment_date To DateTime
    df['payment_date'] = pd.to_datetime(df['payment_date'])
    
    # Format The Date Column
    df['payment_date'] = df['payment_date'].dt.strftime('%d-%m-%Y')
    
    # Select And Rename Columns For Display
    df = df[['installment_number', 'payment_date', 'remaining_principal', 'installment_amount', 
             'principal_payment', 'interest_payment', 'bsmv', 'commission_payment']]
    
    # Rename Columns For Better Display
    df = df.rename(columns={
        'installment_number': 'Taksit No',
        'payment_date': 'Ödeme Tarihi',
        'principal_payment': 'Anapara Ödemesi',
        'interest_payment': 'Faiz Ödemesi',
        'bsmv': 'BSMV Ödemesi',
        'commission_payment': 'Komisyon Ödemesi',
        'installment_amount': 'Taksit Tutarı',
        'remaining_principal': 'Kalan Anapara'
    })
    
    # Create A Copy Of DataFrame Before Formatting For Totals Calculation
    df_numeric = df.copy()
    
    # Round Numeric Columns To 2 Decimal Places
    numeric_columns = ['Anapara Ödemesi', 'Faiz Ödemesi', 'BSMV Ödemesi', 
                      'Komisyon Ödemesi', 'Taksit Tutarı', 'Kalan Anapara']
    df[numeric_columns] = df[numeric_columns].round(2)
    
    # Calculate Totals Before Adding TL Symbol
    totals = {
        'Taksit No': '',
        'Ödeme Tarihi': '',
        'Kalan Anapara': 'Toplam:',
        'Taksit Tutarı': f"{df_numeric['Taksit Tutarı'].sum():,.2f} TL",
        'Anapara Ödemesi': f"{df_numeric['Anapara Ödemesi'].sum():,.2f} TL",
        'Faiz Ödemesi': f"{df_numeric['Faiz Ödemesi'].sum():,.2f} TL",
        'BSMV Ödemesi': f"{df_numeric['BSMV Ödemesi'].sum():,.2f} TL",
        'Komisyon Ödemesi': f"{df_numeric['Komisyon Ödemesi'].sum():,.2f} TL"
    }
    
    # Add Thousand Separator And TL Symbol To Main DataFrame
    for col in numeric_columns:
        df[col] = df[col].apply(lambda x: f"{x:,.2f} TL")
    
    # Add Totals Row
    df.loc[len(df)] = totals
    
    # Display The DataFrame With Custom Styling
    st.markdown("""
    <style>
        .stDataFrame tr:last-child {font-weight: bold;}
    </style>
    """, unsafe_allow_html=True)
    
    # Calculate Total Height Needed (30 Pixels Per Row Plus Header)
    total_height = (len(df) + 1) * 35
    
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        height=total_height
    )
    
    # Create PDF
    def create_pdf():
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=30
        )
        
        # Convert DataFrame To List For PDF Table
        data = [df.columns.tolist()] + df.values.tolist()
        
        # Create Table
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Arial-Unicode'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, -1), (-1, -1), colors.beige),
            ('FONTNAME', (0, -1), (-1, -1), 'Arial-Unicode'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        # Build PDF
        elements = [table]
        doc.build(elements)
        buffer.seek(0)
        return buffer
    
    # PDF Download Button
    pdf_buffer = create_pdf()
    st.download_button(
        label="Ödeme Planını PDF Olarak İndir",
        data=pdf_buffer,
        file_name="odeme_plani.pdf",
        mime="application/pdf"
    )
else:
    st.warning("Lütfen Ana Sayfadan Kredi Hesaplaması Yapınız.")
