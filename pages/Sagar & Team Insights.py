import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import hashlib

# -------------------
# Password Protection
# -------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate(username, password, credentials):
    return credentials.get(username) == hash_password(password)

# Set valid users with hashed password "teamsagar"
PASSWORD_HASH = hash_password("teamsagar")
CREDENTIALS = {
    "sagar": PASSWORD_HASH,
    "admin": PASSWORD_HASH,
    "viewer": PASSWORD_HASH
}

# Authentication
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔒 Login to Access Insights")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if authenticate(username, password, CREDENTIALS):
            st.session_state.logged_in = True
            st.success("Login successful!")
            st.rerun()
        else:
            st.error("Invalid username or password.")
    st.stop()

# ---------------------------
# Main App: Sagar & Team View
# ---------------------------
st.set_page_config(page_title="Sagar & Team Insights", layout="wide")
st.title("📊 Sagar & Team Detailed Insights")

# Load cleaned data
cleaned_df = st.session_state.get("cleaned_df")
if cleaned_df is None and os.path.exists("cleaned_data.xlsx"):
    cleaned_df = pd.read_excel("cleaned_data.xlsx")

if cleaned_df is None:
    st.warning("Please process the data from the main dashboard first.")
else:
    df = cleaned_df.copy()
    df = df[df["Team Name"] == "Sagar & Team"]
    df["Week Number"] = df["Week Number"].astype(str)
    df["Employee Name"] = df["Employee Name"].astype(str).str.strip()

    st.subheader("Last Week Productivity")
    valid_weeks = [w for w in df["Week Number"].unique() if w != "Before Week 1"]
    latest_week = sorted(valid_weeks, key=lambda w: int(w.split()[-1]))[-1]
    latest_week_df = df[df["Week Number"] == latest_week]

    all_employees = latest_week_df["Employee Name"].unique()
    project_hours = latest_week_df[latest_week_df["Product/Service full name"] == "Projects"] \
        .groupby("Employee Name")["Hours"].sum().reindex(all_employees, fill_value=0).reset_index()
    project_hours.columns = ["Employee Name", "Hours"]

    fig = px.bar(project_hours, x="Employee Name", y="Hours", text="Hours", color="Employee Name")
    fig.update_layout(height=350, margin=dict(t=10, b=10, l=10, r=10))
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Last Breakdown by Product/Service")
    services = df[df["Product/Service full name"] != "Time off"]
    total_available = df["Hours"].sum() - df[df["Product/Service full name"] == "Time off"]["Hours"].sum()
    agg = services.groupby("Product/Service full name")["Hours"].sum().reset_index()
    agg["% of Available Time"] = (agg["Hours"] / total_available * 100).round(2)
    agg = agg.sort_values("% of Available Time", ascending=False)
    fig2 = px.bar(agg, x="Product/Service full name", y="% of Available Time", text="% of Available Time", color="Product/Service full name")
    fig2.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Last Week Breakdown by Designation")
    designation_df = df[df["Week Number"] == latest_week]
    designation_df = designation_df[designation_df["Position"].notna()]
    role_summary = designation_df.groupby(["Position", "Product/Service full name"])["Hours"].sum().reset_index()
    total_by_position = designation_df.groupby("Position")["Hours"].sum().reset_index().rename(columns={"Hours": "Total"})
    merged = pd.merge(role_summary, total_by_position, on="Position")
    merged["% of Role Time"] = (merged["Hours"] / merged["Total"] * 100).round(2)

    fig3 = px.bar(
        merged,
        x="Product/Service full name",
        y="% of Role Time",
        color="Position",
        text="% of Role Time",
        barmode="group",
        text_auto=True
    )
    fig3.update_layout(height=400, yaxis_title="% of Role Time", xaxis_title="Product/Service full name")
    st.plotly_chart(fig3, use_container_width=True)

    st.subheader("Team Target Overview and Project % Trend")
    col_a, col_b = st.columns(2)

    with col_a:
        achieved = df[df["Product/Service full name"] == "Projects"]["Projects USD"].sum()
    team_target = 1749439.06

    donut_fig = go.Figure(
        data=[
            go.Pie(
                labels=["Achieved", "Remaining"],
                values=[achieved, max(0, team_target - achieved)],
                hole=0.6,
                marker=dict(colors=["#59622f", "#B0B734"]),
                textinfo="percent",
                hoverinfo="label+percent"
            )
        ]
    )

    donut_fig.update_layout(
        height=500,
        showlegend=False,
        annotations=[dict(text="Target", x=0.5, y=0.5, font_size=16, showarrow=False)]
    )

    st.plotly_chart(donut_fig, use_container_width=True)

    with col_b:
        trends = []
    for week in sorted(df[df['Week Number'] != 'Before Week 1']["Week Number"].unique(), key=lambda w: int(w.split()[-1])):
        week_df = df[df["Week Number"] == week]
        time_off = week_df[week_df["Product/Service full name"] == "Time off"]["Hours"].sum()
        total = week_df["Hours"].sum() - time_off
        projects = week_df[week_df["Product/Service full name"] == "Projects"]["Hours"].sum()
        trends.append({"Week": week, "% Projects": round((projects / total * 100) if total > 0 else 0, 2)})
    trend_df = pd.DataFrame(trends)
    trend_fig = px.line(trend_df, x="Week", y="% Projects", markers=True)
    trend_fig.add_shape(
        type="line",
        x0=0, x1=1, xref='paper',
        y0=75, y1=75, yref='y',
        line=dict(color="gray", dash="dash")
    )
    trend_fig.update_layout(height=300)
    st.plotly_chart(trend_fig, use_container_width=True)

    st.subheader("Individual Service Distribution")
    selected_employee = st.selectbox("Select Employee", sorted(df["Employee Name"].unique()))
    view_mode = st.radio("View by", ["Overview", "Week", "Month"], horizontal=True)

    emp_df = df[df["Employee Name"] == selected_employee]

    if view_mode == "Overview":
        breakdown = emp_df.groupby("Product/Service full name")["Hours"].sum().reset_index()
        breakdown["% of Time"] = (breakdown["Hours"] / breakdown["Hours"].sum() * 100).round(2)
        fig_emp = px.bar(breakdown, x="Product/Service full name", y="% of Time", text="% of Time",
                         color="Product/Service full name")
        st.plotly_chart(fig_emp, use_container_width=True)

    elif view_mode == "Week":
        week_list = sorted(emp_df["Week Number"].unique(),
                           key=lambda w: (0 if w == 'Before Week 1' else int(w.split()[-1])))
        selected_week = st.selectbox("Select Week", week_list)
        week_df = emp_df[emp_df["Week Number"] == selected_week]

        st.markdown("##### Activity Details")
        styled_df = week_df[
            ["Activity date", "Client full name", "Product/Service full name", "Hours", "Description"]].copy()
        styled_df.columns = ["Date", "Client", "Service", "Hours", "Description"]

        # Render with scroll and wrap
        st.dataframe(styled_df.style.set_properties(**{
            'white-space': 'pre-wrap',
            'overflow-wrap': 'break-word'
        }), use_container_width=True)

        breakdown = week_df.groupby("Product/Service full name")["Hours"].sum().reset_index()
        breakdown["% of Time"] = (breakdown["Hours"] / breakdown["Hours"].sum() * 100).round(2)
        fig_emp = px.bar(breakdown, x="Product/Service full name", y="% of Time", text="% of Time",
                         color="Product/Service full name")
        st.plotly_chart(fig_emp, use_container_width=True)

        description = f"**{selected_employee}'s performance in {selected_week}:** {breakdown.to_string(index=False)}"
        st.markdown(description)

    elif view_mode == "Month":
        emp_df["Month"] = pd.to_datetime(emp_df["Activity date"], format="%d/%m/%Y", errors='coerce').dt.strftime(
            "%B %Y")
        month_list = emp_df["Month"].dropna().unique()
        selected_month = st.selectbox("Select Month", sorted(month_list))
        month_df = emp_df[emp_df["Month"] == selected_month]

        st.markdown("##### Monthly Activity Details")
        styled_month_df = month_df[
            ["Activity date", "Client full name", "Product/Service full name", "Hours", "Description"]].copy()
        styled_month_df.columns = ["Date", "Client", "Service", "Hours", "Description"]
        st.dataframe(styled_month_df.style.set_properties(**{
            'white-space': 'pre-wrap',
            'overflow-wrap': 'break-word'
        }), use_container_width=True)

        breakdown = month_df.groupby("Product/Service full name")["Hours"].sum().reset_index()
        breakdown["% of Time"] = (breakdown["Hours"] / breakdown["Hours"].sum() * 100).round(2)
        fig_emp = px.bar(breakdown, x="Product/Service full name", y="% of Time", text="% of Time",
                         color="Product/Service full name")
        st.plotly_chart(fig_emp, use_container_width=True)

        description = f"**{selected_employee}'s performance in {selected_month}:** {breakdown.to_string(index=False)}"
        st.markdown(description)

    elif view_mode == "Month":
        emp_df["Month"] = pd.to_datetime(emp_df["Activity date"], format="%d/%m/%Y", errors='coerce').dt.strftime("%B %Y")
        month_list = emp_df["Month"].dropna().unique()
        selected_month = st.selectbox("Select Month", sorted(month_list))
        month_df = emp_df[emp_df["Month"] == selected_month]
        breakdown = month_df.groupby("Product/Service full name")["Hours"].sum().reset_index()
        breakdown["% of Time"] = (breakdown["Hours"] / breakdown["Hours"].sum() * 100).round(2)
        fig_emp = px.bar(breakdown, x="Product/Service full name", y="% of Time", text="% of Time",
                         color="Product/Service full name")
        st.plotly_chart(fig_emp, use_container_width=True)

        description = f"**{selected_employee}'s performance in {selected_month}:** {breakdown.to_string(index=False)}"
        st.markdown(description)

    st.subheader("Project Hours % of Available Time (Overall)")

    total_hours_df = df.groupby("Employee Name")["Hours"].sum().reset_index().rename(columns={"Hours": "Total Hours"})
    time_off_df = df[df["Product/Service full name"] == "Time off"] \
        .groupby("Employee Name")["Hours"].sum().reset_index().rename(columns={"Hours": "Time Off"})
    project_df = df[df["Product/Service full name"] == "Projects"] \
        .groupby("Employee Name")["Hours"].sum().reset_index().rename(columns={"Hours": "Project Hours"})

    overall_df = pd.merge(total_hours_df, time_off_df, on="Employee Name", how="left")
    overall_df = pd.merge(overall_df, project_df, on="Employee Name", how="left")
    overall_df["Time Off"] = overall_df["Time Off"].fillna(0)
    overall_df["Project Hours"] = overall_df["Project Hours"].fillna(0)

    overall_df["Available Time"] = overall_df["Total Hours"] - overall_df["Time Off"]
    overall_df["% Project Time"] = (overall_df["Project Hours"] / overall_df["Available Time"] * 100).round(2)

    overall_df = overall_df.sort_values("% Project Time", ascending=True)
    fig_overall = px.bar(overall_df,
                         x="% Project Time",
                         y="Employee Name",
                         orientation="h",
                         text="% Project Time",
                         color="Employee Name")
    fig_overall.update_layout(height=400, margin=dict(t=10, b=10, l=10, r=10), showlegend=False)
    st.plotly_chart(fig_overall, use_container_width=True)
