import streamlit as st
import pandas as pd
import re
import warnings

# ----------------------------------------------------------
# PAGE CONFIG + WARNINGS
# ----------------------------------------------------------
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")
st.set_page_config(page_title="Budget Estimator", layout="wide")
st.title("📊 Budget Estimator — v13 (Corrected Unmapped Time Entries)")

# ----------------------------------------------------------
# HELPERS
# ----------------------------------------------------------
def normalize_text(s):
    """Normalize strings for reliable matching."""
    if pd.isna(s):
        return ""
    s = str(s).lower().strip()
    s = re.sub(r"[\s\n\r\t]+", " ", s)
    s = s.replace("–", "-").replace("—", "-")
    s = re.sub(r"[^\w\s:\-]", "", s)
    return s

def convert_duration(v):
    """Convert HH:MM style durations to hours."""
    if pd.isna(v):
        return 0
    v = str(v).strip()
    try:
        if ":" in v:
            h, m = v.split(":")
            return float(h) + float(m) / 60
        return float(v)
    except:
        return 0

# Hourly rates map
RATE_MAP = {
    "Rates:Application Engineer I":100,
    "Rates:Senior Engineer I":200,
    "Rates:Application Engineer II":125,
    "Rates:Senior Director":300,
    "Rates:Director/Principal Engineer- II":275,
    "Rates:Intern":50,
    "Rates:Principal Engineer I":250,
    "Rates:Senior Engineer II":225,
    "Rates:CAD Designer":100,
    "Rates:Admin Assistant":50
}

# ----------------------------------------------------------
# STEP 1 — UPLOAD PROJECT FILES
# ----------------------------------------------------------
st.header("Step 1 — Upload Project Files")
c1, c2 = st.columns(2)
with c1:
    f_est = st.file_uploader("📗 Upload 'Estimates by Client' Excel", type=["xlsx","xls"])
with c2:
    f_mat = st.file_uploader("📘 Upload 'Project Matrix' Excel", type=["xlsx","xls"])

if not (f_est and f_mat):
    st.stop()

# Clean Estimates by Client
df_est_raw = pd.read_excel(f_est, header=None)
hdr_idx = df_est_raw[df_est_raw.iloc[:,0].astype(str).str.strip()=="Client"].index
hdr = hdr_idx[0] if len(hdr_idx)>0 else 0

df_est = pd.read_excel(f_est, header=hdr)
df_est = df_est.loc[:,~df_est.columns.str.contains("^Unnamed")]

st.subheader("✅ Cleaned 'Estimates by Client'")
st.dataframe(df_est.head(), use_container_width=True)

out="Cleaned_Estimates_by_Client.xlsx"
df_est.to_excel(out,index=False)
with open(out,"rb") as f:
    st.download_button("📥 Download Cleaned 'Estimates by Client'", f, file_name=out)

# Load Project Matrix
xls = pd.ExcelFile(f_mat)
first_sheet = xls.sheet_names[0]
df_mat = pd.read_excel(xls, sheet_name=first_sheet, dtype=str)

st.subheader(f"📄 Project Matrix (Sheet: {first_sheet})")
st.dataframe(df_mat.head(), use_container_width=True)

mat_out="Cleaned_Project_Matrix.xlsx"
df_mat.to_excel(mat_out,index=False)
with open(mat_out,"rb") as f:
    st.download_button("📥 Download Cleaned 'Project Matrix'", f, file_name=mat_out)

st.session_state["df_mat"] = df_mat

# ----------------------------------------------------------
# STEP 2 — UPLOAD TIME ACTIVITIES
# ----------------------------------------------------------
st.header("Step 2 — Upload Time Activities")
f_act = st.file_uploader("📂 Upload 'Time Activities by Employee Detail' Excel", type=["xlsx","xls"])

if not f_act:
    st.stop()

df = pd.read_excel(f_act, skiprows=4)
first_col = df.columns[0]
df.rename(columns={first_col:"Employee"}, inplace=True)
df["Employee"] = df["Employee"].ffill()

df = df[df["Product/Service full name"].astype(str).str.startswith("Rates:")]
df["Duration (hrs)"] = df["Duration"].apply(convert_duration)
df["Rate ($/hr)"] = df["Product/Service full name"].map(RATE_MAP).fillna(0)
df["Billable Amount ($)"] = df["Duration (hrs)"] * df["Rate ($/hr)"]

st.success(f"✅ Cleaned {len(df)} time entries")
st.dataframe(df.head(), use_container_width=True)

act_out="Cleaned_Time_Activities.xlsx"
df.to_excel(act_out,index=False)
with open(act_out,"rb") as f:
    st.download_button("📥 Download Cleaned 'Time Activities'", f, file_name=act_out)

# ----------------------------------------------------------
# STEP 3 — CONSOLIDATE PROJECTS (MAIN + COs)
# ----------------------------------------------------------
st.header("Step 3 — Consolidate Projects (Main + COs)")

df_mat = st.session_state["df_mat"].copy()
df_mat.columns = [c.strip() for c in df_mat.columns]

# numeric cleanup
est_cols = ["Project Estimate EST","CO-1 EST","CO-2 EST","CO-3 EST","CO-4 EST","CO-5 EST"]
for c in est_cols:
    if c in df_mat.columns:
        df_mat[c] = (df_mat[c].astype(str).str.extract(r"([\d,\.]+)")[0]
                     .replace(",","",regex=True))
        df_mat[c] = pd.to_numeric(df_mat[c], errors="coerce").fillna(0)

# metadata columns
lead_col  = next((c for c in df_mat.columns if c.lower().startswith("project lead")), None)
team_col  = next((c for c in df_mat.columns if c.lower().startswith("team lead")), None)
terr_col  = next((c for c in df_mat.columns if "territory" in c.lower()), None)
status_col= next((c for c in df_mat.columns if "status" in c.lower()), None)

# CO names + totals
co_name_cols = [c for c in ["CO-1","CO-2","CO-3","CO-4","CO-5"] if c in df_mat.columns]
value_cols   = [c for c in est_cols if c in df_mat.columns]
df_mat["Total Estimate ($)"] = df_mat[value_cols].sum(axis=1)

if co_name_cols:
    df_mat["Change_Order_Tags"] = (
        df_mat[co_name_cols].astype(str)
        .agg(lambda x: ", ".join([v for v in x if v.strip() and v.lower()!="nan"]), axis=1)
        .replace("", "—")
    )
else:
    df_mat["Change_Order_Tags"] = "—"

# alias map
lookup_pairs = []
for _, r in df_mat.iterrows():
    parent = str(r["Project Name"]).strip()
    if not parent:
        continue
    lookup_pairs.append((normalize_text(parent), parent))
    for c in co_name_cols:
        val = str(r.get(c,"")).strip()
        if val and val.lower()!="nan":
            lookup_pairs.append((normalize_text(val), parent))

df_alias = pd.DataFrame(lookup_pairs, columns=["alias_key","Project Name"]).drop_duplicates()
alias_keys = set(df_alias["alias_key"])

# map timesheet → parent project
df["alias_key"] = df["Client full name"].apply(normalize_text)
df_map = df.merge(df_alias, on="alias_key", how="left")
df_map["Project Name"] = df_map["Project Name"].fillna(df_map["Client full name"])

# aggregate billables
agg = df_map.groupby(["Project Name","Employee"], as_index=False)["Billable Amount ($)"].sum()
pivot = (agg.pivot_table(index="Project Name", columns="Employee",
                         values="Billable Amount ($)", aggfunc="sum", fill_value=0)
         .reset_index())
pivot["Total Billable ($)"] = pivot.drop(columns=["Project Name"]).sum(axis=1)

# last activity
last_act = (df_map.groupby("Project Name", as_index=False)["Activity date"]
            .max().rename(columns={"Activity date":"Last Activity Date"}))

# merge metadata + pivot
meta_cols = ["Project Name","Change_Order_Tags","Total Estimate ($)"] + value_cols
for opt in [lead_col, team_col, terr_col, status_col]:
    if opt: meta_cols.append(opt)

meta = df_mat[meta_cols].drop_duplicates(subset=["Project Name"])

final = meta.merge(pivot, on="Project Name", how="left").merge(last_act, on="Project Name", how="left")
final = final.fillna(0)
final["Has Activity"] = final["Total Billable ($)"].gt(0)

# --- Interleave CO Name before each *_EST
rename_map = {c: f"{c} Name" for c in co_name_cols}
final = final.rename(columns=rename_map)

interleaved = []
for i in range(1,6):
    name_col=f"CO-{i} Name"; est_col=f"CO-{i} EST"
    if name_col in final.columns or est_col in final.columns:
        if name_col in final.columns: interleaved.append(name_col)
        if est_col in final.columns: interleaved.append(est_col)

# --- Column order (Total Estimate right after Total Billable)
ordered_cols = (
    ["Project Name"] +
    [c for c in final.columns if c not in ["Project Name"] + est_cols + interleaved +
     ["Change_Order_Tags", "Total Estimate ($)", "Last Activity Date", "Has Activity"]] +
    ["Project Estimate EST"] + interleaved +
    ["Total Billable ($)", "Total Estimate ($)", "Change_Order_Tags",
     "Last Activity Date", "Has Activity"]
)
ordered_cols = [c for c in ordered_cols if c in final.columns]
final = final[ordered_cols]

# Add combined CO names column
co_name_columns = [f"CO-{i} Name" for i in range(1,6) if f"CO-{i} Name" in final.columns]
if co_name_columns:
    final["All CO Names"] = (
        final[co_name_columns].astype(str)
        .agg(lambda x: ", ".join([v for v in x if v.strip() and v.lower() != "nan"]), axis=1)
        .replace("", "—")
    )
else:
    final["All CO Names"] = "—"

# deduplicate columns
final = final.loc[:, ~final.columns.duplicated()].copy()

# reorder Total Estimate
cols = list(final.columns)
if "Total Billable ($)" in cols and "Total Estimate ($)" in cols:
    tb_idx = cols.index("Total Billable ($)")
    cols.remove("Total Estimate ($)")
    cols.insert(tb_idx + 1, "Total Estimate ($)")
    final = final[cols]

# ----------------------------------------------------------
# STEP 3B — Non-Project / Unmapped Time Entries
# ----------------------------------------------------------
st.header("Step 3B — Non-Project / Unmapped Time Entries")

# true unmapped
unmapped_mask = ~df_map["alias_key"].isin(alias_keys)
unmapped = df_map.loc[unmapped_mask].copy()

cols_wanted = [
    "Employee",
    "Activity date",
    "Client full name",
    "Product/Service full name",
    "Description",
    "Duration (hrs)",
    "Rate ($/hr)",
    "Billable Amount ($)"
]
cols_present = [c for c in cols_wanted if c in unmapped.columns]
unmapped = unmapped[cols_present]

if not unmapped.empty:
    st.warning(f"⚠️ Found {len(unmapped)} time entries that do not belong to any project/CO in the matrix.")
    st.dataframe(unmapped.head(20), use_container_width=True)
else:
    st.success("✅ All time entries belong to known projects or COs!")

# ----------------------------------------------------------
# STEP 4 — DOWNLOAD SUMMARY
# ----------------------------------------------------------
st.header("Step 4 — Download Summary Excel")

out = "Final_Consolidated_Project_Summary.xlsx"
with pd.ExcelWriter(out, engine="openpyxl") as writer:
    final.to_excel(writer, sheet_name="Consolidated_Summary", index=False)
    if not unmapped.empty:
        unmapped.to_excel(writer, sheet_name="Unmapped_Time_Entries", index=False)

with open(out,"rb") as f:
    st.download_button("📥 Download Full Consolidated Summary (All Rows)", f, file_name=out)
