#!/usr/bin/env bash
# qc-chapter.sh —— 逐章生产闭环的「一键质检」入口
#
# 把日更逐章落盘后的整套确定性质检收成一条命令，并修正执行顺序：
#   1) normalize-punctuation 先跑（会就地自动清 破折号——/省略号/双连字符/分隔线）
#   2) 再跑 ai-patterns（此时只剩需人工改写的 blocking，如 not-is「不是X是Y」），列表才准
#   3) degeneration 退化防护
#   4) 扩展扫描（软禁词 + 元信息/工程词 + 卷号泄漏 + 英文字母泄漏）
#   5) 字数统计（Python 字符数；区间 [目标, 目标×1.1]，90% 放行线）
#
# 用法:
#   bash skills/story-long-write/scripts/qc-chapter.sh 正文/第032章_*.md [更多章节...]
#   TARGET=2200 bash .../qc-chapter.sh 正文/第032章_*.md   # 指定目标字数(默认2200)
#
# 退出码: 0=全部 PASS；1=任一章存在 blocking / 扫描命中 / 字数低于 90% 放行线
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${TARGET:-2200}"
FLOOR=$(( TARGET * 90 / 100 ))
CEIL=$(( TARGET * 110 / 100 ))

# 软禁词 + 元信息/工程词 + 卷号 + 英文字母（正文严禁）
SCAN='缓缓|仿佛|犹如|宛若|眼中闪过|嘴角勾起|深吸一口气|不禁|，带着|上一章|上章|前一章|本章|这一章|前文|后文|伏笔|细纲|读者|卷一|卷二|卷三|卷四|卷五|[A-Za-z]|F[0-9]'

overall=0
for f in "$@"; do
  [ -f "$f" ] || { echo "✗ 找不到文件: $f"; overall=1; continue; }
  echo "════════════════════════════════════════"
  echo "章节: $f"
  echo "────────────────────────────────────────"

  # 1) 标点归一（就地修改，自动清破折号/省略号）
  node "$SCRIPT_DIR/normalize-punctuation.js" "$f" >/dev/null 2>&1

  # 2) ai-patterns（只报 blocking）
  if node "$SCRIPT_DIR/check-ai-patterns.js" --check --fail-on=blocking "$f" >/tmp/qc_ai.txt 2>&1; then
    echo "  ai-patterns   : PASS"
  else
    echo "  ai-patterns   : FAIL ↓（need 手工改写：not-is「不是X是Y」/ 残留破折号）"
    sed 's/^/      /' /tmp/qc_ai.txt
    overall=1
  fi

  # 3) 退化防护
  if node "$SCRIPT_DIR/check-degeneration.js" --check "$f" >/tmp/qc_deg.txt 2>&1; then
    echo "  degeneration  : PASS"
  else
    echo "  degeneration  : FAIL ↓"
    sed 's/^/      /' /tmp/qc_deg.txt
    overall=1
  fi

  # 4) 扩展扫描（软禁词/元信息/卷号/英文）
  hits=$(grep -nE "$SCAN" "$f" | grep -v '^1:')   # 跳过标题行(第1行)
  if [ -z "$hits" ]; then
    echo "  扩展扫描      : PASS（软禁词/元信息/卷号/英文 无命中）"
  else
    echo "  扩展扫描      : FAIL ↓（软禁词/元信息/卷号泄漏/英文字母）"
    echo "$hits" | sed 's/^/      /'
    overall=1
  fi

  # 5) 字数
  wc_out=$(python3 -c "from pathlib import Path;print(len(Path('$f').read_text(encoding='utf-8')))")
  if [ "$wc_out" -lt "$FLOOR" ]; then
    echo "  字数          : $wc_out ✗（低于 90% 放行线 $FLOOR，需补实义内容到 [$TARGET,$CEIL]）"
    overall=1
  elif [ "$wc_out" -gt "$CEIL" ]; then
    echo "  字数          : $wc_out ⚠（高于 $CEIL，宜压过场/合并疏点收敛）"
  else
    echo "  字数          : $wc_out ✓（区间 [$FLOOR 放行 / $TARGET 目标 / $CEIL 上限]）"
  fi
done

echo "════════════════════════════════════════"
if [ "$overall" -eq 0 ]; then
  echo "✅ 全部 PASS —— 可更新追踪四件套并提交"
else
  echo "❌ 存在 FAIL —— 按上方逐条改写后重跑本脚本（见 references/chapter-qc-playbook.md 改写套路）"
fi
exit "$overall"
