#!/usr/bin/env python3
"""
ヴェネツィア総督選挙 — 戦略シミュレーションゲーム
1268年の選挙プロトコルに基づく (Mowbray & Gollmann, 2007)

あなたはヴェネツィアの野心的な貴族。買収と政治工作で自分の候補を
ドージェ（総督）に当選させよ。ただし金貨の無駄遣いは命取り——
くじ引きラウンドで買収した委員が落ちることもある。
"""

import random
import sys
from dataclasses import dataclass

# ── ヴェネツィア貴族の家名 ─────────────────────────────────

FAMILIES = [
    "コンタリーニ", "モロジーニ", "ダンドロ", "ファリエル", "グラデニーゴ",
    "ティエポロ", "ズィアーニ", "ミキエル", "バルバリーゴ", "グリマーニ",
    "ロレダン", "フォスカリ", "モチェニーゴ", "マリピエロ", "ヴェンドラミン",
    "トレヴィザン", "プリウリ", "ドナ", "グリッティ", "ヴェニエル",
    "コルネール", "ベンボ", "ピザーニ", "バドエル", "クエリーニ",
    "ゼン", "モーロ", "ステーノ", "チェルシ", "ドルフィン",
    "マルチェッロ", "ジュスティニアン", "ソランツォ", "ヴァリエル", "サグレード",
    "エリッツォ", "ディエド", "ロンゴ", "ブラガディン", "カッペッロ",
    "メンモ", "オルセオロ", "セルヴォ", "バゼッジョ",
]

# ── 1268年のプロトコル ─────────────────────────────────────
# 各ラウンド: (種別, 現委員会サイズ, 最低承認数, 次の委員会サイズ)
PROTOCOL = [
    ("lot",      480, None, 30),   # 第1回:  全員 → 30名
    ("lot",       30, None,  9),   # 第2回:   30 → 9名
    ("election",   9,    7, 40),   # 第3回:    9名が40名を選出
    ("lot",       40, None, 12),   # 第4回:   40 → 12名
    ("election",  12,    9, 25),   # 第5回:   12名が25名を選出
    ("lot",       25, None,  9),   # 第6回:   25 → 9名
    ("election",   9,    7, 45),   # 第7回:    9名が45名を選出
    ("lot",       45, None, 11),   # 第8回:   45 → 11名
    ("election",  11,    9, 41),   # 第9回:   11名が41名を選出
    ("election",  41,   25,  1),   # 第10回:  41名がドージェを選出
]


@dataclass
class Oligarch:
    id: int
    family: str
    loyalty: float  # -1.0 (敵対) … 0 (中立) … +1.0 (味方)
    bribe_resistance: int  # 買収に必要な金貨

    @property
    def label(self):
        if self.loyalty > 0.3:
            return "▶味方"
        elif self.loyalty < -0.3:
            return "◀敵"
        return " · "

    def vote_player_prob(self) -> float:
        return max(0.0, min(1.0, (self.loyalty + 1.0) / 2.0))


class DogeGame:
    def __init__(self, seed=None):
        if seed is not None:
            random.seed(seed)
        self.oligarchs: list[Oligarch] = []
        self.college: list[int] = []
        self.player_gold = 100
        self.rival_gold = 100
        self.player_candidate = ""
        self.rival_candidate = ""
        self._init_oligarchs()

    # ── 初期化 ────────────────────────────────────────────

    def _init_oligarchs(self):
        families = FAMILIES * (480 // len(FAMILIES) + 1)
        random.shuffle(families)
        for i in range(480):
            loyalty = random.gauss(0, 0.4)
            loyalty = max(-1.0, min(1.0, loyalty))
            resist = random.randint(4, 12)
            self.oligarchs.append(Oligarch(i, families[i], loyalty, resist))
        self.college = list(range(480))
        best_player = max(self.oligarchs, key=lambda o: o.loyalty)
        best_rival = min(self.oligarchs, key=lambda o: o.loyalty)
        self.player_candidate = best_player.family
        self.rival_candidate = best_rival.family

    # ── 表示 ──────────────────────────────────────────────

    def _count(self, ids: list[int]) -> tuple[int, int, int]:
        """(味方, 敵, 中立) の人数を返す"""
        y = sum(1 for i in ids if self.oligarchs[i].loyalty > 0.3)
        r = sum(1 for i in ids if self.oligarchs[i].loyalty < -0.3)
        return y, r, len(ids) - y - r

    def _bar(self, ids: list[int], width=40) -> str:
        y, r, n = self._count(ids)
        total = max(len(ids), 1)
        yw = round(width * y / total)
        rw = round(width * r / total)
        nw = width - yw - rw
        return f"[{'█' * yw}{'░' * nw}{'▓' * rw}]"

    def _show_status(self):
        y, r, n = self._count(self.college)
        print(f"  💰 金貨: 自軍 {self.player_gold:>3}  |  敵軍 {self.rival_gold:>3}")
        print(f"  📋 委員会 ({len(self.college)}名): 味方 {y} | 中立 {n} | 敵 {r}")
        print(f"     {self._bar(self.college)}")

    # ── くじ引きラウンド ──────────────────────────────────

    def _lot_round(self, next_size: int):
        if next_size >= len(self.college):
            return
        before_y, before_r, _ = self._count(self.college)
        self.college = random.sample(self.college, next_size)
        after_y, after_r, after_n = self._count(self.college)
        print(f"  🎲 くじ引き: {next_size}名を選出")
        print(f"     結果: 味方 {after_y} | 中立 {after_n} | 敵 {after_r}")
        delta = after_y / max(next_size, 1) - before_y / max(before_y + before_r + (len(self.college) if len(self.college) != next_size else 480), 1)
        if after_y > before_y * next_size / max(before_y + before_r + 480, 1) + 1:
            print(f"     → 運命の女神が微笑んだ！")
        elif after_y < max(0, before_y * next_size / 480 - 1):
            print(f"     → 不運……")

    # ── 買収フェーズ ──────────────────────────────────────

    def _bribe_phase(self, round_num: int):
        y, r, n = self._count(self.college)
        bribable_n = [(i, self.oligarchs[i]) for i in self.college
                      if -0.3 <= self.oligarchs[i].loyalty <= 0.3]
        bribable_r = [(i, self.oligarchs[i]) for i in self.college
                      if self.oligarchs[i].loyalty < -0.3]

        if self.player_gold <= 0 or (not bribable_n and not bribable_r):
            print("  （買収可能な委員がいません）")
            return

        avg_n_cost = (sum(o.bribe_resistance for _, o in bribable_n) // max(len(bribable_n), 1)) if bribable_n else 0
        avg_r_cost = (sum(o.bribe_resistance * 2 for _, o in bribable_r) // max(len(bribable_r), 1)) if bribable_r else 0

        print(f"\n  ── 買収フェーズ ──")
        print(f"  💰 所持金: {self.player_gold}")
        if bribable_n:
            print(f"  [N] 中立派を買収: {len(bribable_n)}名, 平均 ~{avg_n_cost}枚/人")
        if bribable_r:
            print(f"  [R] 敵派閥を買収: {len(bribable_r)}名, 平均 ~{avg_r_cost}枚/人")
        print(f"  [S] 見送る（金貨を温存）")

        while True:
            choice = input("  > ").strip().upper()
            if choice == "S" or choice == "":
                break
            elif choice == "N" and bribable_n:
                self._do_bribe(bribable_n, cost_mult=1)
                break
            elif choice == "R" and bribable_r:
                self._do_bribe(bribable_r, cost_mult=2)
                break
            else:
                print("  無効な選択です。")

    def _do_bribe(self, targets: list[tuple[int, "Oligarch"]], cost_mult: int):
        targets_sorted = sorted(targets, key=lambda t: t[1].bribe_resistance)
        max_affordable = 0
        running_cost = 0
        for _, o in targets_sorted:
            c = o.bribe_resistance * cost_mult
            if running_cost + c <= self.player_gold:
                max_affordable += 1
                running_cost += c
            else:
                break

        prompt = f"    何名を買収？ (1-{max_affordable}, 所持金: {self.player_gold}) > "
        raw = input(prompt).strip()
        try:
            count = max(0, min(int(raw), max_affordable))
        except ValueError:
            print("    キャンセルしました。")
            return

        if count == 0:
            return

        total_cost = 0
        bribed = 0
        for _, o in targets_sorted[:count]:
            cost = o.bribe_resistance * cost_mult
            o.loyalty = min(1.0, o.loyalty + 0.7)
            total_cost += cost
            bribed += 1

        self.player_gold -= total_cost
        print(f"    ✓ {bribed}名を買収（{total_cost}枚消費）")

    def _rival_bribe(self, round_num: int):
        """敵AI: ラウンドが進むほど積極的に買収する"""
        bribable = [(i, self.oligarchs[i]) for i in self.college
                    if self.oligarchs[i].loyalty >= -0.3]
        if not bribable or self.rival_gold <= 0:
            return

        aggression = 0.15 + 0.05 * round_num
        budget = int(self.rival_gold * aggression)
        budget = min(budget, self.rival_gold)

        neutrals = sorted(
            [(i, o) for i, o in bribable if -0.3 <= o.loyalty <= 0.3],
            key=lambda t: t[1].bribe_resistance,
        )

        spent = 0
        count = 0
        for _, o in neutrals:
            if spent + o.bribe_resistance > budget:
                break
            o.loyalty = max(-1.0, o.loyalty - 0.7)
            spent += o.bribe_resistance
            count += 1

        self.rival_gold -= spent
        if count > 0:
            print(f"  🕵  敵が{count}名を買収した……（{spent}枚消費）")

    # ── 選挙ラウンド ──────────────────────────────────────

    def _election_round(self, min_approvals: int, next_size: int) -> tuple[int, int] | None:
        """選挙を実施。最終ラウンドでは (味方票, 敵票) を返す"""
        player_votes = 0
        rival_votes = 0
        for idx in self.college:
            o = self.oligarchs[idx]
            if random.random() < o.vote_player_prob():
                player_votes += 1
            else:
                rival_votes += 1

        total = len(self.college)
        print(f"  🗳  投票結果: 味方 {player_votes} / 敵 {rival_votes}（全{total}票）")

        if next_size == 1:
            return player_votes, rival_votes

        player_ratio = player_votes / max(total, 1)

        if player_votes >= min_approvals:
            boost = min(1.3, 1.0 + (player_votes - min_approvals) / total)
            target_yours = int(next_size * player_ratio * boost)
            print(f"     → あなたの派閥が選挙を支配した！")
        elif rival_votes >= min_approvals:
            suppress = max(0.7, 1.0 - (rival_votes - min_approvals) / total)
            target_yours = int(next_size * player_ratio * suppress)
            print(f"     → 敵派閥が選挙を支配した！")
        else:
            target_yours = int(next_size * player_ratio)
            print(f"     → どちらの派閥も過半数に届かず。比例配分。")

        target_yours += random.randint(-1, 1)
        target_yours = max(0, min(next_size, target_yours))
        target_rival = next_size - target_yours

        pool_y = [i for i in range(480) if self.oligarchs[i].loyalty > 0.3]
        pool_r = [i for i in range(480) if self.oligarchs[i].loyalty < -0.3]
        pool_n = [i for i in range(480) if -0.3 <= self.oligarchs[i].loyalty <= 0.3]
        random.shuffle(pool_y)
        random.shuffle(pool_r)
        random.shuffle(pool_n)

        new_college = []
        new_college.extend(pool_y[:target_yours])
        remaining = target_rival
        new_college.extend(pool_r[:remaining])
        while len(new_college) < next_size:
            if pool_n:
                new_college.append(pool_n.pop())
            else:
                leftover = [i for i in range(480) if i not in new_college]
                if leftover:
                    new_college.append(random.choice(leftover))
                else:
                    break

        self.college = new_college[:next_size]
        ny, nr, nn = self._count(self.college)
        print(f"  📋 新委員会（{next_size}名）: 味方 {ny} | 中立 {nn} | 敵 {nr}")
        return None

    # ── 最終投票 ──────────────────────────────────────────

    def _final_vote(self, player_votes: int, rival_votes: int, min_approvals: int) -> bool | None:
        print()
        print("=" * 56)
        print("        ⚜  ドージェ最終選挙  ⚜")
        print("=" * 56)
        print(f"  あなたの候補:  {self.player_candidate}家")
        print(f"  敵の候補:      {self.rival_candidate}家")
        print()
        print(f"  当選に必要な承認: 41票中 {min_approvals}票")
        print(f"  ─────────────────────────────────")

        pc = self.player_candidate + "家"
        rc = self.rival_candidate + "家"
        print(f"  {pc:>16}: {'█' * player_votes} {player_votes}")
        print(f"  {rc:>16}: {'▓' * rival_votes} {rival_votes}")
        print(f"  {'当選ライン':>12}: {'·' * min_approvals} {min_approvals}")
        print()

        if player_votes >= min_approvals and player_votes > rival_votes:
            print(f"  🎉 勝利！ {self.player_candidate}家が新たなドージェに！")
            print(f"  サン・マルコの鐘がラグーナに鳴り響く！")
            return True
        elif rival_votes >= min_approvals and rival_votes >= player_votes:
            print(f"  💀 敗北。{self.rival_candidate}家がドージェの座を手にした。")
            print(f"  あなたの派閥はパラッツォへと退く……")
            return False
        else:
            print(f"  ⚖  膠着。どの候補も{min_approvals}票に届かなかった。")
            print(f"  選挙は振り出しに戻る。（引き分け）")
            return None

    # ── メインループ ──────────────────────────────────────

    def play(self):
        print()
        print("=" * 56)
        print("      ⚜  ヴェネツィア総督選挙  ⚜")
        print("          Anno Domini MCCLXVIII")
        print("=" * 56)
        print()
        print(f"  あなたの候補:  {self.player_candidate}家")
        print(f"  敵の候補:      {self.rival_candidate}家")
        print(f"  貴族: 480名  |  初期資金: {self.player_gold}枚")
        print()
        print("  くじ引きと選挙を交互に繰り返す全10ラウンド。")
        print("  金貨を使って味方を増やせ——ただし、")
        print("  くじ引きで買収した委員が落ちれば金の無駄になる。")
        print()
        input("  Enterキーで開始... ")

        for round_idx, (rtype, _, min_app, next_size) in enumerate(PROTOCOL):
            round_num = round_idx + 1
            is_final = (round_num == 10)

            print()
            print(f"─── 第{round_num}回 / 全10回 {'─' * 36}")
            if rtype == "lot":
                kind = "🎲 くじ引き"
            elif is_final:
                kind = "👑 ドージェ最終選挙"
            else:
                kind = "🗳  選挙"
            print(f"  {kind}")
            if rtype == "election":
                print(f"  （支配に必要な承認数: {min_app}）")
            self._show_status()

            if rtype == "lot":
                self._lot_round(next_size)
                input("\n  Enterで続行... ")
            else:
                self._bribe_phase(round_num)
                self._rival_bribe(round_num)
                result = self._election_round(min_app, next_size)

                if result is not None:
                    pv, rv = result
                    outcome = self._final_vote(pv, rv, min_app)
                    print()
                    print(f"  ── 最終結果 ──")
                    print(f"  残り金貨: 自軍 {self.player_gold}枚 | 敵軍 {self.rival_gold}枚")
                    if outcome is True:
                        bonus = self.player_gold * 10
                        print(f"  🏆 スコア: {1000 + bonus}（勝利 + 金貨ボーナス {bonus}）")
                    elif outcome is False:
                        print(f"  スコア: 0")
                    else:
                        print(f"  スコア: {self.player_gold * 5}（引き分け + 金貨ボーナス）")
                    return outcome

                input("\n  Enterで続行... ")

        return None


def main():
    print("\n  ⚜  ヴェネツィア総督選挙  ⚜")
    print("  買収と投票箱の戦略ゲーム")
    print("  原典: Mowbray & Gollmann (2007)")
    print("  ─────────────────────────────────────")

    while True:
        seed_input = input("\n  シード値（Enterでランダム）: ").strip()
        seed = int(seed_input) if seed_input.isdigit() else None
        game = DogeGame(seed=seed)
        game.play()

        if input("\n  もう一度遊ぶ？ (y/n) > ").strip().lower() != "y":
            print("\n  Arrivederci! 🇮🇹\n")
            break


if __name__ == "__main__":
    main()
