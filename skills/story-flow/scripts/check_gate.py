#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_gate.py — story-flow 确定性门禁：字数预算 / 对话占比 / 超长段落。

只用标准库。输出人读摘要 + （--json 时）机读 JSON，含精确修复预算。
风格指纹检查不在本脚本：由 story-deslop check-ai-patterns.js --fail-on=blocking 承担。
分级/容差/轮次规则的正典见 references/gate-policy.md。

字数口径（重要）：total = len(全文文本)，全码点计数，与仓库钦定口径一致
（scripts/test-charcount-portable.sh 的 len(Path.read_text())、
check-prose-after-write hook 的 len(text)、细纲情节点序列的字数预算同源）。
不要与"仅中文字符数"混用；cn_chars 仅作参考信息输出。

调用（遵守仓库解释器探测惯例，禁止裸调）：
  for PYBIN in python3 python py; do "$PYBIN" -c "" 2>/dev/null && break; done
  "$PYBIN" skills/story-flow/scripts/check_gate.py 正文/C-0001.md --config 设定/门禁配置.json
  "$PYBIN" ... check_gate.py 正文/C-0001.md --min-chars 2200 --max-chars 2420   # 控制卡覆写

参数优先级：CLI > --config 文件 > 内置默认。min/max-chars 必须由 CLI 或 config 提供。
退出码：0 = 硬性项（字数/对话占比，容差后）全过；1 = 未过；2 = 参数/配置错误。
"""
import argparse
import json
import math
import re
import sys

CN_RE = re.compile(r"[一-鿿]")
# 对话span：中英双引号与直角引号内的内容；内容类排除所有引号字符，
# 防止缺闭引号时贪婪跨段吞叙述（嵌套引号会在内层截断，占比按容差带吸收该近似误差）
DIALOG_RE = re.compile(r"[\"“「『]([^\"“”「」『』]*)[\"”」』]")

DEFAULTS = {"dialog_min": 25.0, "dialog_max": 60.0,
            "tolerance_pct": 2.0, "dialog_tolerance_pt": 3.0,
            "long_para_chars": 250}


def die(msg):
    print("参数/配置错误: %s" % msg, file=sys.stderr)
    sys.exit(2)


def analyze(path):
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    total = len(raw.strip())
    dialog = sum(len(m) for m in DIALOG_RE.findall(raw))
    cn = len(CN_RE.findall(raw))
    long_paras, para_sent_counts = [], []
    for i, p in enumerate([p.strip() for p in re.split(r"\n\s*\n", raw) if p.strip()], 1):
        if p.startswith("#") or p.startswith("```"):
            continue
        if len(p) > DEFAULTS["long_para_chars"]:
            long_paras.append({"para_index": i, "chars": len(p), "head": p[:20]})
        para_sent_counts.append(max(len(re.findall(r"[。！？…]+", p)), 1))
    # 文风指纹（仅信息输出，不参与门禁判定；N6 用于跨章漂移对比）
    n_sent = sum(para_sent_counts) or 1
    fingerprint = {
        "sent_avg_chars": round(total / n_sent, 1),
        "single_sent_para_ratio_pct": round(
            sum(1 for c in para_sent_counts if c == 1) / len(para_sent_counts) * 100, 1)
        if para_sent_counts else 0.0,
        # 逗号密度哨兵（声口滚雪球乱码的早期指标，来源：voice-loop 实战教训）
        "comma_density_pct": round(raw.count("，") / cn * 100, 1) if cn else 0.0,
    }
    return total, dialog, cn, long_paras, fingerprint


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--config", help="JSON 配置（设定/门禁配置.json），CLI 参数优先于它")
    ap.add_argument("--min-chars", type=int)
    ap.add_argument("--max-chars", type=int)
    ap.add_argument("--tolerance-pct", type=float)
    ap.add_argument("--dialog-min", type=float)
    ap.add_argument("--dialog-max", type=float)
    ap.add_argument("--dialog-tolerance-pt", type=float)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    cfg = dict(DEFAULTS)
    if args.config:
        try:
            with open(args.config, encoding="utf-8") as f:
                loaded = json.load(f)
        except (OSError, ValueError) as e:
            die("无法读取配置 %s: %s" % (args.config, e))
        for k in ("min_chars", "max_chars", "dialog_min", "dialog_max",
                  "tolerance_pct", "dialog_tolerance_pt", "long_para_chars"):
            if k in loaded:
                cfg[k] = loaded[k]
    for cli_k, cfg_k in (("min_chars", "min_chars"), ("max_chars", "max_chars"),
                         ("tolerance_pct", "tolerance_pct"), ("dialog_min", "dialog_min"),
                         ("dialog_max", "dialog_max"), ("dialog_tolerance_pt", "dialog_tolerance_pt")):
        v = getattr(args, cli_k)
        if v is not None:
            cfg[cfg_k] = v

    if cfg.get("min_chars") is None or cfg.get("max_chars") is None:
        die("min_chars/max_chars 必须由 --min-chars/--max-chars 或 --config 提供")
    if not (0 < cfg["min_chars"] < cfg["max_chars"]):
        die("要求 0 < min_chars(%s) < max_chars(%s)" % (cfg["min_chars"], cfg["max_chars"]))
    if not (0 <= cfg["dialog_min"] < cfg["dialog_max"] <= 100) or cfg["dialog_min"] >= 100:
        die("要求 0 <= dialog_min(%s) < dialog_max(%s) <= 100" % (cfg["dialog_min"], cfg["dialog_max"]))
    if cfg["tolerance_pct"] < 0 or cfg["dialog_tolerance_pt"] < 0:
        die("容差不得为负")

    total, dialog, cn, long_paras, fingerprint = analyze(args.file)
    ratio = (dialog / total * 100.0) if total else 0.0
    checks, budget = [], {}

    tol = cfg["tolerance_pct"] / 100.0
    lo, hi = cfg["min_chars"] * (1 - tol), cfg["max_chars"] * (1 + tol)
    limit_s = "%d-%d" % (cfg["min_chars"], cfg["max_chars"])
    if total < lo:
        checks.append({"id": "char-count", "level": "budget", "status": "fail",
                       "value": total, "limit": limit_s})
        budget["need_chars"] = cfg["min_chars"] - total
    elif total > hi:
        checks.append({"id": "char-count", "level": "budget", "status": "fail",
                       "value": total, "limit": limit_s})
        budget["cut_chars"] = total - cfg["max_chars"]
    else:
        note = "tolerance" if (total < cfg["min_chars"] or total > cfg["max_chars"]) else ""
        checks.append({"id": "char-count", "level": "budget", "status": "pass",
                       "value": total, "limit": limit_s, "note": note})

    dlo = cfg["dialog_min"] - cfg["dialog_tolerance_pt"]
    dhi = cfg["dialog_max"] + cfg["dialog_tolerance_pt"]
    dlimit_s = "%g-%g%%" % (cfg["dialog_min"], cfg["dialog_max"])
    if ratio < dlo:
        rmin = cfg["dialog_min"] / 100.0
        need = int(math.ceil((rmin * total - dialog) / (1 - rmin)))
        checks.append({"id": "dialog-ratio", "level": "budget", "status": "fail",
                       "value": round(ratio, 1), "limit": dlimit_s})
        budget["need_dialog_chars"] = max(need, 0)
    elif ratio > dhi:
        checks.append({"id": "dialog-ratio", "level": "budget", "status": "fail",
                       "value": round(ratio, 1), "limit": dlimit_s,
                       "note": "对话超带：补叙述/动作 beat，勿删信息量对话"})
    else:
        note = "tolerance" if (ratio < cfg["dialog_min"] or ratio > cfg["dialog_max"]) else ""
        checks.append({"id": "dialog-ratio", "level": "budget", "status": "pass",
                       "value": round(ratio, 1), "limit": dlimit_s, "note": note})

    if long_paras:
        checks.append({"id": "long-paragraph", "level": "advisory", "status": "info",
                       "value": len(long_paras), "detail": long_paras[:5],
                       "note": "单段超 %d 字符，按镜头断段（advisory，不阻断）" % DEFAULTS["long_para_chars"]})

    hard_fail = [c for c in checks if c["level"] == "budget" and c["status"] == "fail"]
    result = {"file": args.file, "pass": not hard_fail, "total_chars": total,
              "cn_chars": cn, "dialog_ratio_pct": round(ratio, 1),
              "fingerprint": fingerprint, "checks": checks, "repair_budget": budget}

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("字数 %d（区间 %s，全码点口径）| 对话 %.1f%%（区间 %s）| 中文字符 %d"
              % (total, limit_s, ratio, dlimit_s, cn))
        for c in checks:
            mark = {"pass": "✅", "fail": "❌", "info": "ℹ️"}[c["status"]]
            print("%s %s: %s (limit %s) %s" % (mark, c["id"], c["value"], c.get("limit", "-"), c.get("note", "")))
        if budget:
            print("修复预算: %s" % json.dumps(budget, ensure_ascii=False))
    sys.exit(0 if result["pass"] else 1)


if __name__ == "__main__":
    main()
