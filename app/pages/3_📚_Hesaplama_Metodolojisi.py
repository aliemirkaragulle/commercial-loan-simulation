import streamlit as st

# Page Config
st.set_page_config(
    page_title="Hesaplama Metodolojisi",
    page_icon="📚",
    layout="wide"
)

# Title
st.title("Hesaplama Metodolojisi")

# 1. Ödeme Tarihi Hesaplanması
st.header("1. Ödeme Tarihi Hesaplanması")
st.markdown("""
Ticari kredilerde ödeme tarihi hesaplaması aşağıdaki prensiplere göre yapılır:

* Her ay aynı günde ödeme yapılır (örn: her ayın 15'i).
* Tahakkuk süresi her zaman 30 gün olarak alınır.
* Eğer ödeme günü hafta sonu veya resmi tatile denk gelirse, ödeme bir sonraki iş gününe kayar.
* Önemli: Tahakkuk tarihi değişmez, sadece ödeme tarihi kayar.
* Örnek: 15 Ocak'ta başlayan bir kredinin ödemeleri her ayın 15'inde olur.
""")

# 2. Eşit Ana Paralı Kredi
st.header("2. Eşit Ana Paralı Kredi")
st.markdown("""
Eşit ana paralı kredide basit faiz yöntemi kullanılır:

1. **Basit Faiz Oranı Hesaplaması**:
   * Dönemsel faiz oranı şu şekilde hesaplanır:
   * $r_{dönem} = r_{aylık} \\times \\frac{dönem\\_gün}{30}$
   * Örnek: 90 günlük dönem için $r_{dönem} = r_{aylık} \\times \\frac{90}{30} = 3r_{aylık}$

2. **Ana Formüller**:
   * Anapara Ödemesi: $AP = \\frac{Kredi\\_Tutarı}{Vade}$
   * Faiz: $F_n = Kalan\\_Anapara_n \\times r_{dönem}$
   * BSMV: $BSMV = F_n \\times 0.05$
   * Taksit: $T_n = AP + F_n + BSMV$
   * Kalan Anapara: $Kalan\\_Anapara_{n+1} = Kalan\\_Anapara_n - AP$
""")

# 3. Eşit Taksitli Kredi
st.header("3. Eşit Taksitli Kredi")
st.markdown("""
Eşit taksitli kredide de basit faiz yöntemi kullanılır, ancak BSMV faiz oranına dahil edilir:

1. **Basit Faiz ve BSMV Dahil Oran Hesaplaması**:
   * Önce dönemsel faiz hesaplanır: $r_{dönem} = r_{aylık} \\times \\frac{dönem\\_gün}{30}$
   * BSMV dahil oran: $r_{prime} = r_{dönem} + (r_{dönem} \\times bsmv\\_oran)$
   * Örnek: $r_{prime} = r_{dönem} + (r_{dönem} \\times 0.05)$

2. **Ana Formüller**:
   * Taksit (PMT): $PMT = PV \\times \\frac{r_{prime}(1+r_{prime})^n}{(1+r_{prime})^n-1}$
   * Faiz: $F_n = Kalan\\_Anapara_n \\times r_{dönem}$
   * BSMV: $BSMV = F_n \\times 0.05$
   * Anapara: $AP_n = PMT - F_n - BSMV$
   * Kalan Anapara: $Kalan\\_Anapara_{n+1} = Kalan\\_Anapara_n - AP_n$

Burada:
* PV: Kredi tutarı
* n: Toplam dönem sayısı
* $r_{prime}$: BSMV dahil dönemsel faiz oranı
""")

# Add CSS for better LaTeX rendering
st.markdown("""
<style>
.katex { font-size: 1.1em; }
</style>
""", unsafe_allow_html=True)
