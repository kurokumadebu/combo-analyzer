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

# 명장 우선, 국가 순 정렬
def sort_warriors(wlist):
    return sorted(wlist, key=lambda w: ("01" if w.category == "名将" else "02", w.name))

sorted_warriors = defaultdict(list)
for w in warriors:
    sorted_warriors[w.nation].append(w)
for nation in sorted_warriors:
    sorted_warriors[nation] = sort_warriors(sorted_warriors[nation])

# 1단계: 고정 장수 선택
st.subheader("Step 1. 固定武将の選択(オプション)")
st.markdown("""
特定の武将を固定したい場合は、最大3人まで指定可能です。
指定しない場合は、全ての組み合わせを対象に分析します。
""") # 문구 수정

def format_label(w):
    label = f"名将 {w.name}" if w.category == "名将" else w.name
    return label

all_sorted = []
for nation in ["蜀", "魏", "呉", "群", "野"]:
    all_sorted.extend(sorted_warriors[nation])

label_options = [format_label(w) for w in all_sorted]
name_options = [w.name for w in all_sorted]

col1, col2, col3 = st.columns(3)
fixed1 = col1.selectbox("固定武将1", [""] + name_options, format_func=lambda n: "" if n == "" else format_label(warrior_dict[n]))
fixed2 = col2.selectbox("固定武将2", [""] + name_options, format_func=lambda n: "" if n == "" else format_label(warrior_dict[n]))
fixed3 = col3.selectbox("固定武将3", [""] + name_options, format_func=lambda n: "" if n == "" else format_label(warrior_dict[n]))

fixed_selected = [n for n in [fixed1, fixed2, fixed3] if n]

if st.button("次へ"):
    if len(set(fixed_selected)) != len(fixed_selected):
        st.error("⚠️ 同じ武将を複数固定できません。")
    else:
        st.session_state["fixed_members"] = fixed_selected
        st.session_state["go_next"] = True
        # Step2 선택 초기화 및 상세 표시 초기화
        st.session_state["selected_members_step2"] = []
        st.session_state["top_teams"] = []
        st.session_state["top_4combo_teams"] = []
        st.session_state["detailed_index"] = None

# 2단계: 나머지 장수 선택
if st.session_state.get("go_next"):
    st.subheader("Step 2. 武将の選択")
    st.markdown("武装は固定武装を含め、最低4人以上を指定してください。")

    selected_names = st.session_state.get("selected_members_step2", [])

    for nation in ["蜀", "魏", "呉", "群", "野"]:
        st.markdown(f"**■ {nation}**")
        cols = st.columns(3)
        for idx, warrior in enumerate(sorted_warriors[nation]):
            col = cols[idx % 3]
            disabled = warrior.name in st.session_state["fixed_members"]
            label = f"{'名将 ' if warrior.category == '名将' else ''}{warrior.name}"
            if disabled:
                col.checkbox(label + " (固定)", key=f"chk_{warrior.name}", value=True, disabled=True)
            else:
                checked = warrior.name in selected_names
                val = col.checkbox(label, key=f"chk_{warrior.name}", value=checked)
                # 선택값 업데이트 (실시간 반영)
                if val and warrior.name not in selected_names:
                    selected_names.append(warrior.name)
                elif not val and warrior.name in selected_names:
                    selected_names.remove(warrior.name)

    # 선택 상태를 세션에 저장
    st.session_state["selected_members_step2"] = selected_names

    total_selected = len(selected_names) + len(st.session_state["fixed_members"])
    if total_selected < 4:
        st.info("将軍を最低4人以上選んでください。")
    else:
        st.subheader("Step 3. 合体技の指定")
        same_nation_option = st.checkbox("🧩 **三同一任 編成**", value=False) # 체크박스 명칭 수정

        # 같은 국가 3명 이상 검사 (고정 + 선택 합산)
        if same_nation_option:
            nation_counts = defaultdict(int)
            for n in st.session_state["fixed_members"] + selected_names:
                nation = warrior_dict[n].nation
                nation_counts[nation] += 1
            if all(count < 3 for count in nation_counts.values()):
                st.error("⚠️ 同一国家の武将が3人以上必要です。")
            else:
                if st.button("🔍 探せ！"):
                    all_selected = st.session_state["fixed_members"] + selected_names
                    selected_warriors = [warrior_dict[n] for n in all_selected]
                    sim_data = run_combo_simulation(selected_warriors, same_nation_option=same_nation_option, fixed_members=st.session_state["fixed_members"])
                    st.session_state["top_teams"] = sim_data["top_teams"]
                    st.session_state["top_4combo_teams"] = sim_data["top_4combo_teams"]
                    st.session_state["detailed_index"] = None
        else:
            if st.button("🔍 探せ！"):
                all_selected = st.session_state["fixed_members"] + selected_names
                selected_warriors = [warrior_dict[n] for n in all_selected]
                sim_data = run_combo_simulation(selected_warriors, same_nation_option=same_nation_option, fixed_members=st.session_state["fixed_members"])
                st.session_state["top_teams"] = sim_data["top_teams"]
                st.session_state["top_4combo_teams"] = sim_data["top_4combo_teams"]
                st.session_state["detailed_index"] = None

# 팀 요약 출력 함수
def render_team_summary(title, teams, key_prefix):
    st.subheader(f"📋 {title}")
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

        st.markdown("<hr style='margin:4px 0;'>", unsafe_allow_html=True)

if "top_teams" in st.session_state and st.session_state["top_teams"]:
    render_team_summary("おすすめ上位15組", st.session_state["top_teams"], "top")

if "top_4combo_teams" in st.session_state and st.session_state["top_4combo_teams"]:
    render_team_summary("連続コンボが多い上位５組", st.session_state["top_4combo_teams"], "combo4")

# 상세 콤보 시퀀스
if st.session_state.get("detailed_index") is not None:
    all_teams = st.session_state.get("top_teams", []) + st.session_state.get("top_4combo_teams", [])
    selected_team = next((t for t in all_teams if t["team_no"] == st.session_state["detailed_index"]), None)
    if selected_team:
        st.markdown("---")
        styled_names = " ".join([
            (
                "<span style='background-color:#eee;color:black;padding:2px 8px;border-radius:4px;margin-right:4px;'>"
                "<span style='background-color:#d33;color:white;padding:1px 4px;border-radius:2px;margin-right:4px;font-size:10px'>名将</span> "
                f"{name}</span>"
                if warrior_dict[name].category == "名将" else
                f"<span style='background-color:#eee;color:black;padding:2px 8px;border-radius:4px;margin-right:4px;'>{name}</span>"
            )
            for name in selected_team["team_names"]
        ])
        st.markdown(f"📋 {selected_team['team_no']} コンボ構成: {styled_names}", unsafe_allow_html=True)

        table_data = []
        for row in selected_team["results"]:
            sequence = row["전체 기술 시퀀스"]
            parts = sequence.split(" → ")

            def format_step(step):
                match = re.match(r"(.+?) (기술1|기술2|콤보)\((.*?)\)", step)
                if match:
                    name, skill_type, effect = match.group(1), match.group(2), match.group(3)
                    prefix = "怒り: " if skill_type == "기술1" else "普通: " if skill_type == "技術2" else ""
                    return f"{name}\n({prefix}{effect if effect else '状態変更なし'})"
                return step

            발동 = format_step(parts[0]) if parts else ""
            콤보 = [format_step(p) for p in parts[1:]] if len(parts) > 1 else []
            row_data = [발동] + 콤보 + [""] * (4 - len(콤보))
            table_data.append(row_data)

        df = pd.DataFrame(table_data, columns=["攻撃技", "コンボ 1", "コンボ 2", "コンボ 3", "コンボ 4"])
        df.index = range(1, len(df) + 1)
        st.dataframe(
            df.style.set_properties(
                subset=["攻撃技", "コンボ 1", "コンボ 2", "コンボ 3", "コンボ 4"],
                **{"white-space": "pre-wrap"}
            ).set_table_styles([
                {"selector": "th, td", "props": [("border", "1px solid #ccc"), ("padding", "6px")]},
                {"selector": "th", "props": [("background-color", "#f0f0f0")]},
            ]),
            use_container_width=True
        )