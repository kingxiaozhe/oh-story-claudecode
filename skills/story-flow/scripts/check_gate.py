#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_gate.py — story-flow 确定性门禁：字数预算 / 对话占比 / 超长段落。

只用标准库。输出人读摘要 + （--json 时）机读 JSON，含精确修复预算。
风格指纹检查不在本脚本：由 story-deslop check-ai-patterns.js --fail-on=blocking 承担。

用法：
  python3 check_gate.py 正文/C-0001.md --min-chars 1900 --max-chars 2500
  python3 check_gate.py 正文/C-0001.md --min-chars 1900 --max-chars 2500 \
      --dialog-min 25 --dialog-max 60 --json

判定规则（见 references/gate-policy.md）：
  - 字数带 ±tolerance-pct（默认 2%）容差；容差内 pass 但标注 tolerance
  - 对话占比带 ±dialog-tolerance-pt（默认 3 个百分点）容差
  - 超长段落为 advisory，不影响退出码
  - 未通过时给出精确修复预算（need_chars / need_dialog_chars）
退出码：硬性项（字数/对话占比，容差后）全过 0，否则 1。
"""
import argparse
import json
import math
import re
import sys

CN_RE = re.compile(r"[一-鿿]")
# 对话：中英双引号与直角引号内的内容
DIALOG_RE = re.compile(r"[\"“「『]([^\"”」』]*)[\"”」』]")


def strip_markdown(text):
    out = []
    in_fence = False
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or s.startswith("#") or s.startswith(">"):
            continue
        out.append(line)
    return "\n".join(out)


def cn_count(text):
    return len(CN_RE.findall(text))


def analyze(path):
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    body = strip_markdown(raw)
    total = cn_count(body)
    dialog = sum(cn_count(m) for m in DIALOG_RE.findall(body))
    paras = [p for p in re.split(r"\n\s*\n", body) if p.strip()]
    long_paras = []
    for i, p in enumerate(paras, 1):
        lines_est = max(len(p.strip().splitlines()), math.ceil(cn_count(p) / 40.0))
        if lines_est > 6:
            long_paras.append({"para_index": i, "est_lines": lines_est, "head": p.strip()[:20]})
    return total, dialog, long_paras


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--min-chars", type=int, required=True)
    ap.add_argument("--max-chars", type=int, required=True)
    ap.add_argument("--tolerance-pct", type=float, default=2.0)
    ap.add_argument("--dialog-min", type=float, default=25.0)
    ap.add_argument("--dialog-max", type=float, default=60.0)
    ap.add_argument("--dialog-tolerance-pt", type=float, default=3.0)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    total, dialog, long_paras = analyze(args.file)
    ratio = (dialog / total * 100.0) if total else 0.0
    checks, budget = [], {}

    tol = args.tolerance_pct / 100.0
    lo, hi = args.min_chars * (1 - tol), args.max_chars * (1 + tol)
    if total < lo:
        checks.append({"id": "char-count", "level": "budget", "status": "fail",
                       "value": total, "limit": "%d-%d" % (args.min_chars, args.max_chars)})
        budget["need_chars"] = args.min_chars - total
    elif total > hi:
        checks.append({"id": "char-count", "level": "budget", "status": "fail",
                       "value": total, "limit": "%d-%d" % (args.min_chars, args.max_chars)})
        budget["cut_chars"] = total - args.max_chars
    else:
        note = "tolerance" if (total < args.min_chars or total > args.max_chars) else ""
        checks.append({"id": "char-count", "level": "budget", "status": "pass",
                       "value": total, "limit": "%d-%d" % (args.min_chars, args.max_chars),
                       "note": note})

    dlo, dhi = args.dialog_min - args.dialog_tolerance_pt, args.dialog_max + args.dialog_tolerance_pt
    if ratio < dlo:
        rmin = args.dialog_min / 100.0
        need = int(math.ceil((rmin * total - dialog) / (1 - rmin)))
        checks.append({"id": "dialog-ratio", "level": "budget", "status": "fail",
                       "value": round(ratio, 1), "limit": "%g-%g%%" % (args.dialog_min, args.dialog_max)})
        budget["need_dialog_chars"] = max(need, 0)
    elif ratio > dhi:
        checks.append({"id": "dialog-ratio", "level": "budget", "status": "fail",
                       "value": round(ratio, 1), "limit": "%g-%g%%" % (args.dialog_min, args.dialog_max),
                       "note": "对话超带：补叙述/动作 beat，勿删信息量对话"})
    else:
        note = "tolerance" if (ratio < args.dialog_min or ratio > args.dialog_max) else ""
        checks.append({"id": "dialog-ratio", "level": "budget", "status": "pass",
                       "value": round(ratio, 1), "limit": "%g-%g%%" % (args.dialog_min, args.dialog_max),
                       "note": note})

    if long_paras:
        checks.append({"id": "long-paragraph", "level": "advisory", "status": "info",
                       "value": len(long_paras), "detail": long_paras[:5],
                       "note": "超长段按镜头断段（advisory，不阻断）"})

    hard_fail = [c for c in checks if c["level"] == "budget" and c["status"] == "fail"]
    result = {"file": args.file, "pass": not hard_fail, "total_chars": total,
              "dialog_ratio_pct": round(ratio, 1), "checks": checks, "repair_budget": budget}

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("字数 %d（区间 %d-%d）| 对话 %.1f%%（区间 %g-%g%%）"
              % (total, args.min_chars, args.max_chars, ratio, args.dialog_min, args.dialog_max))
        for c in checks:
            mark = {"pass": "✅", "fail": "❌", "info": "ℹ️"}[c["status"]]
            print("%s %s: %s (limit %s) %s" % (mark, c["id"], c["value"], c.get("limit", "-"), c.get("note", "")))
        if budget:
            print("修复预算: %s" % json.dumps(budget, ensure_ascii=False))
    sys.exit(0 if result["pass"] else 1)


if __name__ == "__main__":
    main()
