from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(page_title="소방서별 출동거리 증가율", page_icon="🚒", layout="wide")

SUMMARY_FILE = Path("소방서별_출동거리_증가율_2020_2021_내림차순.csv")
RAW_FILES = {
    2020: Path("구급출동_현황_2020.csv"),
    2021: Path("구급출동_현황_2021.csv"),
}


@st.cache_data(show_spinner=False)
def calculate_growth_from_raw() -> pd.DataFrame:
    """Calculate fire-station-level distance growth from the two source files."""
    annual_averages = []
    for year, file_path in RAW_FILES.items():
        data = pd.read_csv(
            file_path,
            encoding="utf-8-sig",
            skiprows=[1],  # The second source row contains English field names.
            usecols=["소방서명", "현장거리"],
            low_memory=False,
        )
        data["현장거리"] = pd.to_numeric(data["현장거리"], errors="coerce")
        data = data.dropna(subset=["소방서명", "현장거리"])
        data = data[data["현장거리"] >= 0]

        average = data.groupby("소방서명", as_index=False)["현장거리"].mean()
        annual_averages.append(
            average.rename(columns={"현장거리": f"{year}년_평균_현장거리"})
        )

    result = annual_averages[0].merge(annual_averages[1], on="소방서명", how="inner")
    result["출동거리_증가율"] = (
        (result["2021년_평균_현장거리"] - result["2020년_평균_현장거리"])
        / result["2020년_평균_현장거리"]
        * 100
    )
    return result


@st.cache_data(show_spinner=False)
def load_data() -> tuple[pd.DataFrame, str]:
    if SUMMARY_FILE.exists():
        frame = pd.read_csv(SUMMARY_FILE, encoding="utf-8-sig")
        source = f"집계 파일: {SUMMARY_FILE.name}"
    elif all(file_path.exists() for file_path in RAW_FILES.values()):
        frame = calculate_growth_from_raw()
        source = "원본 2020·2021 CSV에서 계산"
    else:
        missing = [str(path) for path in [SUMMARY_FILE, *RAW_FILES.values()] if not path.exists()]
        raise FileNotFoundError("다음 데이터 파일을 찾을 수 없습니다: " + ", ".join(missing))

    numeric_columns = ["2020년_평균_현장거리", "2021년_평균_현장거리", "출동거리_증가율"]
    for column in numeric_columns:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame.sort_values("출동거리_증가율", ascending=False), source


st.title("2020년 대비 2021년 출동거리 증가율")
st.caption("계산식: (2021년 평균 현장거리 − 2020년 평균 현장거리) / 2020년 평균 현장거리 × 100")

try:
    df, source_name = load_data()
except (FileNotFoundError, ValueError, KeyError) as error:
    st.error(f"데이터를 불러오지 못했습니다. {error}")
    st.stop()

st.caption(source_name)

top_five = df.head(5)
columns = st.columns(3)
columns[0].metric("대상 소방서", f"{len(df)}곳")
columns[1].metric("평균 증가율", f"{df['출동거리_증가율'].mean():.2f}%")
columns[2].metric("최대 증가율", f"{top_five.iloc[0]['출동거리_증가율']:.2f}%", top_five.iloc[0]["소방서명"])

chart_data = df.copy()
chart_data["색상 구분"] = "기타 소방서"
chart_data.loc[chart_data.index.isin(top_five.index), "색상 구분"] = "상위 5개 소방서"
chart_data.loc[chart_data["소방서명"] == "119특수구조단", "색상 구분"] = "119특수구조단"

fig = px.bar(
    chart_data.sort_values("출동거리_증가율"),
    x="출동거리_증가율",
    y="소방서명",
    orientation="h",
    color="색상 구분",
    color_discrete_map={
        "상위 5개 소방서": "#d62728",
        "기타 소방서": "#ff7f0e",
        "119특수구조단": "#1f77b4",
    },
    text=chart_data.sort_values("출동거리_증가율")["출동거리_증가율"].map("{:.2f}%".format),
    labels={"출동거리_증가율": "증가율 (%)", "소방서명": ""},
)
fig.update_traces(textposition="outside", cliponaxis=False)
fig.update_layout(
    height=780,
    legend_title_text="",
    margin=dict(l=10, r=80, t=25, b=10),
    yaxis=dict(categoryorder="total ascending"),
)
fig.add_vline(x=0, line_width=1, line_color="gray")
st.plotly_chart(fig, use_container_width=True)

display = df.copy()
display[["2020년_평균_현장거리", "2021년_평균_현장거리", "출동거리_증가율"]] = display[
    ["2020년_평균_현장거리", "2021년_평균_현장거리", "출동거리_증가율"]
].round(3)
st.dataframe(display, use_container_width=True, hide_index=True)

st.download_button(
    "정렬된 결과 CSV 다운로드",
    data=display.to_csv(index=False).encode("utf-8-sig"),
    file_name="소방서별_출동거리_증가율_2020_2021_내림차순.csv",
    mime="text/csv",
)
