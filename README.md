# Commercial Loan Calculator

A Turkish commercial loan calculator with support for Equal Principal (Eşit Ana Paralı) and Equal Installment (Eşit Taksitli) loans, built with Streamlit.

## Features

- Equal Principal Loan (Eşit Ana Paralı Kredi) calculations
- Equal Installment Loan (Eşit Taksitli Kredi) calculations
- Turkish banking calendar support
- BSMV tax and commission handling
- Interactive payment schedule visualization
- Excel and PDF export options
- Detailed calculation methodology documentation

## Prerequisites

1. Python 3.8 or higher
2. Arial Unicode font for Turkish character support in PDF exports
   - Font path: `/Library/Fonts/Arial Unicode.ttf`
   - If not installed, please install the font for proper PDF generation with Turkish characters

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/commercial_loan_calculator.git
   cd commercial_loan_calculator
   ```

2. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

1. Make sure your virtual environment is activated

2. Start the Streamlit application:
   ```bash
   streamlit run app/1_🏠_Genel_Bakış.py
   ```

3. The application will open in your default web browser at http://localhost:8501

## Usage

1. **Genel Bakış (Overview)**
   - Select loan type (Equal Principal or Equal Installment)
   - Enter loan amount, interest rate, and term
   - View payment schedule and analytics

2. **Ödeme Planı (Payment Schedule)**
   - View detailed payment schedule
   - Export to Excel or PDF

3. **Hesaplama Metodolojisi (Calculation Methodology)**
   - Learn about the calculation methods
   - View formulas and banking rules

## License

This project is licensed under the MIT License - see the LICENSE file for details.