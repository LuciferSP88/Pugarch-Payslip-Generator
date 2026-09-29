import io
import os
import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PyPDF2 import PdfReader, PdfWriter

# --- Page Configuration & Styling ---
st.set_page_config(
    page_title="PugArch Payslip Generator",
    page_icon="📄",
    layout="wide"
)

st.markdown("""
<style>
    /* Global Background */
    .stApp {
        background-color: #0A090D;
        color: #FFFFFF;
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

    /* Input Fields */
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

    /* Download & Action Buttons */
    .stDownloadButton button, .stButton button {
        background: linear-gradient(135deg, #7E22CE, #9333EA) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 12px 24px !important;
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

# Field lists matching Pugarch Payslip_1.pdf
EARNINGS_KEYS = [
    "Basic Pay", "HRA", "Conveyance", "Medical Allowance", 
    "DA", "Incentives"
]
DEDUCTIONS_KEYS = ["PT", "Leave Without Pay"]


def create_overlay(data):
    """Draws values onto a transparent PDF overlay using calibrated coordinates."""
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=letter)

    # 1. Header Details (10pt Helvetica)
    c.setFont("Helvetica", 10)
    c.drawString(180, 686, f"{data['details']['pay_period']}")
    c.drawString(180, 664, f"{data['details']['emp_name']}")
    c.drawString(180, 642, f"{data['details']['account_number']}")
    c.drawString(180, 620, f"{data['details']['days_worked']}")
    
    c.drawString(420, 686, f"{data['details']['emp_id']}")
    c.drawString(420, 664, f"{data['details']['position']}")
    c.drawString(420, 642, f"{data['details']['ifsc_code']}")
    c.drawString(420, 620, f"{data['details']['days_on_leave']}")

    # Shared horizontal center for the Amount column
    X_AMOUNT = 412

    # 2. Earnings Table (13pt Helvetica)
    c.setFont("Helvetica", 13)
    y_earnings = 513.5
    row_pitch_earnings = 26.85

    for category in EARNINGS_KEYS:
        amount = data["earnings"].get(category, 0.0)
        c.drawCentredString(X_AMOUNT, round(y_earnings), f"{amount:.2f}")
        y_earnings -= row_pitch_earnings
            
    c.drawCentredString(X_AMOUNT, 352, f"{data['earnings']['Total']:.2f}")

    # 3. Deductions Table (13pt Helvetica)
    c.setFont("Helvetica", 13)
    y_deductions = 251.0
    row_pitch_deductions = 26.85

    for category in DEDUCTIONS_KEYS:
        amount = data["deductions"].get(category, 0.0)
        c.drawCentredString(X_AMOUNT, round(y_deductions), f"{amount:.2f}")
        y_deductions -= row_pitch_deductions
            
    c.drawCentredString(X_AMOUNT, 195.0, f"{data['deductions']['Total']:.2f}")

    # 4. Net Salary (14pt Bold)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(185, 162, f"{data['net_salary']:.2f}")

    c.save()
    packet.seek(0)
    return packet


def generate_payslip_bytes(template_bytes, data):
    """Merges the overlay with the base PDF template."""
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


# --- Main Application Layout ---
st.title("PAYSLIP GENERATOR")
st.caption("PugArch automated payroll processing engine")

# Template Resolver
default_template = "Pugarch Payslip_1.pdf"
uploaded_template = st.sidebar.file_uploader("Upload Base PDF (Optional)", type=["pdf"])

template_bytes = None
if uploaded_template:
    template_bytes = uploaded_template.read()
elif os.path.exists(default_template):
    with open(default_template, "rb") as f:
        template_bytes = f.read()
else:
    st.sidebar.warning(f"Template '{default_template}' not found in root. Please upload it.")

# 1. Header Information
st.subheader("1. Employee & Attendance Details")
col1, col2 = st.columns(2)
with col1:
    pay_period = st.text_input("Pay Period", value="August 2026")
    emp_name = st.text_input("Employee Name", value="XYZ")
    account_number = st.text_input("Account Number", value="1234567890")
    days_worked = st.text_input("Days Worked", value="26")

with col2:
    emp_id = st.text_input("Employee ID", value="ABC0000")
    position = st.text_input("Position", value="Junior Developer")
    ifsc_code = st.text_input("IFSC Code", value="SGVCHJ8678")
    days_on_leave = st.text_input("Days On Leave", value="0")

# 2. Figures (Earnings & Deductions)
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

# 3. Summary Cards
st.write("---")
m1, m2, m3 = st.columns(3)
m1.metric("TOTAL EARNINGS", f"₹ {earnings['Total']:,.2f}")
m2.metric("TOTAL DEDUCTIONS", f"₹ {deductions['Total']:,.2f}")
m3.metric("NET PAY", f"₹ {net_salary:,.2f}")

# 4. Generate & Download Action
st.write("---")
if template_bytes:
    payload = {
        "details": {
            "pay_period": pay_period,
            "emp_name": emp_name,
            "account_number": account_number,
            "days_worked": days_worked,
            "emp_id": emp_id,
            "position": position,
            "ifsc_code": ifsc_code,
            "days_on_leave": days_on_leave
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
    st.error("Missing PDF template. Please upload 'Pugarch Payslip_1.pdf' in the sidebar.")
