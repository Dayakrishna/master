import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

st.set_page_config(page_title="Praveen & Team Insights", layout="wide")
st.title("📊 Praveen & Team Detailed Insights")

# Load the data
file_path = "cleaned_data.xlsx"
df = pd.read_excel(file_path)
df = df[df["Team Name"] == "Praveen & Team"]
df["Week Number"] = df["Week Number"].astype(str)
df["Employee Name"] = df["Employee Name"].astype(str).str.strip()

# --- Last Week Productivity ---
valid_weeks = [w for w in df["Week Number"].unique() if w != "Before Week 1"]
latest_week = sorted(valid_weeks, key=lambda w: int(w.split()[-1]))[-1]
latest_week_df = df[df["Week Number"] == latest_week]

st.subheader("Last Week Productivity Hours")
employees = latest_week_df["Employee Name"].unique()
project_hours = latest_week_df[latest_week_df["Product/Service full name"] == "Projects"]
project_hours = project_hours.groupby("Employee Name")["Hours"].sum().reindex(employees, fill_value=0).reset_index()
fig = px.bar(project_hours, x="Employee Name", y="Hours", text="Hours", color="Employee Name")
fig.update_layout(height=350, margin=dict(t=10, b=10))
st.plotly_chart(fig, use_container_width=True)

# --- % Breakdown by Product/Service ---
st.subheader(f"{latest_week} Breakdown by Product/Service")
services_df = latest_week_df[latest_week_df["Product/Service full name"] != "Time off"]
num_employees = latest_week_df["Employee Name"].nunique()
expected_hours = num_employees * 40
team_time_off = latest_week_df[latest_week_df["Product/Service full name"] == "Time off"]["Hours"].sum()
available = expected_hours - team_time_off
service_summary = services_df.groupby("Product/Service full name")["Hours"].sum().reset_index()
service_summary["% of Available Time"] = (service_summary["Hours"] / available * 100).round(2)
fig2 = px.bar(service_summary, x="Product/Service full name", y="% of Available Time", text="% of Available Time",
              color="Product/Service full name")
fig2.update_layout(height=400, showlegend=False)
st.plotly_chart(fig2, use_container_width=True)

# --- % Breakdown by Product/Service by Position ---
st.subheader(f"{latest_week} - Position Breakdown by Product/Service")
position_df = latest_week_df[latest_week_df["Product/Service full name"] != "Time off"]
position_df = position_df[position_df["Position"].notna()]

position_summary = position_df.groupby(["Position", "Product/Service full name"])["Hours"].sum().reset_index()
position_count = latest_week_df.groupby("Position")["Employee Name"].nunique().reset_index().rename(columns={"Employee Name": "Headcount"})
position_time_off = latest_week_df[latest_week_df["Product/Service full name"] == "Time off"].groupby("Position")["Hours"].sum().reset_index().rename(columns={"Hours": "Time Off"})

position_summary = pd.merge(position_summary, position_count, on="Position", how="left")
position_summary = pd.merge(position_summary, position_time_off, on="Position", how="left")
position_summary["Time Off"] = position_summary["Time Off"].fillna(0)
position_summary["Available"] = position_summary["Headcount"] * 40 - position_summary["Time Off"]
position_summary["% of Available Time"] = (position_summary["Hours"] / position_summary["Available"] * 100).round(2)

fig_pos = px.bar(position_summary, x="Product/Service full name", y="% of Available Time", color="Position",
                 barmode="group", text="% of Available Time")
fig_pos.update_layout(height=400, xaxis_title="Product/Service", yaxis_title="% of Available Time")
st.plotly_chart(fig_pos, use_container_width=True)

# --- Time Off by Position ---
st.subheader(f"{latest_week} - Time Off Breakdown by Position and Employee")
timeoff_df = latest_week_df[latest_week_df["Product/Service full name"] == "Time off"]
timeoff_by_position_employee = timeoff_df.groupby(["Position", "Employee Name"])["Hours"].sum().reset_index()
fig_timeoff = px.bar(timeoff_by_position_employee, x="Hours", y="Employee Name", color="Position",
                     orientation="h", text="Hours")
fig_timeoff.update_layout(height=500, xaxis_title="Time Off Hours", yaxis_title="Employee", barmode="stack")
st.plotly_chart(fig_timeoff, use_container_width=True)

# --- Weekly Project % Trend ---
st.subheader("Team Project % Trend")
trend = []
for week in sorted(valid_weeks, key=lambda w: int(w.split()[-1])):
    week_df = df[df["Week Number"] == week]
    num_emp_week = week_df["Employee Name"].nunique()
    expected_weekly_hours = num_emp_week * 40
    time_off_week = week_df[week_df["Product/Service full name"] == "Time off"]["Hours"].sum()
    available_weekly_hours = expected_weekly_hours - time_off_week
    project_hours_week = week_df[week_df["Product/Service full name"] == "Projects"]["Hours"].sum()
    pct = round((project_hours_week / available_weekly_hours * 100), 2) if available_weekly_hours > 0 else 0
    trend.append({"Week": week, "% Projects": pct})
trend_df = pd.DataFrame(trend)
fig3 = px.line(trend_df, x="Week", y="% Projects", markers=True)
fig3.update_layout(height=350)
st.plotly_chart(fig3, use_container_width=True)

# --- Target Overview ---
st.subheader("Target vs Achieved")
achieved = df[df["Product/Service full name"] == "Projects"]["Projects USD"].sum()
team_target = 2783710.62
donut_fig = go.Figure(data=[
    go.Pie(labels=["Achieved", "Remaining"],
           values=[achieved, max(0, team_target - achieved)],
           hole=0.6,
           marker=dict(colors=["#607d8b", "#cfd8dc"]),
           textinfo="percent")
])
donut_fig.update_layout(height=400, showlegend=True)
st.plotly_chart(donut_fig, use_container_width=True)

# --- Overall Breakdown by Product/Service ---
st.subheader("Overall Breakdown by Product/Service")
overall_services_df = df[df["Product/Service full name"] != "Time off"]
total_employees = df["Employee Name"].nunique()
total_expected_hours = total_employees * 40 * len(valid_weeks)
total_time_off = df[df["Product/Service full name"] == "Time off"]["Hours"].sum()
total_available = total_expected_hours - total_time_off

overall_summary = overall_services_df.groupby("Product/Service full name")["Hours"].sum().reset_index()
overall_summary["% of Available Time"] = (overall_summary["Hours"] / total_available * 100).round(2)
fig4 = px.bar(overall_summary, x="Product/Service full name", y="% of Available Time", text="% of Available Time",
              color="Product/Service full name")
fig4.update_layout(height=400, showlegend=False)
st.plotly_chart(fig4, use_container_width=True)

# --- Individual Project % of Available Time (Stacked) ---
st.subheader("Overall Project % by Employee")
individual_data = []
for emp in df["Employee Name"].unique():
    emp_df = df[df["Employee Name"] == emp]
    weeks = emp_df["Week Number"].nunique()
    expected = weeks * 40
    time_off = emp_df[emp_df["Product/Service full name"] == "Time off"]["Hours"].sum()
    available = expected - time_off
    project = emp_df[emp_df["Product/Service full name"] == "Projects"]["Hours"].sum()
    pct = round((project / available * 100), 2) if available > 0 else 0
    individual_data.append({"Employee Name": emp, "% Project Time": pct})
individual_df = pd.DataFrame(individual_data).sort_values("% Project Time")
fig5 = px.bar(individual_df, x="% Project Time", y="Employee Name", text="% Project Time",
              orientation="h", color="Employee Name")
fig5.update_layout(height=500, showlegend=False)
st.plotly_chart(fig5, use_container_width=True)

# --- Employee Breakdown View ---
st.subheader("Employee-Level Breakdown")
selected_emp = st.selectbox("Select Employee", sorted(df["Employee Name"].unique()))
emp_data = df[df["Employee Name"] == selected_emp]
view_mode = st.radio("View Mode", ["Overall", "Weekly", "Monthly"], horizontal=True)

if view_mode == "Overall":
    time_off = emp_data[emp_data["Product/Service full name"] == "Time off"]["Hours"].sum()
    total_expected = emp_data["Week Number"].nunique() * 40
    available = total_expected - time_off
    breakdown = emp_data[emp_data["Product/Service full name"] != "Time off"]
    summary = breakdown.groupby("Product/Service full name")["Hours"].sum().reset_index()
    summary["% of Available Time"] = (summary["Hours"] / available * 100).round(2)
    fig = px.bar(summary, x="Product/Service full name", y="% of Available Time", text="% of Available Time",
                 color="Product/Service full name")
    st.plotly_chart(fig, use_container_width=True)

elif view_mode == "Weekly":
    selected_week = st.selectbox("Select Week", sorted(emp_data["Week Number"].unique(), key=lambda w: int(w.split()[-1])))
    week_data = emp_data[emp_data["Week Number"] == selected_week]
    time_off = week_data[week_data["Product/Service full name"] == "Time off"]["Hours"].sum()
    available = 40 - time_off
    breakdown = week_data[week_data["Product/Service full name"] != "Time off"]
    summary = breakdown.groupby("Product/Service full name")["Hours"].sum().reset_index()
    summary["% of Available Time"] = (summary["Hours"] / available * 100).round(2)
    fig = px.bar(summary, x="Product/Service full name", y="% of Available Time", text="% of Available Time",
                 color="Product/Service full name")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Weekly Activity Log")
    log = week_data[["Client full name", "Product/Service full name", "Description", "Rates", "Duration"]]
    st.dataframe(log.reset_index(drop=True))

elif view_mode == "Monthly":
    emp_data["Activity date"] = pd.to_datetime(emp_data["Activity date"], errors='coerce')
    emp_data["Month"] = emp_data["Activity date"].dt.strftime("%B %Y")
    selected_month = st.selectbox("Select Month", sorted(emp_data["Month"].dropna().unique()))
    month_data = emp_data[emp_data["Month"] == selected_month]
    time_off = month_data[month_data["Product/Service full name"] == "Time off"]["Hours"].sum()
    available = len(month_data["Week Number"].unique()) * 40 - time_off
    breakdown = month_data[month_data["Product/Service full name"] != "Time off"]
    summary = breakdown.groupby("Product/Service full name")["Hours"].sum().reset_index()
    summary["% of Available Time"] = (summary["Hours"] / available * 100).round(2)
    fig = px.bar(summary, x="Product/Service full name", y="% of Available Time", text="% of Available Time",
                 color="Product/Service full name")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Monthly Activity Log")
    log = month_data[["Client full name", "Product/Service full name", "Description", "Rates", "Duration"]]
    st.dataframe(log.reset_index(drop=True))
