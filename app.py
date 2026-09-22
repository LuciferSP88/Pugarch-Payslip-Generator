import io
import os
import sys

# Automatically launch with Streamlit runtime if executed directly via `python app.py`
if __name__ == "__main__":
    try:
        from streamlit.runtime import exists as _streamlit_exists
        if not _streamlit_exists():
            from streamlit.web import cli as stcli
            sys.argv = ["streamlit", "run", os.path.abspath(__file__)]
            sys.exit(stcli.main())
    except ImportError:
        pass

import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PyPDF2 import PdfReader, PdfWriter

# --- Page Configuration & Dark / Neon Purple Theme ---
st.set_page_config(
    page_title="PugArch Payslip Generator",
    page_icon="📄",
    layout="wide"
)

# Custom CSS for Pitch Black & Neon Purple Styling
st.markdown("""
<style>
    /* Global Background */
    .stApp {
        background-color: #0A090D;
        color: #FFFFFF;
    }
    
    /* Card Containers */
    div[data-testid="stVerticalBlock"] > div[style*="background-color"] {
        background-color: #14121E !important;
        border-radius: 10px;
        border: 1px solid #3B1C59;
    }
    
    /* Section Headers & Labels */
    h1, h2, h3, h4 {
        color: #A855F7 !important;
        font-family: 'Helvetica', sans-serif;
    }
    label {
        color: #A78BFA !important;
        font-weight: 500;
    }

    /* Input Boxes */
    input {
        background-color: #1D192B !important;
        color: #FFFFFF !important;
        border: 1px solid #3B1C59 !important;
        border-radius: 6px !important;
    }
    input:focus {
        border-color: #A855F7 !important;
        box-shadow: 0 0 8px #A855F7 !important;
    }

    /* Metric Cards */
    div[data-testid="stMetric"] {
        background-color: #14121E;
        border: 1px solid #3B1C59;
        padding: 12px 18px;
        border-radius: 8px;
    }
    div[data-testid="stMetricLabel"] p {
        color: #A78BFA !important;
        font-size: 0.85rem !important;
    }
    div[data-testid="stMetricValue"] div {
        color: #C084FC !important;
        font-weight: bold;
    }

    /* Primary Buttons & Download Buttons */
    .stDownloadButton button, .stButton button {
        background: linear-gradient(135deg, #7E22CE, #9333EA) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 10px 24px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease-in-out;
        width: 100%;
    }
    .stDownloadButton button:hover, .stButton button:hover {
        background: linear-gradient(135deg, #9333EA, #A855F7) !important;
        box-shadow: 0 0 12px #A855F7 !important;
    }
</style>
""", unsafe_allow_html=True)

EARNINGS_KEYS = [
    "Basic Pay", "HRA", "Conveyance", "Medical Allowance", 
    "KRA", "DA", "Incentives"
]
DEDUCTIONS_KEYS = ["PF", "PT"]

def create_overlay(data):
    """Creates a transparent PDF overlay using calibrated coordinates."""
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=letter)

    # 1. Header Details (10pt)
    c.setFont("Helvetica", 10)
    c.drawString(180, 686, f"{data['details']['pay_period']}")
    c.drawString(180, 664, f"{data['details']['emp_name']}")
    c.drawString(180, 642, f"{data['details']['account_number']}")
    
    c.drawString(420, 686, f"{data['details']['emp_id']}")
    c.drawString(420, 664, f"{data['details']['position']}")
    c.drawString(420, 642, f"{data['details']['ifsc_code']}")

    # 2. Earnings Table (11pt)
    c.setFont("Helvetica", 11)
    y_earnings = 543.0
    row_pitch_earnings = 26.85

    for category in EARNINGS_KEYS:
        amount = data["earnings"].get(category, 0.0)
        c.drawCentredString(430, round(y_earnings), f"{amount:.2f}")
        y_earnings -= row_pitch_earnings
            
    c.drawCentredString(430, 350, f"{data['earnings']['Total']:.2f}")

    # 3. Deductions Table (11pt)
    c.setFont("Helvetica", 11)
    y_deductions = 255
    row_pitch_deductions = 24

    for category in DEDUCTIONS_KEYS:
        amount = data["deductions"].get(category, 0.0)
        c.drawCentredString(430, y_deductions, f"{amount:.2f}")
        y_deductions -= row_pitch_deductions
            
    c.drawCentredString(430, 207, f"{data['deductions']['Total']:.2f}")

    # 4. Net Salary (12pt Bold)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(185, 162, f"{data['net_salary']:.2f}")

    c.save()
    packet.seek(0)
    return packet

def generate_payslip_bytes(template_bytes, data):
    """Merges overlay with template PDF and returns result as bytes."""
    template_reader = PdfReader(io.BytesIO(template_bytes))
    template_page = template_reader.pages[0]

    overlay_pdf = create_overlay(data)
    overlay_reader = PdfReader(overlay_pdf)
    overlay_page = overlay_reader.pages[0]

    template_page.merge_page(overlay_page)

    writer = PdfWriter()
    writer.add_page(template_page)
    
    output_stream = io.BytesIO()
    writer.write(output_stream)
    return output_stream.getvalue()

# --- Main App Layout ---
st.title("PAYSLIP GENERATOR")
st.caption("Automated payroll generation matching the PugArch PDF layout")

# 1. Base Template Management
default_template = "Pugarch Payslip.pdf"
uploaded_template = st.sidebar.file_uploader("Upload Base PDF (Optional)", type=["pdf"])

template_bytes = None
if uploaded_template:
    template_bytes = uploaded_template.read()
elif os.path.exists(default_template):
    with open(default_template, "rb") as f:
        template_bytes = f.read()
else:
    st.sidebar.warning("Please upload 'Pugarch Payslip.pdf' to generate slips.")

# 2. Employee Details
st.subheader("1. Employee & Payroll Information")
col1, col2 = st.columns(2)
with col1:
    pay_period = st.text_input("Pay Period", value="August 2026")
    emp_name = st.text_input("Employee Name", value="XYZ")
    account_number = st.text_input("Account Number", value="1234567890")

with col2:
    emp_id = st.text_input("Employee ID", value="ABC0000")
    position = st.text_input("Position", value="Junior Developer")
    ifsc_code = st.text_input("IFSC Code", value="SGVCHJ8678")

# 3. Figures (Earnings & Deductions)
st.subheader("2. Salary Figures (₹)")
earn_col, ded_col = st.columns(2)

earnings = {}
with earn_col:
    st.markdown("### Earnings")
    for category in EARNINGS_KEYS:
        val = st.number_input(f"{category}", min_value=0.0, step=500.0, format="%.2f", key=f"earn_{category}")
        earnings[category] = val
earnings["Total"] = sum(earnings.values())

deductions = {}
with ded_col:
    st.markdown("### Deductions")
    for category in DEDUCTIONS_KEYS:
        val = st.number_input(f"{category}", min_value=0.0, step=100.0, format="%.2f", key=f"ded_{category}")
        deductions[category] = val
deductions["Total"] = sum(deductions.values())

net_salary = earnings["Total"] - deductions["Total"]

# 4. Live Summary Bar
st.write("---")
m1, m2, m3 = st.columns(3)
m1.metric("TOTAL EARNINGS", f"₹ {earnings['Total']:,.2f}")
m2.metric("TOTAL DEDUCTIONS", f"₹ {deductions['Total']:,.2f}")
m3.metric("NET PAY", f"₹ {net_salary:,.2f}")

# 5. Output / Download Action
st.write("---")
if template_bytes:
    payload = {
        "details": {
            "pay_period": pay_period,
            "emp_name": emp_name,
            "account_number": account_number,
            "emp_id": emp_id,
            "position": position,
            "ifsc_code": ifsc_code,
        },
        "earnings": earnings,
        "deductions": deductions,
        "net_salary": net_salary
    }
    
    clean_name = emp_name.strip().replace(" ", "_") or "Employee"
    clean_period = pay_period.strip().replace(" ", "_") or "Period"
    output_filename = f"Payslip_{clean_name}_{clean_period}.pdf"

    pdf_output = generate_payslip_bytes(template_bytes, payload)

    st.download_button(
        label=f"⬇️ GENERATE & DOWNLOAD {output_filename}",
        data=pdf_output,
        file_name=output_filename,
        mime="application/pdf"
    )
else:
    st.error("Cannot generate payslip without a base template. Please upload your template PDF in the sidebar.")