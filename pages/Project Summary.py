# ---------------- Project Timesheet Entries (final fixed 2025-11-10 v17) ----------------
# Save as: Pages/Project Summary.py

import io
import os
import re
from datetime import datetime
import numpy as np
import pandas as pd
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm

# -------------------------------------------------------------------
# Config
# -------------------------------------------------------------------
st.set_page_config(page_title="Project Timesheet Entries", layout="wide")

MAIN_FILE = "Final_Consolidated_Project_Summary.xlsx"
TIME_FILE = "Cleaned_Time_Activities.xlsx"
TITLE = "Project Timesheet Entries"

# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------
def safe_read_excel(path, sheet_name=None):
    if not os.path.exists(path):
        st.error(f"❌ File not found: {path}")
        st.stop()
    try:
        df = pd.read_excel(path, sheet_name=sheet_name, engine="openpyxl")
        if isinstance(df, dict):
            df = df[list(df.keys())[0]]
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"❌ Failed to read {path}: {e}")
        st.stop()

def normalize_base(s):
    if pd.isna(s):
        return ""
    s = str(s).lower().replace("–", "-").replace("—", "-")
    s = re.sub(r"[^\w\s:\-]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def extract_project_key(s):
    s_norm = normalize_base(s)
    for pat in [r"\bco\s*-\s*(\d+)\b", r"\b(\d{3,6})\s*nb\b", r"\b(\d{3,6})\s*b\b"]:
        m = re.search(pat, s_norm)
        if m:
            return m.group(0)
    return " ".join(s_norm.split()[:8])

def pick_contribution_column(df):
    preferred = ["Billable Amount ($)", "Employee Contribution ($)", "Amount ($)"]
    for p in preferred:
        if p in df.columns:
            s = pd.to_numeric(df[p], errors="coerce")
            if s.notna().sum() > 0:
                return p
    numeric_cols = [c for c in df.columns if any(k in c.lower() for k in ["amount", "contribution", "$"])]
    if not numeric_cols:
        return None
    totals = {c: pd.to_numeric(df[c], errors="coerce").sum() for c in numeric_cols}
    return max(totals, key=totals.get)

def kpi_card(title, value, bg="#f8fafc", color="#111827"):
    return f"""
    <div style="background:{bg};border:1px solid #e5e7eb;border-radius:12px;
                padding:14px 16px;height:92px;display:flex;flex-direction:column;justify-content:center;">
        <div style="font-size:12px;color:#6b7280;margin-bottom:2px">{title}</div>
        <div style="font-size:26px;font-weight:700;color:{color};line-height:1">{value}</div>
    </div>
    """

def uniques(df, col):
    if col in df.columns:
        return sorted(df[col].dropna().astype(str).unique().tolist())
    return []

# -------------------------------------------------------------------
# Load Data
# -------------------------------------------------------------------
df_main = safe_read_excel(MAIN_FILE, sheet_name="Consolidated_Summary")
df_time = safe_read_excel(TIME_FILE)

for c in ["Total Billable ($)", "Total Estimate ($)", "Project Estimate EST", "Project Estimate"]:
    if c in df_main.columns:
        df_main[c] = pd.to_numeric(df_main[c], errors="coerce")

if "Last Activity Date" in df_main.columns:
    df_main["Last Activity Date"] = pd.to_datetime(df_main["Last Activity Date"], errors="coerce")

df_main["Adjusted Billable ($)"] = np.where(
    df_main.get("Territory", "").astype(str).str.upper().str.strip() == "IND",
    df_main["Total Billable ($)"] / 2,
    df_main["Total Billable ($)"],
)

est_col = "Total Estimate ($)" if "Total Estimate ($)" in df_main.columns else "Total Estimate"
if est_col not in df_main.columns:
    df_main["__EST__"] = 0.0
    est_col = "__EST__"

df_main["% Utilization"] = np.where(
    df_main[est_col] > 0,
    (df_main["Adjusted Billable ($)"] / df_main[est_col] * 100).round(1),
    0,
)
df_main["Exceeded ($)"] = (df_main["Adjusted Billable ($)"] - df_main[est_col]).clip(lower=0)
df_main["__proj_key__"] = df_main["Project Name"].apply(extract_project_key)

contrib_col = pick_contribution_column(df_time)
df_time[contrib_col] = pd.to_numeric(df_time[contrib_col], errors="coerce").fillna(0)
df_time["__proj_key__"] = df_time["Client full name"].apply(extract_project_key)
df_time["Employee"] = df_time["Employee"].astype(str).str.strip()

# -------------------------------------------------------------------
# Filters and Layout
# -------------------------------------------------------------------
st.markdown(f"<h1 style='margin-bottom:8px'>{TITLE}</h1>", unsafe_allow_html=True)

if "f_pm" not in st.session_state:
    st.session_state.f_pm = "All"
if "f_tl" not in st.session_state:
    st.session_state.f_tl = "All"

pm_options = ["All"] + uniques(df_main, "Project Lead")
if st.session_state.f_pm != "All":
    tl_filtered = df_main[df_main["Project Lead"] == st.session_state.f_pm]
    tl_options = ["All"] + sorted(tl_filtered["Team Lead"].dropna().astype(str).unique().tolist())
else:
    tl_options = ["All"] + uniques(df_main, "Team Lead")

if st.session_state.f_tl not in tl_options:
    st.session_state.f_tl = "All"

fcols = st.columns([2.0, 1.4, 1.4, 1.4, 1.4, 1.6])
with fcols[0]:
    q = st.text_input("Search Project", placeholder="type to filter by project name...").strip()

def update_pm():
    st.session_state.f_pm = st.session_state.sel_pm
    valid_tls = ["All"] + sorted(
        df_main[df_main["Project Lead"] == st.session_state.f_pm]["Team Lead"]
        .dropna().astype(str).unique().tolist()
    )
    if st.session_state.f_tl not in valid_tls:
        st.session_state.f_tl = "All"

def update_tl():
    st.session_state.f_tl = st.session_state.sel_tl

with fcols[1]:
    st.selectbox("Project Lead", pm_options, index=pm_options.index(st.session_state.f_pm),
                 key="sel_pm", on_change=update_pm)
with fcols[2]:
    st.selectbox("Team Lead", tl_options, index=tl_options.index(st.session_state.f_tl),
                 key="sel_tl", on_change=update_tl)
with fcols[3]:
    f_tr = st.selectbox("Territory", ["All"] + uniques(df_main, "Territory"))
with fcols[4]:
    f_ps = st.selectbox("Status", ["All"] + uniques(df_main, "Project Status"))
with fcols[5]:
    util_filter = st.selectbox(
        "Utilization Filter",
        ["All", "Under Utilized (< 80%)", "Within Budget (80–100%)", "Over Budget (100–120%)",
         "Highly Over Budget (> 120%)", "Sort: Low → High", "Sort: High → Low"],
    )

# -------------------------------------------------------------------
# Apply Filters
# -------------------------------------------------------------------
df = df_main.copy()
if q:
    df = df[df["Project Name"].str.contains(q, case=False, na=False)]
if st.session_state.f_pm != "All":
    df = df[df["Project Lead"].astype(str) == st.session_state.f_pm]
if st.session_state.f_tl != "All":
    df = df[df["Team Lead"].astype(str) == st.session_state.f_tl]
if f_tr != "All":
    df = df[df["Territory"].astype(str) == f_tr]
if f_ps != "All":
    df = df[df["Project Status"].astype(str) == f_ps]

if util_filter == "Under Utilized (< 80%)":
    df = df[df["% Utilization"] < 80]
elif util_filter == "Within Budget (80–100%)":
    df = df[(df["% Utilization"] >= 80) & (df["% Utilization"] <= 100)]
elif util_filter == "Over Budget (100–120%)":
    df = df[(df["% Utilization"] > 100) & (df["% Utilization"] <= 120)]
elif util_filter == "Highly Over Budget (> 120%)":
    df = df[df["% Utilization"] > 120]
elif util_filter == "Sort: Low → High":
    df = df.sort_values("% Utilization", ascending=True)
elif util_filter == "Sort: High → Low":
    df = df.sort_values("% Utilization", ascending=False)

# -------------------------------------------------------------------
# KPI Cards
# -------------------------------------------------------------------
total_projects = len(df)
within = int((df["% Utilization"] <= 100).sum())
exceeded = int((df["% Utilization"] > 100).sum())

k1, k2, k3, k4, k5 = st.columns(5)
with k1: st.markdown(kpi_card("Project Leads", st.session_state.f_pm), unsafe_allow_html=True)
with k2: st.markdown(kpi_card("Team Leads", st.session_state.f_tl), unsafe_allow_html=True)
with k3: st.markdown(kpi_card("Total Projects", f"{total_projects}"), unsafe_allow_html=True)
with k4: st.markdown(kpi_card("Within Budget", f"{within}", bg="#ecfdf5", color="#047857"), unsafe_allow_html=True)
with k5: st.markdown(kpi_card("Exceeded Budget", f"{exceeded}", bg="#fef2f2", color="#b91c1c"), unsafe_allow_html=True)

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# -------------------------------------------------------------------
# Project Cards
# -------------------------------------------------------------------
st.markdown("### 📊 Project Summary View")
if df.empty:
    st.warning("⚠️ No projects found for the selected filters.")
    st.stop()

project_data_for_pdf = []

for _, row in df.iterrows():
    proj = str(row["Project Name"])
    co_cols = [c for c in df_main.columns if re.match(r"CO-\d+", c, flags=re.I)]
    co_texts = [f"{c}: {float(row[c]):,.0f}" for c in co_cols if pd.notna(row.get(c)) and float(row[c]) != 0]
    co_html = f"<div style='font-size:12px;color:#4b5563;margin-bottom:4px'><i>{' | '.join(co_texts)}</i></div>" if co_texts else ""

    slice_df = df_time[df_time["__proj_key__"] == row["__proj_key__"]]
    emp_txt = "(No employee data)"
    emp_lines_pdf = ""
    if not slice_df.empty:
        agg = slice_df.groupby("Employee", as_index=False)[contrib_col].sum().sort_values(contrib_col, ascending=False)
        total_contrib = agg[contrib_col].sum()
        total = row["Adjusted Billable ($)"] if row["Adjusted Billable ($)"] > 0 else total_contrib
        if total > 0:
            emp_list = [f"{r['Employee']}: {round((r[contrib_col]/total)*100,1)}%" for _, r in agg.iterrows()]
            emp_txt = " | ".join(emp_list)
            emp_lines_pdf = ", ".join(emp_list)

    util = float(row["% Utilization"])
    est_total = float(row[est_col]) if pd.notna(row[est_col]) else 0
    spent = float(row["Adjusted Billable ($)"]) if pd.notna(row["Adjusted Billable ($)"]) else 0
    exceeded_amt = max(0, spent - est_total)

    blue_pct = min(est_total / spent, 1.0) * 100 if spent > 0 else 0
    red_pct = max((spent - est_total) / spent, 0) * 100 if spent > 0 else 0

    bar_html = f"""
    <div style='width:100%;background:#e5e7eb;border-radius:6px;height:8px;overflow:hidden;display:flex'>
        <div style='flex:0 0 {blue_pct}%;background:#3b82f6;height:100%'></div>
        {'<div style="flex:0 0 '+str(red_pct)+'%;background:#ef4444;height:100%"></div>' if red_pct>0 else ''}
    </div>
    """

    status_text = "Within Budget" if util <= 100 else "Exceeded Budget"
    status_color = "#059669" if util <= 100 else "#b91c1c"
    last_d = row["Last Activity Date"].strftime("%b %d, %Y") if pd.notna(row["Last Activity Date"]) else "No data"

    pl = str(row.get("Project Lead", "—"))
    tl = str(row.get("Team Lead", "—"))
    stt = str(row.get("Project Status", "—"))

    with st.container():
        left, right = st.columns([0.65, 0.35])
        with left:
            st.markdown(f"<div style='font-size:15px;font-weight:700;margin-bottom:2px'>{proj}</div>", unsafe_allow_html=True)
            if co_html:
                st.markdown(co_html, unsafe_allow_html=True)
            st.markdown(f"<div style='font-size:12px;color:#374151;margin-bottom:2px'><i>Employees:</i> {emp_txt}</div>", unsafe_allow_html=True)
            st.markdown(
                f"<div style='font-size:12px;color:#6b7280'><b>Last Activity:</b> {last_d} • "
                f"<b>Project Lead:</b> {pl} • <b>Team Lead:</b> {tl} • <b>Status:</b> {stt}</div>",
                unsafe_allow_html=True)
        with right:
            st.markdown(f"<div style='text-align:right;font-size:12px;color:{status_color};font-weight:700;margin-bottom:2px'>{status_text}</div>",
                        unsafe_allow_html=True)
            st.markdown(bar_html, unsafe_allow_html=True)
            st.markdown(
                f"<div style='font-size:12px;color:#6b7280;text-align:right'>"
                f"Budget: {est_total/1000:.1f}K | Spent: {spent/1000:.1f}K | Exceeded: {exceeded_amt/1000:.1f}K | Utilization: {util:.1f}%</div>",
                unsafe_allow_html=True)
        st.markdown("<hr style='margin:6px 0;border:0.5px solid #e5e7eb'>", unsafe_allow_html=True)

    project_data_for_pdf.append({
        "Project": proj,
        "CO": " | ".join(co_texts) if co_texts else "",
        "Last Activity": last_d,
        "Project Lead": pl,
        "Team Lead": tl,
        "Status": stt,
        "Budget": est_total,
        "Spent": spent,
        "Exceeded": exceeded_amt,
        "Utilization": util,
        "Employees": emp_lines_pdf
    })

# -------------------------------------------------------------------
# PDF Export
# -------------------------------------------------------------------
def make_pdf(projects):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=landscape(A4))
    W, H = landscape(A4)
    margin = 15 * mm
    x, y = margin, H - margin

    c.setFillColorRGB(1, 0.85, 0.85)
    c.rect(0, H - 20, W, 20, fill=True, stroke=False)
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(x, H - 15, TITLE)
    y -= 25

    c.setFont("Helvetica", 10)
    total = len(projects)
    within = sum(p["Utilization"] <= 100 for p in projects)
    exceeded = sum(p["Utilization"] > 100 for p in projects)
    pls = ", ".join(sorted(set(str(p["Project Lead"]) for p in projects)))
    tls = ", ".join(sorted(set(str(p["Team Lead"]) for p in projects)))
    c.drawString(x, y, f"Project Leads: {pls or 'All'}")
    y -= 12
    c.drawString(x, y, f"Team Leads: {tls or 'All'}")
    y -= 12
    c.drawString(x, y, f"Total Projects: {total}  |  Within: {within}  |  Exceeded: {exceeded}")
    y -= 18
    c.line(x, y, W - margin, y)
    y -= 15

    for p in projects:
        if y < 45 * mm:
            c.showPage()
            y = H - margin
            c.setFont("Helvetica-Bold", 13)
            c.drawString(x, y, TITLE)
            y -= 20

        util = p["Utilization"]
        status_text = "Within Budget" if util <= 100 else "Exceeded Budget"

        c.setFillColorRGB(0.92, 0.95, 0.99) if util <= 100 else c.setFillColorRGB(1.0, 0.92, 0.92)
        c.rect(x - 3, y - 3, W - 2 * margin + 6, 14, fill=True, stroke=False)
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x, y, p["Project"][:95])
        y -= 12

        if p["CO"]:
            c.setFont("Helvetica-Oblique", 8)
            c.setFillColor(colors.darkgray)
            c.drawString(x, y, p["CO"][:200])
            y -= 9
            c.setFillColor(colors.black)

        if p["Employees"]:
            c.setFont("Helvetica-Oblique", 8)
            c.setFillColor(colors.grey)
            c.drawString(x, y, f"Employees: {p['Employees'][:200]}")
            y -= 9
            c.setFillColor(colors.black)

        c.setFont("Helvetica", 8)
        c.drawString(x, y, f"Budget: {p['Budget']:,.0f} | Spent: {p['Spent']:,.0f} | Exceeded: {p['Exceeded']:,.0f} | Utilization: {p['Utilization']:.1f}%")
        y -= 9

        c.setFont("Helvetica", 8)
        c.setFillColor(colors.grey)
        c.drawString(x, y, f"PL: {p['Project Lead']} | TL: {p['Team Lead']} | Status: {p['Status']} | Last Activity: {p['Last Activity']}")
        y -= 10
        c.setFillColor(colors.black)

        # Utilization bar
        bar_x, bar_y = x, y
        bar_w, bar_h = 90 * mm, 4
        c.setStrokeColor(colors.lightgrey)
        c.rect(bar_x, bar_y, bar_w, bar_h, stroke=1, fill=0)

        if p["Spent"] > 0:
            blue_w = min(p["Budget"] / p["Spent"], 1.0) * bar_w
            red_w = max(p["Spent"] - p["Budget"], 0) / p["Spent"] * bar_w
            c.setFillColor(colors.blue)
            c.rect(bar_x, bar_y, blue_w, bar_h, stroke=0, fill=1)
            if red_w > 0:
                c.setFillColor(colors.red)
                c.rect(bar_x + blue_w, bar_y, red_w, bar_h, stroke=0, fill=1)
        y -= 12

        c.setFont("Helvetica-Bold", 8)
        c.setFillColor(colors.red if util > 100 else colors.green)
        c.drawString(x, y, status_text)
        c.setFillColor(colors.black)
        y -= 8

        c.setStrokeColor(colors.lightgrey)
        c.line(x, y, W - margin, y)
        y -= 12

    c.save()
    buf.seek(0)
    return buf

# -------------------------------------------------------------------
# PDF Download
# -------------------------------------------------------------------
if project_data_for_pdf:
    pdf_bytes = make_pdf(project_data_for_pdf)
    st.download_button(
        "📥 Download PDF (visible projects)",
        data=pdf_bytes,
        file_name=f"Project_Timesheet_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
        mime="application/pdf",
    )
else:
    st.info("No data available to export.")

# -------------------------------------------------------------------
# Final cleanup (prevents 'None' boxes)
# -------------------------------------------------------------------
for _ in range(5):
    st.markdown("", unsafe_allow_html=True)
