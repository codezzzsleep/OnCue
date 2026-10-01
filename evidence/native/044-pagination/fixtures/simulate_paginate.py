#!/usr/bin/env python3
"""离线自查：逐行复刻 oncue/bundle/main.splash 的 cue_paginate() 遍历逻辑，
验证两条硬性质（目标 3 / 目标 7）：

  A. 所有页按顺序拼接后 == 原始输入（逐字符相等，不缺失、不重复、不重序）
  B. 每页占用的视觉行数 <= 每页行数预算（因此正文不会被状态行/按钮遮挡）

本脚本只验证算法本身：它不是在跑 OctoScript，也不是宿主运行结果。
宿主就绪后仍需按 probe-plan.md 在真实 OctoScript 里复核（尤其
string.to_chars() / array.to_string() 的真实表现）。
"""
import os
import sys

PAGE_COLS = 11   # cue_page_cols：每条视觉行的显示列预算（窄视口 412 下安全）
PAGE_ROWS = 5    # cue_page_rows：阅读区（对白/摘要/A/B）每页视觉行数
MSG_ROWS = 4     # cue_msg_rows：原消息每页视觉行数


def cue_is_wide(cp):
    """与 main.splash 的 cue_is_wide 一致：东亚宽字与 emoji 记 2 列，其余 1 列。"""
    if cp >= 9472:                       # 0x2500 起：符号 / dingbats / CJK / 假名 / 全角
        return True
    if 126976 <= cp <= 129791:           # 0x1F300-0x1FAFF emoji
        return True
    return False


def wrapped_rows(seg, page_cols=PAGE_COLS):
    """段内按列数折行后的行数（空段也算 1 行）。"""
    rows, cols = 0, 0
    for ch in seg:
        cp = ord(ch)
        w = 2 if cue_is_wide(cp) else 1
        if cols + w > page_cols:
            rows += 1
            cols = 0
        cols += w
    return rows + 1


def cue_paginate(text, page_rows, page_cols=PAGE_COLS):
    """与 main.splash 的 cue_paginate 逐行对应（含换行符归属规则）。"""
    chars = list(text)                   # str.chars()
    total = len(chars)                   # array.len() 元素个数（不是字节数）
    pages = []
    if total == 0:
        return [""]
    page = []                            # "".to_chars() 起的 typed U32 页缓冲
    cols = 0
    rows = 1
    for c in chars:
        cp = ord(c)
        if cp == 10:                     # 源换行符：终止当前行并另起一行
            if rows >= page_rows:
                pages.append("".join(page))
                page = []
                rows = 1
                cols = 0
            page.append(c)
            cols = 0
            if rows >= page_rows:
                pages.append("".join(page))
                page = []
                rows = 1
                cols = 0
            else:
                rows += 1
        else:
            w = 2 if cue_is_wide(cp) else 1
            if cols + w > page_cols:     # 软折行
                if rows >= page_rows:
                    pages.append("".join(page))
                    page = []
                    rows = 1
                    cols = 0
                else:
                    rows += 1
                    cols = 0
            page.append(c)               # page.push(c)
            cols += w
    if len(page) > 0:
        pages.append("".join(page))
    return pages


def measure_rows(text, page_cols=PAGE_COLS):
    """渲染器视觉行数模型：按 "\n" 切段，段内折行，收尾空段也计一行。"""
    return sum(wrapped_rows(seg, page_cols) for seg in text.split("\n"))


def check(name, text, rows_budget):
    pages = cue_paginate(text, rows_budget)
    joined = "".join(pages)
    ok_roundtrip = joined == text
    per_page_rows = [measure_rows(p) for p in pages]
    ok_rows = all(r <= rows_budget for r in per_page_rows)
    ok_nonempty = bool(pages) and all(p != "" for p in pages[:-1])
    ok = ok_roundtrip and ok_rows and ok_nonempty
    print("[%s] 字符数=%d 字节数=%d 页数=%d 逐字符相等=%s 每页行数<= %d=%s(max=%d) 中间页非空=%s => %s"
          % (name, len(text), len(text.encode("utf-8")), len(pages),
             "PASS" if ok_roundtrip else "FAIL", rows_budget,
             "PASS" if ok_rows else "FAIL", max(per_page_rows),
             "PASS" if ok_nonempty else "FAIL", "PASS" if ok else "FAIL"))
    if not ok_roundtrip:
        for i, (a, b) in enumerate(zip(joined, text)):
            if a != b:
                print("    首个差异在第 %d 个字符: joined=%r text=%r" % (i, a, b))
                break
        print("    len(joined)=%d len(text)=%d" % (len(joined), len(text)))
    return ok


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    raw = {}
    for fn in sorted(os.listdir(here)):
        if fn.endswith(".txt"):
            raw[fn] = open(os.path.join(here, fn), encoding="utf-8").read()

    cases = [(fn, txt, MSG_ROWS) for fn, txt in raw.items()]
    # 真实应用路径上的组合文本：对白模式 = body + "\n" + draft
    cases.append(("组合: 多行 A/B 作为 body + 换行 + draft",
                  raw.get("04-multiline-ab.txt", "")
                  + "\n两天内回复都行，不必勉强；地点优先西湖周边，随时可改。", PAGE_ROWS))
    cases.append(("组合: 长对白 body + 换行 + 建议 draft",
                  raw.get("05-long-dialogue.txt", ""), PAGE_ROWS))
    cases.append(("组合: 场摘要 + 换行 + 说明",
                  raw.get("01-long-single-line-zh.txt", ""), PAGE_ROWS))

    allok = True
    for name, text, budget in cases:
        allok &= check(name, text, budget)
    print("总体：", "PASS" if allok else "FAIL")
    return 0 if allok else 1


if __name__ == "__main__":
    sys.exit(main())
