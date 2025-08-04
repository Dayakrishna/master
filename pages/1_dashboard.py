import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os

st.set_page_config(page_title="Enerzinx Dashboard", layout="wide")

st.markdown("<h1 style='text-align: center;'>Enerzinx Dashboard</h1>", unsafe_allow_html=True)

manual_targets = {
    "Sagar & Team": 1794808.38,
    "Vinoth & Team": 1513014.32,
    "Dr. Suresh & Team": 1711218.09,
    "Praveen & Team": 2783710.62,
    "Jigar & Team": 695927.66,
    "Dr. Amritpal Singh & Team": 759192
}

cleaned_df = st.session_state.get("cleaned_df")

if cleaned_df is None and os.path.exists("cleaned_data.xlsx"):
    cleaned_df = pd.read_excel("cleaned_data.xlsx")

if cleaned_df is None:
    st.warning("Cleaned timesheet data not found. Please process data in main.py first.")
    st.page_link("main.py", label="⬅️ Go to Data Upload Page", icon="📁")
else:
    if "Team Name" not in cleaned_df.columns or "Projects USD" not in cleaned_df.columns:
        st.error("❌ Required columns ('Team Name', 'Projects USD') are missing in the cleaned data.")
    else:
        cleaned_df["Team Name"] = cleaned_df["Team Name"].astype(str).str.strip()
        team_achieved_actual = cleaned_df.groupby("Team Name")["Projects USD"].sum()

        team_achieved = {team: team_achieved_actual.get(team, 0.0) for team in manual_targets.keys()}
        total_target = sum(manual_targets.values())
        total_achieved = sum(team_achieved.values())

        layout = st.columns([1, 2])

        with layout[0]:
            main_fig = go.Figure(data=[
                go.Pie(
                    labels=["Achieved", "Remaining"],
                    values=[total_achieved, max(0, total_target - total_achieved)],
                    hole=0.6,
                    marker=dict(colors=["#59622f", "#B0B734"]),
                    textinfo="percent",
                    hoverinfo="label+percent"
                )
            ])
            main_fig.update_layout(
                annotations=[dict(text="EZX Team", x=0.5, y=0.5, font_size=18, showarrow=False)],
                showlegend=False,
                margin=dict(t=10, b=10, l=10, r=10),
                height=360
            )
            st.plotly_chart(main_fig, use_container_width=True)

        with layout[1]:
            team_list = list(manual_targets.keys())
            color_palette = ["#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A", "#19D3F3"]
            line_color_map = dict(zip(team_list, color_palette))
            rows = [st.columns(3), st.columns(3)]
            for idx, team in enumerate(team_list):
                target = manual_targets[team]
                achieved = team_achieved[team]
                remaining = max(0, target - achieved)
                fig = go.Figure(data=[
                    go.Pie(
                        labels=["Achieved", "Remaining"],
                        values=[achieved, remaining],
                        hole=0.6,
                        marker=dict(colors=[color_palette[idx % len(color_palette)], "#E0E0E0"]),
                        textinfo="percent+label",
                        hoverinfo="label+percent"
                    )
                ])
                fig.update_layout(
                    annotations=[dict(text=team.replace(' & Team', ''), x=0.5, y=0.5, font_size=13, showarrow=False)],
                    showlegend=False,
                    margin=dict(t=10, b=10, l=10, r=10),
                    height=180
                )
                with rows[idx // 3][idx % 3]:
                    st.plotly_chart(fig, use_container_width=True)

        # --- Weekly Trends Chart ---
        if {"Week Number", "Duration", "Product/Service full name", "Hours"}.issubset(cleaned_df.columns):
            st.markdown("<h3 style='margin-top: 40px;'>Weekly Project Utilization (%)</h3>", unsafe_allow_html=True)

            cleaned_df["Week Number"] = cleaned_df["Week Number"].astype(str)
            cleaned_df["Employee Name"] = cleaned_df["Employee Name"].astype(str).str.strip()

            trends = []
            for team in manual_targets:
                team_df = cleaned_df[cleaned_df["Team Name"] == team]
                if team_df.empty:
                    continue

                weeks_sorted = sorted(team_df["Week Number"].unique(), key=lambda w: (0 if w == 'Before Week 1' else int(w.split()[-1])))
                for week in weeks_sorted:
                    week_df = team_df[team_df["Week Number"] == week]
                    active_employees = week_df["Employee Name"].unique()
                    if len(active_employees) == 0:
                        continue
                    base_hours = len(active_employees) * 40
                    time_off_hours = week_df[week_df["Product/Service full name"] == "Time off"]["Hours"].sum()
                    available_hours = base_hours - time_off_hours
                    project_hours = week_df[week_df["Product/Service full name"] == "Projects"]["Hours"].sum()
                    utilization = (project_hours / available_hours * 100) if available_hours > 0 else 0
                    trends.append({"Week": week, "Team": team, "Project %": round(utilization, 2)})

            trend_df = pd.DataFrame(trends)
            if not trend_df.empty:
                fig_line = px.line(trend_df, x="Week", y="Project %", color="Team", markers=True, color_discrete_map=line_color_map)
                fig_line.update_layout(
                    height=400,
                    margin=dict(t=30, l=10, r=10, b=10),
                    shapes=[
                        dict(type='line', xref='paper', x0=0, x1=1, y0=75, y1=75,
                             line=dict(dash='dash', color='gray'))
                    ]
                )
                st.plotly_chart(fig_line, use_container_width=True)
            else:
                st.info("No weekly project hour data available to display.")

        # --- Total EZX Team Engagement ---

        # --- Last Week EZX Team Engagement ---
        if "Week Number" in cleaned_df.columns:
            st.markdown("<h3 style='margin-top: 40px;'>Last Week Team Engagement}</h3>", unsafe_allow_html=True)
            cleaned_df["Week Number"] = cleaned_df["Week Number"].astype(str)
            cleaned_df["Employee Name"] = cleaned_df["Employee Name"].astype(str).str.strip()

            team_summary_week = []
            team_availabilities = []

            # Get latest week (excluding 'Before Week 1')
            valid_weeks = [w for w in cleaned_df["Week Number"].unique() if w != 'Before Week 1']
            if valid_weeks:
                latest_week = sorted(valid_weeks, key=lambda w: int(w.split()[-1]))[-1]

                for team in manual_targets:
                    team_df = cleaned_df[(cleaned_df["Team Name"] == team) & (cleaned_df["Week Number"] == latest_week)]
                    if team_df.empty:
                        continue
                    total_team_hours = team_df["Hours"].sum()
                    team_time_off = team_df[team_df["Product/Service full name"] == "Time off"]["Hours"].sum()
                    team_available = total_team_hours - team_time_off
                    team_availabilities.append(team_available)
                    service_sum = team_df[team_df["Product/Service full name"] != "Time off"] \
                        .groupby("Product/Service full name")["Hours"].sum().reset_index()
                    team_summary_week.append(service_sum)

                if team_summary_week:
                    combined_week = pd.concat(team_summary_week)
                    summary_week = combined_week.groupby("Product/Service full name")["Hours"].sum().reset_index()
                    total_week_available = sum(team_availabilities)
                    summary_week["% of Time"] = (summary_week["Hours"] / total_week_available * 100).round(2)

                    bar_fig_week = px.bar(
                        summary_week,
                        x="Product/Service full name",
                        y="% of Time",
                        text="% of Time",
                        hover_data={"Hours": True, "% of Time": True},
                        color="Product/Service full name",
                        color_discrete_sequence=['#1f77b4', '#2ca02c', '#ff7f0e', '#9467bd', '#8c564b', '#17becf']
                    )
                    bar_fig_week.update_layout(
                        showlegend=False,
                        height=400,
                        yaxis_title=f"% of Available Time in {latest_week}"
                    )
                    st.plotly_chart(bar_fig_week, use_container_width=True)
        if {"Product/Service full name", "Hours"}.issubset(cleaned_df.columns):
            st.markdown("<h3 style='margin-top: 40px;'>Total EZX Team Engagement - All Weeks Till Date</h3>", unsafe_allow_html=True)
            total_hours = cleaned_df[cleaned_df["Team Name"].notna()]["Hours"].sum()
            time_off_hours = cleaned_df[(cleaned_df["Product/Service full name"] == "Time off") & (cleaned_df["Team Name"].notna())]["Hours"].sum()
            available_time = total_hours - time_off_hours
            team_summary = []
            for team in manual_targets:
                team_df = cleaned_df[cleaned_df["Team Name"] == team]
                if team_df.empty:
                    continue
                total_team_hours = team_df["Hours"].sum()
                team_time_off = team_df[team_df["Product/Service full name"] == "Time off"]["Hours"].sum()
                team_available = total_team_hours - team_time_off
                service_sum = team_df[team_df["Product/Service full name"] != "Time off"].groupby("Product/Service full name")["Hours"].sum().reset_index()
                service_sum["Available"] = team_available
                team_summary.append(service_sum)
            combined = pd.concat(team_summary)
            summary = combined.groupby("Product/Service full name")[["Hours", "Available"]].sum().reset_index()
            summary = summary[summary["Product/Service full name"] != "Time off"]
            total_available = sum([df["Available"].max() for df in team_summary if not df.empty])
            summary["% of Time"] = (summary["Hours"] / total_available * 100).round(2)

            bar_fig = px.bar(summary, x="Product/Service full name", y="% of Time", text="% of Time", color="Product/Service full name", color_discrete_sequence=px.colors.qualitative.Set3)
            bar_fig.update_layout(showlegend=False, height=400, yaxis_title="% of Available Time")
            st.plotly_chart(bar_fig, use_container_width=True)
