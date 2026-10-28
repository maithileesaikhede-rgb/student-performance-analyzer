import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Student Performance Analyzer",
    page_icon="📊",
    layout="wide"
)

SUBJECTS = ["Math", "Science", "English", "Computer"]
REQUIRED_COLUMNS = ["Name"] + SUBJECTS
PASS_MARKS = 40

st.title("📊 Student Performance Analyzer")
st.write(
    "Analyze student marks, grades and subject-wise performance."
)


def prepare_data(df):
    # Check required columns
    missing = [
        col for col in REQUIRED_COLUMNS
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            "Missing columns: " + ", ".join(missing)
        )

    df = df[REQUIRED_COLUMNS].copy()

    # Clean student names
    df["Name"] = df["Name"].astype("string").str.strip()

    if df["Name"].isna().any() or df["Name"].eq("").any():
        raise ValueError("Every student must have a name.")

    if df["Name"].duplicated().any():
        raise ValueError("Student names must be unique.")

    # Convert marks to numeric values
    for subject in SUBJECTS:
        df[subject] = pd.to_numeric(
            df[subject], errors="raise"
        )

    # Validate marks
    if df[SUBJECTS].isna().any().any():
        raise ValueError("Marks cannot be empty.")

    if not df[SUBJECTS].isin(
        range(101)
    ).all().all():
        raise ValueError(
            "All marks must be whole numbers from 0 to 100."
        )

    if not df[SUBJECTS].apply(
        lambda col: col.mod(1).eq(0)
    ).all().all():
        raise ValueError("Marks must be whole numbers.")

    # Calculate total, average and grade
    df["Total"] = df[SUBJECTS].sum(axis=1)
    df["Average"] = df[SUBJECTS].mean(axis=1).round(2)

    def calculate_grade(avg):
        if avg >= 90:
            return "A+"
        elif avg >= 80:
            return "A"
        elif avg >= 70:
            return "B"
        elif avg >= 60:
            return "C"
        elif avg >= 40:
            return "D"
        return "F"

    df["Grade"] = df["Average"].apply(calculate_grade)

    # Student passes only if every subject is >= 40
    df["Result"] = df[SUBJECTS].ge(
        PASS_MARKS
    ).all(axis=1).map({
        True: "Pass",
        False: "Fail"
    })

    return df


# Upload a CSV or use the included sample data
uploaded_file = st.file_uploader(
    "Upload student CSV file",
    type=["csv"]
)

try:
    if uploaded_file is not None:
        raw_data = pd.read_csv(uploaded_file)
    else:
        raw_data = pd.read_csv("students.csv")

    data = prepare_data(raw_data)

except Exception as error:
    st.error(f"Could not process the dataset: {error}")
    st.stop()


# Dashboard summary
total_students = len(data)
class_average = round(data["Average"].mean(), 2)
top_student = data.loc[data["Average"].idxmax()]
pass_rate = round(
    data["Result"].eq("Pass").mean() * 100, 2
)

c1, c2, c3, c4 = st.columns(4)

c1.metric("Total Students", total_students)
c2.metric("Class Average", class_average)
c3.metric("Pass Rate", f"{pass_rate}%")
c4.metric("Top Performer", top_student["Name"])

st.divider()

# Student results table
st.subheader("Student Results")

st.dataframe(
    data.sort_values("Average", ascending=False),
    use_container_width=True,
    hide_index=True
)

# Subject-wise average
st.subheader("Subject-wise Average Marks")

subject_averages = (
    data[SUBJECTS].mean()
    .rename_axis("Subject")
    .reset_index(name="Average Marks")
)

fig1 = px.bar(
    subject_averages,
    x="Subject",
    y="Average Marks",
    title="Average Marks by Subject",
    text_auto=".1f"
)
fig1.update_yaxes(range=[0, 100])
st.plotly_chart(fig1, use_container_width=True)

# Compare students
st.subheader("Student Performance Comparison")

fig2 = px.bar(
    data,
    x="Name",
    y="Average",
    color="Result",
    hover_data=["Total", "Grade"],
    title="Average Marks per Student"
)
fig2.update_yaxes(range=[0, 100])
st.plotly_chart(fig2, use_container_width=True)

# Grade distribution
st.subheader("Grade Distribution")

grade_counts = (
    data["Grade"].value_counts()
    .reindex(["A+", "A", "B", "C", "D", "F"], fill_value=0)
    .rename_axis("Grade")
    .reset_index(name="Students")
)

fig3 = px.pie(
    grade_counts,
    names="Grade",
    values="Students",
    title="Students by Grade",
    hole=0.35
)
st.plotly_chart(fig3, use_container_width=True)

# Download analyzed results
csv_data = data.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download Analyzed Results",
    data=csv_data,
    file_name="student_analysis_results.csv",
    mime="text/csv"
)

st.caption(
    "Grade rules and pass marks are illustrative and can be "
    "changed to match your institution's policy."
)