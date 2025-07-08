from typing import List
from itertools import combinations
import csv

class Warrior:
    def __init__(self, nation: str, name: str, category: str, skill1: str, skill2: str, trigger: str, combo: str):
        self.nation = nation
        self.name = name
        self.category = category  # "名将" 또는 ""
        self.skills = {"기술1": skill1, "기술2": skill2}
        self.trigger = trigger
        self.combo = combo

class ComboSimulator:
    def __init__(self, warriors: List[Warrior]):
        self.warriors = warriors
        self.results = []
        self.case_no = 1

    def simulate_all(self):
        self.results.clear()
        self.case_no = 1
        for warrior in self.warriors:
            for skill_type in ["기술1", "기술2"]:
                skill_used = warrior.skills[skill_type]
                if not skill_used.strip():
                    continue
                self.simulate(warrior, skill_used, skill_type)

    def simulate(self, starter: Warrior, skill_used: str, skill_type: str):
        used_skill = {starter.name}
        used_combo = set()
        base_seq = [f"{starter.name} {skill_type}({skill_used})"]
        state = skill_used

        def recurse(state, used_skill, used_combo, seq):
            if len(seq) - 1 >= 4:
                if any("콤보(" in s for s in seq[1:]):
                    self.results.append({
                        "CaseNo": str(self.case_no),
                        "전체 기술 시퀀스": " → ".join(seq)
                    })
                    self.case_no += 1
                return

            triggered = False
            for w in self.warriors:
                if w.name in used_combo:
                    continue
                if w.trigger == state and w.combo.strip() and w.combo != "상태변환없음" and w.combo != "終了":
                    new_seq = seq + [f"{w.name} 콤보({w.combo})"]
                    triggered = True
                    recurse(w.combo, used_skill, used_combo | {w.name}, new_seq)

            if not triggered:
                if any("콤보(" in s for s in seq[1:]):
                    self.results.append({
                        "CaseNo": str(self.case_no),
                        "전체 기술 시퀀스": " → ".join(seq)
                    })
                    self.case_no += 1

        # 직접 발동
        if starter.trigger == state and starter.combo.strip() and starter.combo not in ["상태변환없음", "終了"]:
            own_seq = base_seq + [f"{starter.name} 콤보({starter.combo})"]
            recurse(starter.combo, used_skill, {starter.name}, own_seq)

        # 타인 발동
        for w in self.warriors:
            if w.name == starter.name or w.name in used_combo:
                continue
            if w.trigger == state and w.combo.strip() and w.combo not in ["상태변환없음", "終了"]:
                alt_seq = base_seq + [f"{w.name} 콤보({w.combo})"]
                recurse(w.combo, used_skill, {w.name}, alt_seq)

        # 콤보 없음
        if not any(w.trigger == state and w.combo.strip() and w.combo not in ["상태변환없음", "終了"] for w in self.warriors):
            # 콤보 없이 기술만 사용된 경우는 제외 (출력 안 함)
            pass

    def get_results(self):
        return self.results

def load_warriors_from_csv(filepath: str) -> List[Warrior]:
    warriors = []
    with open(filepath, "r", encoding="utf-8") as file:
        for line in file:
            parts = line.strip().split(",")
            if len(parts) == 7:
                nation, name, category, skill1, skill2, trigger, combo = parts
                warriors.append(Warrior(
                    nation.strip(),
                    name.strip(),
                    category.strip(),
                    skill1.strip(),
                    skill2.strip(),
                    trigger.strip(),
                    combo.strip()
                ))
    return warriors

def run_combo_simulation(warriors: List[Warrior]):
    """선택된 장수들로 가능한 4인 팀 조합을 모두 시뮬레이션"""
    all_results = []
    combis = list(combinations(warriors, 4))
    for idx, team in enumerate(combis, 1):
        sim = ComboSimulator(list(team))
        sim.simulate_all()
        results = sim.get_results()
        if results:
            combo_counts = [r["전체 기술 시퀀스"].count("콤보(") for r in results]
            all_results.append({
                "team_no": idx,
                "team_names": [w.name for w in team],
                "results": results,
                "case_count": len(combo_counts),
                "combo0": combo_counts.count(0),
                "combo1": combo_counts.count(1),
                "combo2": combo_counts.count(2),
                "combo3": combo_counts.count(3),
                "combo4": combo_counts.count(4)
            })

    # 총 발생수 → 콤보4 → 콤보3 기준 정렬하여 상위 15개
    top_teams = sorted(
        all_results,
        key=lambda x: (x["case_count"], x["combo4"], x["combo3"]),
        reverse=True
    )[:15]

    # 콤보4 수 기준 상위 5개
    top_4combo_teams = sorted(
        all_results,
        key=lambda x: (x["combo4"], x["case_count"], x["combo3"]),
        reverse=True
    )[:5]

    return {
        "top_teams": top_teams,
        "top_4combo_teams": top_4combo_teams
    }
