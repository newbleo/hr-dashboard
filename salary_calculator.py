#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HR 연봉 계산기 – 인사담당자용 급여 관리 도구
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import csv
from datetime import datetime
from pathlib import Path

# ─────────────────────────────────────────────────────────────
# 상수
# ─────────────────────────────────────────────────────────────
DATA_FILE = Path.home() / ".hr_salary_calculator.json"

DEPT_LIST = ["개발", "디자인", "마케팅", "영업", "인사", "재무", "운영", "기타"]
RANK_LIST = ["인턴", "사원", "주임", "대리", "과장", "차장", "부장", "이사", "상무", "전무"]

BG      = "#F1F5F9"
WHITE   = "#FFFFFF"
PRI     = "#3B5BDB"
PRI_DK  = "#2F4AC7"
SUCCESS = "#0CA678"
DANGER  = "#E03131"
WARNING = "#F08C00"
TEXT    = "#212529"
SUBTEXT = "#6B7280"
BORDER  = "#DEE2E6"
HDR     = "#1A2E4A"
ACCENT  = "#EBF0FF"
ROW_ALT = "#F8FAFC"

DEPT_COLOR = {
    "개발":   "#3B5BDB", "디자인": "#AE3EC9", "마케팅": "#F08C00",
    "영업":   "#0CA678", "인사":   "#1C7ED6", "재무":   "#7048E8",
    "운영":   "#0C8599", "기타":   "#868E96",
}

# ─────────────────────────────────────────────────────────────
# 유틸
# ─────────────────────────────────────────────────────────────
def fmt(n: int) -> str:
    return f"{int(n):,}"


# ─────────────────────────────────────────────────────────────
# 급여 계산 엔진
# ─────────────────────────────────────────────────────────────
def _income_tax_annual(annual: float) -> float:
    """근로소득세 연간 계산 (2024년 기준, 본인 1인·비과세 없음)"""
    # 근로소득공제
    if annual <= 5_000_000:
        earned = annual * 0.70
    elif annual <= 15_000_000:
        earned = 3_500_000 + (annual - 5_000_000) * 0.40
    elif annual <= 45_000_000:
        earned = 7_500_000 + (annual - 15_000_000) * 0.15
    elif annual <= 100_000_000:
        earned = 12_000_000 + (annual - 45_000_000) * 0.05
    else:
        earned = 14_750_000 + (annual - 100_000_000) * 0.02
    earned = min(earned, 20_000_000)
    gross = annual - earned

    # 4대보험 공제액 (연간) – 과세표준 계산용
    m = annual / 12
    ins_yr = (
        round(min(m, 5_900_000) * 0.045)
        + round(m * 0.03545)
        + round(m * 0.004591)
        + round(m * 0.009)
    ) * 12

    taxable = max(0.0, gross - 1_500_000 - ins_yr)  # 인적공제 150만

    # 세율 (2024)
    tax = 0.0
    for lim, rate, prog in [
        (14_000_000,    0.06,  0),
        (50_000_000,    0.15,  1_260_000),
        (88_000_000,    0.24,  5_760_000),
        (150_000_000,   0.35,  15_440_000),
        (300_000_000,   0.38,  19_940_000),
        (500_000_000,   0.40,  25_940_000),
        (1_000_000_000, 0.42,  35_940_000),
        (float("inf"),  0.45,  65_940_000),
    ]:
        if taxable <= lim:
            tax = max(0.0, taxable * rate - prog)
            break

    # 근로소득세액공제
    credit = tax * 0.55 if tax <= 1_300_000 else 715_000 + (tax - 1_300_000) * 0.30
    if annual <= 33_000_000:
        lim_c = 740_000
    elif annual <= 70_000_000:
        lim_c = max(740_000 - (annual - 33_000_000) * 0.008, 660_000)
    else:
        lim_c = max(660_000 - (annual - 70_000_000) * 0.05, 500_000)

    return max(0.0, tax - min(credit, lim_c))


def calc_salary(annual: float) -> dict:
    m        = annual / 12
    pension  = round(min(m, 5_900_000) * 0.045)   # 국민연금 상한 590만
    health   = round(m * 0.03545)
    lcare    = round(m * 0.004591)
    employ   = round(m * 0.009)
    itax     = round(_income_tax_annual(annual) / 12)
    ltax     = round(itax * 0.1)
    ded      = pension + health + lcare + employ + itax + ltax
    return dict(
        annual=int(annual), monthly=round(m),
        pension=pension, health=health, lcare=lcare, employ=employ,
        income_tax=itax, local_tax=ltax,
        deductions=ded, net=round(m) - ded,
    )


# ─────────────────────────────────────────────────────────────
# 커스텀 위젯 헬퍼
# ─────────────────────────────────────────────────────────────
def make_btn(parent, text, cmd, bg=PRI, fg=WHITE, padx=18, pady=7):
    return tk.Button(
        parent, text=text, command=cmd,
        bg=bg, fg=fg, activebackground=PRI_DK, activeforeground=WHITE,
        font=("Helvetica", 12, "bold"),
        relief="flat", bd=0, cursor="hand2",
        padx=padx, pady=pady,
    )


def sep(parent, bg=BORDER, height=1, padx=0, pady=4):
    tk.Frame(parent, bg=bg, height=height).pack(fill="x", padx=padx, pady=pady)


def card(parent, **kw):
    f = tk.Frame(parent, bg=WHITE, relief="flat", bd=0, **kw)
    return f


# ─────────────────────────────────────────────────────────────
# 직원 추가 / 수정 다이얼로그
# ─────────────────────────────────────────────────────────────
class EmployeeDialog(tk.Toplevel):
    def __init__(self, parent, on_save, initial=None):
        super().__init__(parent)
        self.on_save = on_save
        self.initial = initial
        is_edit = initial is not None

        self.title("직원 수정" if is_edit else "직원 추가")
        self.resizable(False, False)
        self.configure(bg=WHITE)
        self.transient(parent)
        self.grab_set()

        self._build()

        w, h = 440, 460
        px = parent.winfo_x() + (parent.winfo_width()  - w) // 2
        py = parent.winfo_y() + (parent.winfo_height() - h) // 2
        self.geometry(f"{w}x{h}+{px}+{py}")

        if is_edit:
            self._fill(initial)
        else:
            self.vars["dept"].set(DEPT_LIST[0])
            self.vars["rank"].set(RANK_LIST[3])  # 기본: 대리

        self.wait_window()

    def _build(self):
        # 헤더
        hf = tk.Frame(self, bg=HDR)
        hf.pack(fill="x")
        tk.Label(hf, text=self.title(), bg=HDR, fg=WHITE,
                 font=("Helvetica", 15, "bold")).pack(padx=22, pady=16, anchor="w")

        body = tk.Frame(self, bg=WHITE)
        body.pack(fill="both", expand=True, padx=24, pady=4)

        self.vars: dict[str, tk.Variable] = {}

        def field(label, key, is_combo=False, opts=None):
            tk.Label(body, text=label, bg=WHITE, fg=TEXT,
                     font=("Helvetica", 11, "bold")).pack(anchor="w", pady=(10, 2))
            var = tk.StringVar()
            if is_combo:
                cb = ttk.Combobox(body, textvariable=var, values=opts,
                                  state="readonly", font=("Helvetica", 12))
                cb.pack(fill="x", ipady=5)
            else:
                e = tk.Entry(body, textvariable=var, font=("Helvetica", 12),
                             relief="solid", bd=1,
                             highlightthickness=1,
                             highlightbackground=BORDER,
                             highlightcolor=PRI)
                e.pack(fill="x", ipady=7)
                if key == "annual":
                    var.trace_add("write", self._on_annual_change)
            self.vars[key] = var

        field("이름",        "name")
        field("부서",        "dept",   True, DEPT_LIST)
        field("직급",        "rank",   True, RANK_LIST)
        field("연봉 (원)",   "annual")

        # 실시간 미리보기
        self.preview_var = tk.StringVar(value="")
        tk.Label(body, textvariable=self.preview_var, bg=WHITE, fg=PRI,
                 font=("Helvetica", 10), justify="left").pack(anchor="w", pady=(6, 0))

        # 버튼
        bf = tk.Frame(self, bg=WHITE)
        bf.pack(fill="x", padx=24, pady=14)
        make_btn(bf, "취소", self.destroy, bg="#E9ECEF", fg=TEXT).pack(side="right", padx=(6, 0))
        make_btn(bf, "저장", self._submit).pack(side="right")

    def _fill(self, emp: dict):
        self.vars["name"].set(emp["name"])
        self.vars["dept"].set(emp["dept"])
        self.vars["rank"].set(emp["rank"])
        self.vars["annual"].set(str(emp["annual"]))

    def _on_annual_change(self, *_):
        raw = self.vars["annual"].get().replace(",", "").strip()
        try:
            s = calc_salary(float(raw))
            self.preview_var.set(
                f"월급: {fmt(s['monthly'])}원   "
                f"공제합계: {fmt(s['deductions'])}원   "
                f"실수령액: {fmt(s['net'])}원"
            )
        except (ValueError, ZeroDivisionError):
            self.preview_var.set("")

    def _submit(self):
        name = self.vars["name"].get().strip()
        dept = self.vars["dept"].get()
        rank = self.vars["rank"].get()
        raw  = self.vars["annual"].get().replace(",", "").strip()

        if not name:
            messagebox.showwarning("입력 오류", "이름을 입력하세요.", parent=self)
            return
        try:
            annual = int(float(raw))
            if annual <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("입력 오류",
                "올바른 연봉을 입력하세요.\n예: 48000000", parent=self)
            return

        data = {"name": name, "dept": dept, "rank": rank, "annual": annual}
        if self.initial:
            data["id"] = self.initial["id"]

        self.on_save(data)
        self.destroy()


# ─────────────────────────────────────────────────────────────
# 메인 앱
# ─────────────────────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("HR 연봉 계산기")
        self.geometry("1280x780")
        self.minsize(960, 620)
        self.configure(bg=BG)

        self.employees: list[dict] = []
        self.next_id    = 1
        self.sel_id     = None
        self.last_saved = "없음"

        self._setup_style()
        self._build_ui()
        self._load_data()
        self._refresh_tree()
        self._refresh_summary()
        self._update_status()

    # ── 스타일 ───────────────────────────────────────────────
    def _setup_style(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure(".", background=BG, foreground=TEXT, font=("Helvetica", 12))
        s.configure("Treeview",
            background=WHITE, foreground=TEXT, fieldbackground=WHITE,
            rowheight=40, font=("Helvetica", 12))
        s.configure("Treeview.Heading",
            background="#E9ECEF", foreground=TEXT,
            font=("Helvetica", 12, "bold"), relief="flat")
        s.map("Treeview",
            background=[("selected", ACCENT)],
            foreground=[("selected", PRI)])
        s.configure("Vertical.TScrollbar",
            troughcolor=BG, background=BORDER, relief="flat", width=8)

    # ── UI 구성 ─────────────────────────────────────────────
    def _build_ui(self):
        self._build_header()
        self._build_toolbar()

        pw = tk.PanedWindow(self, orient="horizontal", bg="#CBD5E1",
                            sashwidth=4, sashrelief="flat", relief="flat")
        pw.pack(fill="both", expand=True)

        left  = self._build_left(pw)
        right = self._build_right(pw)
        pw.add(left,  minsize=520)
        pw.add(right, minsize=360)
        pw.paneconfigure(left,  stretch="always")
        pw.paneconfigure(right, stretch="never")

        self._build_statusbar()

    # ── 헤더 ─────────────────────────────────────────────────
    def _build_header(self):
        hf = tk.Frame(self, bg=HDR, height=62)
        hf.pack(fill="x")
        hf.pack_propagate(False)

        tk.Label(hf, text="HR 연봉 계산기", bg=HDR, fg=WHITE,
                 font=("Helvetica", 20, "bold")).pack(side="left", padx=24, pady=14)
        tk.Label(hf, text="인사담당자용 급여 관리 도구", bg=HDR, fg="#93C5FD",
                 font=("Helvetica", 12)).pack(side="left", padx=0, pady=14)
        tk.Label(hf, text=datetime.now().strftime("%Y년 %m월 %d일 (%a)"),
                 bg=HDR, fg="#94A3B8", font=("Helvetica", 11)).pack(side="right", padx=24)

    # ── 툴바 ─────────────────────────────────────────────────
    def _build_toolbar(self):
        tf = tk.Frame(self, bg=WHITE, height=56)
        tf.pack(fill="x")
        tf.pack_propagate(False)
        tk.Frame(tf, bg=BORDER, height=1).place(relwidth=1, rely=1.0, y=-1)

        left = tk.Frame(tf, bg=WHITE)
        left.pack(side="left", padx=18, pady=10)

        make_btn(left, "＋  직원 추가", self._cmd_add).pack(side="left", padx=3)
        self.btn_edit = make_btn(left, "✏  수정", self._cmd_edit,
                                 bg="#495057", fg=WHITE, padx=14)
        self.btn_edit.pack(side="left", padx=3)
        self.btn_del = make_btn(left, "🗑  삭제", self._cmd_delete,
                                bg=DANGER, fg=WHITE, padx=14)
        self.btn_del.pack(side="left", padx=3)

        right = tk.Frame(tf, bg=WHITE)
        right.pack(side="right", padx=18, pady=10)
        make_btn(right, "📊  CSV 내보내기", self._cmd_export_csv,
                 bg=SUCCESS, fg=WHITE, padx=14).pack(side="left", padx=3)

    # ── 왼쪽: 직원 목록 ──────────────────────────────────────
    def _build_left(self, parent):
        outer = tk.Frame(parent, bg=BG)

        cols = ("name", "dept", "rank", "annual", "monthly", "net")
        self.tree = ttk.Treeview(outer, columns=cols,
                                  show="headings", selectmode="browse")
        headers = [
            ("name",    "이름",     130, "w"),
            ("dept",    "부서",      80, "center"),
            ("rank",    "직급",      70, "center"),
            ("annual",  "연봉",     155, "e"),
            ("monthly", "월급",     140, "e"),
            ("net",     "실수령액", 145, "e"),
        ]
        for col, txt, w, anch in headers:
            self.tree.heading(col, text=txt, anchor="center")
            self.tree.column(col, width=w, anchor=anch, minwidth=60)

        self.tree.tag_configure("odd",  background=WHITE)
        self.tree.tag_configure("even", background=ROW_ALT)

        vsb = ttk.Scrollbar(outer, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)

        self.tree.pack(side="left", fill="both", expand=True, padx=(14, 0), pady=14)
        vsb.pack(side="left", fill="y", pady=14, padx=(0, 6))

        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        self.tree.bind("<Double-1>", lambda _: self._cmd_edit())

        return outer

    # ── 오른쪽: 상세 + 요약 ──────────────────────────────────
    def _build_right(self, parent):
        outer = tk.Frame(parent, bg=BG, width=400)

        # 스크롤 가능 영역
        canvas = tk.Canvas(outer, bg=BG, highlightthickness=0)
        vsb    = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)

        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(canvas, bg=BG)
        win_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        def _resize(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(win_id, width=e.width)

        inner.bind("<Configure>", _resize)

        # ── 급여 명세 카드 ──
        self._build_detail_card(inner)

        # ── 인건비 요약 카드 ──
        self._build_summary_card(inner)

        return outer

    def _section_title(self, parent, text):
        tk.Label(parent, text=text, bg=WHITE, fg=TEXT,
                 font=("Helvetica", 13, "bold")).pack(anchor="w", padx=18, pady=(14, 6))
        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=18, pady=(0, 4))

    # ── 급여 명세 카드 ────────────────────────────────────────
    def _build_detail_card(self, parent):
        c = card(parent)
        c.pack(fill="x", padx=12, pady=(14, 6))
        self._section_title(c, "💰  급여 명세")

        self.detail_lbl: dict[str, tk.Label] = {}

        # 안내 문구
        self.detail_hint = tk.Label(c,
            text="직원을 선택하면 급여 명세가 표시됩니다.",
            bg=WHITE, fg=SUBTEXT, font=("Helvetica", 12))
        self.detail_hint.pack(pady=20)

        # 명세 바디
        self.detail_body = tk.Frame(c, bg=WHITE)

        rows = [
            ("header",      None,                    TEXT,    True,   False),
            ("monthly",     "월급",                   TEXT,    True,   False),
            (None,          None,                    None,    None,   None),
            ("pension",     "국민연금  (4.5%)",       SUBTEXT, False,  True),
            ("health",      "건강보험  (3.545%)",     SUBTEXT, False,  True),
            ("lcare",       "장기요양  (0.4591%)",    SUBTEXT, False,  True),
            ("employ",      "고용보험  (0.9%)",       SUBTEXT, False,  True),
            ("income_tax",  "소득세",                 SUBTEXT, False,  True),
            ("local_tax",   "지방소득세  (소득세×10%)", SUBTEXT, False, True),
            (None,          None,                    None,    None,   None),
            ("net",         "✅  실수령액",            SUCCESS, True,   False),
        ]

        inner = tk.Frame(self.detail_body, bg=WHITE)
        inner.pack(fill="x", padx=18, pady=(4, 14))

        for key, label, color, bold, deduct in rows:
            if key is None:
                tk.Frame(inner, bg=BORDER, height=1).pack(fill="x", pady=5)
                continue
            row = tk.Frame(inner, bg=WHITE)
            row.pack(fill="x", pady=2)
            fw = "bold" if bold else "normal"
            if key == "header":
                lbl = tk.Label(row, text="", bg=WHITE, fg=color,
                               font=("Helvetica", 12, "bold"), anchor="w")
                lbl.pack(side="left", fill="x", expand=True)
            else:
                tk.Label(row, text=label, bg=WHITE, fg=color,
                         font=("Helvetica", 11, fw), anchor="w",
                         width=26).pack(side="left")
                lbl = tk.Label(row, text="–", bg=WHITE, fg=color,
                               font=("Helvetica", 11, fw), anchor="e")
                lbl.pack(side="right")
            self.detail_lbl[key] = lbl

    # ── 인건비 요약 카드 ─────────────────────────────────────
    def _build_summary_card(self, parent):
        c = card(parent)
        c.pack(fill="x", padx=12, pady=(0, 14))
        self._section_title(c, "📊  인건비 요약")

        self.kpi_lbl: dict[str, tk.Label] = {}

        # KPI 세 칸
        kpi_row = tk.Frame(c, bg=WHITE)
        kpi_row.pack(fill="x", padx=18, pady=(4, 10))
        for i, (key, label, color) in enumerate([
            ("total",  "총 인건비\n(연봉 합계)",  PRI),
            ("avg",    "평균 연봉",               WARNING),
            ("count",  "총 직원 수",              SUCCESS),
        ]):
            cell = tk.Frame(kpi_row, bg=ACCENT, bd=0)
            cell.grid(row=0, column=i, padx=4, sticky="nsew")
            kpi_row.columnconfigure(i, weight=1)
            tk.Label(cell, text=label, bg=ACCENT, fg=SUBTEXT,
                     font=("Helvetica", 10), justify="center").pack(pady=(10, 2))
            lbl = tk.Label(cell, text="–", bg=ACCENT, fg=color,
                           font=("Helvetica", 12, "bold"), justify="center")
            lbl.pack(pady=(0, 10))
            self.kpi_lbl[key] = lbl

        # 부서별
        tk.Frame(c, bg=BORDER, height=1).pack(fill="x", padx=18, pady=(2, 0))
        tk.Label(c, text="부서별 인건비", bg=WHITE, fg=TEXT,
                 font=("Helvetica", 11, "bold")).pack(anchor="w", padx=18, pady=(10, 4))

        self.dept_canvas = tk.Canvas(c, bg=WHITE, highlightthickness=0, height=10)
        self.dept_canvas.pack(fill="x", padx=18, pady=(0, 16))
        self.dept_canvas.bind("<Configure>", lambda _: self._draw_dept_bars())

    # ── 이벤트 ──────────────────────────────────────────────
    def _on_tree_select(self, _=None):
        sel = self.tree.selection()
        if not sel:
            self.sel_id = None
            self._hide_detail()
            return
        self.sel_id = int(sel[0])
        emp = self._find(self.sel_id)
        self._show_detail(emp)

    def _show_detail(self, emp: dict):
        self.detail_hint.pack_forget()
        self.detail_body.pack(fill="x")

        s = calc_salary(emp["annual"])
        self.detail_lbl["header"].config(
            text=f"{emp['name']}  ({emp['dept']} / {emp['rank']})   "
                 f"연봉 {fmt(emp['annual'])} 원")
        self.detail_lbl["monthly"].config(text=f"{fmt(s['monthly'])} 원")
        self.detail_lbl["pension"].config(text=f"- {fmt(s['pension'])} 원")
        self.detail_lbl["health"].config(text=f"- {fmt(s['health'])} 원")
        self.detail_lbl["lcare"].config(text=f"- {fmt(s['lcare'])} 원")
        self.detail_lbl["employ"].config(text=f"- {fmt(s['employ'])} 원")
        self.detail_lbl["income_tax"].config(text=f"- {fmt(s['income_tax'])} 원")
        self.detail_lbl["local_tax"].config(text=f"- {fmt(s['local_tax'])} 원")
        self.detail_lbl["net"].config(text=f"{fmt(s['net'])} 원")

    def _hide_detail(self):
        self.detail_body.pack_forget()
        self.detail_hint.pack(pady=20)

    # ── 요약 갱신 ────────────────────────────────────────────
    def _refresh_summary(self):
        if not self.employees:
            self.kpi_lbl["total"].config(text="0 원")
            self.kpi_lbl["avg"].config(text="0 원")
            self.kpi_lbl["count"].config(text="0 명")
            self._draw_dept_bars()
            return

        total = sum(e["annual"] for e in self.employees)
        avg   = total // len(self.employees)
        cnt   = len(self.employees)
        self.kpi_lbl["total"].config(text=f"{fmt(total)} 원")
        self.kpi_lbl["avg"].config(text=f"{fmt(avg)} 원")
        self.kpi_lbl["count"].config(text=f"{cnt} 명")
        self._draw_dept_bars()

    def _draw_dept_bars(self):
        cv = self.dept_canvas
        cv.delete("all")

        if not self.employees:
            return

        dept_totals: dict[str, int] = {}
        for e in self.employees:
            dept_totals[e["dept"]] = dept_totals.get(e["dept"], 0) + e["annual"]

        sorted_depts = sorted(dept_totals.items(), key=lambda x: -x[1])
        max_val = sorted_depts[0][1] if sorted_depts else 1

        BAR_H   = 18
        ROW_H   = 32
        LABEL_W = 54
        VAL_W   = 110
        PAD     = 6

        n = len(sorted_depts)
        cv.config(height=max(10, n * ROW_H + 4))
        cv.update_idletasks()
        W = cv.winfo_width()
        if W < 10:
            return

        bar_area = W - LABEL_W - VAL_W - PAD * 2

        for i, (dept, val) in enumerate(sorted_depts):
            y = i * ROW_H + (ROW_H - BAR_H) // 2

            # 레이블
            cv.create_text(0, y + BAR_H // 2, text=dept,
                           anchor="w", font=("Helvetica", 10),
                           fill=TEXT)

            # 배경 트랙
            bx = LABEL_W
            cv.create_rectangle(bx, y, bx + bar_area, y + BAR_H,
                                 fill="#E9ECEF", outline="")

            # 채움 막대
            bw = max(4, int(bar_area * val / max_val))
            color = DEPT_COLOR.get(dept, "#868E96")
            cv.create_rectangle(bx, y, bx + bw, y + BAR_H,
                                 fill=color, outline="")

            # 값
            cv.create_text(W, y + BAR_H // 2,
                           text=f"{fmt(val)} 원",
                           anchor="e", font=("Helvetica", 10),
                           fill=SUBTEXT)

    # ── 목록 갱신 ────────────────────────────────────────────
    def _refresh_tree(self):
        self.tree.delete(*self.tree.get_children())
        for i, emp in enumerate(self.employees):
            s   = calc_salary(emp["annual"])
            tag = "even" if i % 2 == 0 else "odd"
            self.tree.insert("", "end", iid=str(emp["id"]),
                values=(
                    emp["name"],
                    emp["dept"],
                    emp["rank"],
                    fmt(emp["annual"]) + " 원",
                    fmt(s["monthly"]) + " 원",
                    fmt(s["net"]) + " 원",
                ),
                tags=(tag,),
            )

    # ── 상태바 ───────────────────────────────────────────────
    def _build_statusbar(self):
        sb = tk.Frame(self, bg="#E2E8F0")
        sb.pack(fill="x", side="bottom")
        tk.Frame(sb, bg=BORDER, height=1).pack(fill="x", side="top")
        self._status_l = tk.Label(sb, text="", bg="#E2E8F0", fg=SUBTEXT,
                                  font=("Helvetica", 11), anchor="w")
        self._status_r = tk.Label(sb, text="", bg="#E2E8F0", fg=SUBTEXT,
                                  font=("Helvetica", 11), anchor="e")
        self._status_l.pack(side="left",  padx=16, pady=8)
        self._status_r.pack(side="right", padx=16, pady=8)

    def _update_status(self):
        self._status_l.config(text=f"마지막 저장: {self.last_saved}")
        self._status_r.config(text=f"직원 {len(self.employees)}명 등록됨")

    # ── CRUD 커맨드 ──────────────────────────────────────────
    def _cmd_add(self):
        EmployeeDialog(self, on_save=self._do_add)

    def _do_add(self, data: dict):
        data["id"] = self.next_id
        self.next_id += 1
        self.employees.append(data)
        self._refresh_tree()
        self._refresh_summary()
        self._save_data()

    def _cmd_edit(self):
        emp = self._require_selection("수정")
        if not emp:
            return
        EmployeeDialog(self, on_save=self._do_edit, initial=emp)

    def _do_edit(self, data: dict):
        for i, e in enumerate(self.employees):
            if e["id"] == data["id"]:
                self.employees[i] = data
                break
        self._refresh_tree()
        self._refresh_summary()
        self._show_detail(data)
        self._save_data()

    def _cmd_delete(self):
        emp = self._require_selection("삭제")
        if not emp:
            return
        if not messagebox.askyesno("삭제 확인",
                f"'{emp['name']}' 직원을 삭제하시겠습니까?", parent=self):
            return
        self.employees = [e for e in self.employees if e["id"] != self.sel_id]
        self.sel_id = None
        self._refresh_tree()
        self._hide_detail()
        self._refresh_summary()
        self._save_data()

    def _cmd_export_csv(self):
        if not self.employees:
            messagebox.showinfo("알림", "내보낼 데이터가 없습니다.", parent=self)
            return
        path = filedialog.asksaveasfilename(
            parent=self,
            defaultextension=".csv",
            filetypes=[("CSV 파일", "*.csv"), ("모든 파일", "*.*")],
            initialfile=f"급여명세_{datetime.now().strftime('%Y%m%d')}.csv",
        )
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow([
                "이름", "부서", "직급", "연봉", "월급",
                "국민연금", "건강보험", "장기요양", "고용보험",
                "소득세", "지방소득세", "공제합계", "실수령액",
            ])
            for emp in self.employees:
                s = calc_salary(emp["annual"])
                w.writerow([
                    emp["name"], emp["dept"], emp["rank"],
                    s["annual"], s["monthly"],
                    s["pension"], s["health"], s["lcare"], s["employ"],
                    s["income_tax"], s["local_tax"], s["deductions"], s["net"],
                ])
        messagebox.showinfo("완료", f"CSV 파일 저장 완료\n{path}", parent=self)

    # ── 데이터 저장 / 로드 ───────────────────────────────────
    def _save_data(self):
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(
                    {"employees": self.employees, "next_id": self.next_id},
                    f, ensure_ascii=False, indent=2,
                )
            self.last_saved = datetime.now().strftime("%Y-%m-%d %H:%M")
        except Exception as ex:
            messagebox.showerror("저장 오류", str(ex), parent=self)
        self._update_status()

    def _load_data(self):
        if not DATA_FILE.exists():
            return
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
            self.employees = d.get("employees", [])
            self.next_id   = d.get("next_id", 1)
            self.last_saved = "파일에서 로드됨"
        except Exception as ex:
            messagebox.showerror("로드 오류", str(ex), parent=self)

    # ── 유틸 ─────────────────────────────────────────────────
    def _find(self, eid: int):
        return next((e for e in self.employees if e["id"] == eid), None)

    def _require_selection(self, action: str):
        if self.sel_id is None:
            messagebox.showinfo("알림", f"{action}할 직원을 먼저 선택하세요.", parent=self)
            return None
        return self._find(self.sel_id)


# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = App()
    app.mainloop()
