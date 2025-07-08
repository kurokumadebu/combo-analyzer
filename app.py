import streamlit as st
from simulator_core import load_warriors_from_csv, run_combo_simulation
import pandas as pd
import re
from collections import defaultdict

st.set_page_config(page_title="バリバリコンボ分析", layout="wide")
st.title("⚔️ バリバリコンボ分析")

# CSV에서 장수 목록 불러오기
warriors = load_warriors_from_csv("warriors.csv")
warrior_dict = {w.name: w for w in warriors}
warrior_by_nation = defaultdict(list)
for w in warriors:
    warrior_by_nation[w.nation].append(w)

# ✅ 장수 선택 UI
st.subheader("🧙 武将を選択してください（4人以上）")
selected_names = []
for nation in sorted(warrior_by_nation.keys()):
    st.markdown(f"**■ {nation}**")
    cols = st.columns(3)
    for idx, warrior in enumerate(warrior_by_nation[nation]):
        col = cols[idx % 3]
        if warrior.category == "名将":
            label = f"🔴 名将 {warrior.name}"
        else:
            label = warrior.name
        if col.checkbox(label, key=f"chk_{warrior.name}"):
            selected_names.append(warrior.name)

if len(selected_names) < 4:
    st.info("将軍を最低4人以上選んでください。")

st.markdown("---")

# ✅ 분석 버튼
if len(selected_names) >= 4:
    if st.button("🔍 探せ！"):
        selected_warriors = [warrior_dict[name] for name in selected_names]
        sim_data = run_combo_simulation(selected_warriors)
        st.session_state["top_teams"] = sim_data["top_teams"]
        st.session_state["top_4combo_teams"] = sim_data["top_4combo_teams"]
        st.session_state["detailed_index"] = None

# ✅ 팀 요약 출력
def render_team_summary(title, teams, key_prefix):
    st.subheader(f"📋 {title}")

    # ✅ 헤더 출력
    header_cols = st.columns([0.6, 2.5, 1.0, 0.9, 0.9, 0.9, 0.9, 1.4])
    header_cols[0].markdown("**No.**")
    header_cols[1].markdown("**編成**")
    header_cols[2].markdown("<div style='padding-left:1em;'>総発生数</div>", unsafe_allow_html=True)
    header_cols[3].markdown("<div style='padding-left:1em;'>コンボ 1</div>", unsafe_allow_html=True)
    header_cols[4].markdown("<div style='padding-left:1em;'>コンボ 2</div>", unsafe_allow_html=True)
    header_cols[5].markdown("<div style='padding-left:1em;'>コンボ 3</div>", unsafe_allow_html=True)
    header_cols[6].markdown("<div style='padding-left:1em;'>コンボ 4</div>", unsafe_allow_html=True)
    header_cols[7].markdown("<div style='padding-left:1em;'>照会</div>", unsafe_allow_html=True)

    for team in teams:
        team_no = team["team_no"]
        team_names = team["team_names"]
        combo_counts = [r["전체 기술 시퀀스"].count("콤보(") for r in team["results"]]
        case_count = len(combo_counts)

        row_cols = st.columns([0.6, 2.5, 1.0, 0.9, 0.9, 0.9, 0.9, 1.4])
        row_cols[0].markdown(f"**{team_no}**")
        row_cols[1].markdown(" + ".join(team_names))
        row_cols[2].markdown(f"<div style='padding-left:1em;'>{case_count}</div>", unsafe_allow_html=True)
        row_cols[3].markdown(f"<div style='padding-left:1em;'>{combo_counts.count(1)}</div>", unsafe_allow_html=True)
        row_cols[4].markdown(f"<div style='padding-left:1em;'>{combo_counts.count(2)}</div>", unsafe_allow_html=True)
        row_cols[5].markdown(f"<div style='padding-left:1em;'>{combo_counts.count(3)}</div>", unsafe_allow_html=True)
        row_cols[6].markdown(f"<div style='padding-left:1em;'>{combo_counts.count(4)}</div>", unsafe_allow_html=True)

        with row_cols[7]:
            if st.button("詳細内容", key=f"{key_prefix}_detail_btn_{team_no}"):
                st.session_state["detailed_index"] = team_no

        st.markdown("<hr style='margin:4px 0;'>", unsafe_allow_html=True)  # 각 행 구분선

# 🔹 출력: 추천 상위 15개 팀
if "top_teams" in st.session_state:
    render_team_summary("おすすめ上位15組", st.session_state["top_teams"], "top")

# 🔹 출력: 콤보4 상위 5개 팀
if "top_4combo_teams" in st.session_state:
    render_team_summary("連続コンボが多い上位５組", st.session_state["top_4combo_teams"], "combo4")

# ✅ 상세 콤보 시퀀스 출력
if st.session_state.get("detailed_index") is not None:
    all_teams = st.session_state["top_teams"] + st.session_state["top_4combo_teams"]
    selected_team = next((t for t in all_teams if t["team_no"] == st.session_state["detailed_index"]), None)
    if selected_team:
        st.markdown("---")
        styled_names = " ".join([
            f"<span style='background-color:#eee;color:black;padding:2px 8px;border-radius:4px;margin-right:4px;'>"
            f"{'<span style=\"background-color:#d33;color:white;padding:1px 4px;border-radius:2px;margin-right:4px;font-size:10px\">名将</span> ' if warrior_dict[name].category == '名将' else ''}{name}</span>"
            for name in selected_team["team_names"]
        ])
        st.markdown(f"📋 {selected_team['team_no']} コンボ構成: {styled_names}", unsafe_allow_html=True)

        # 테이블 데이터 구성
        table_data = []
        for row in selected_team["results"]:
            sequence = row["전체 기술 시퀀스"]
            parts = sequence.split(" → ")

            def format_step(step):
                match = re.match(r"(.+?) (기술1|기술2|콤보)\((.*?)\)", step)
                if match:
                    name, skill_type, effect = match.group(1), match.group(2), match.group(3)
                    prefix = ""
                    if skill_type == "기술1":
                        prefix = "怒り: "
                    elif skill_type == "기술2":
                        prefix = "普通: "
                    if effect.strip() == "":
                        return f"{name}\n({prefix}状態変更なし)"
                    else:
                        return f"{name}\n({prefix}{effect})"
                return step

            발동 = format_step(parts[0]) if parts else ""
            콤보 = [format_step(p) for p in parts[1:]] if len(parts) > 1 else []
            row_data = [발동]
            row_data.extend(콤보 + [""] * (4 - len(콤보)))
            table_data.append(row_data)

        df = pd.DataFrame(table_data, columns=["攻撃技", "コンボ 1", "コンボ 2", "コンボ 3", "コンボ 4"])
        df.index = range(1, len(df) + 1)
        st.dataframe(
            df.style.set_properties(
                subset=["攻撃技", "コンボ 1", "コンボ 2", "コンボ 3", "コンボ 4"],
                **{"white-space": "pre-wrap"}
            ).set_table_styles([
                {"selector": "th, td", "props": [("border", "1px solid #ccc"), ("padding", "6px")]},
                {"selector": "th", "props": [("background-color", "#f0f0f0")]}
            ]),
            use_container_width=True
        )
