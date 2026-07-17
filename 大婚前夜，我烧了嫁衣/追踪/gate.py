#!/usr/bin/env python3
# 本书门禁（女频古言参数）：字数2000-2500 / 对话25-50% / 逗号密度≤16% / 心理词≤6 / A类禁用词 / 章末钩子
# 提示项（不判负）：省略号≤4/千字 / 感叹号≤2/千字 —— 冷声口底盘，超了先自查
import sys, re, os
BAN = "慢慢地|缓缓地|渐渐地|显得|看上去|不禁"          # 古言书保留 似乎/仿佛 的正当用法，收紧副词类
PSY = "心里|心中|心头|脑海|脑中|思绪|心想|暗想|暗忖"    # 女频限量不禁：≤6/章
HOOK = ["来了","是谁","竟","原来","没想到","明日","今夜","死","血","信","帖","门","回来","开始","第一","最后","等","换","轮到","知道","？","！"]
def han(t): return len(re.findall(r'[一-鿿]', t))
def check(path):
    raw = open(path, encoding='utf-8').read()
    body = re.sub(r'^#.*$','',raw,flags=re.M)
    n = han(body)
    dlg = re.findall(r'[“"](.*?)[”"]', body, re.S)
    d = sum(han(x) for x in dlg)
    ratio = d/n*100 if n else 0
    comma = len(re.findall(r'[，,]', body)); cratio = comma/n*100 if n else 0
    ell = len(re.findall(r'…', body)); eratio = ell/n*1000 if n else 0
    ex = len(re.findall(r'！', body)); xratio = ex/n*1000 if n else 0
    psy = re.findall(PSY, body)
    ban = re.findall(BAN, body)
    tail = body.replace('\n','')[-300:]
    hook = [h for h in HOOK if h in tail]
    ok = (2000<=n<=2500) and (25<=ratio<=50) and (cratio<=16) and (len(psy)<=6) and not ban and hook
    print(f"[{'PASS' if ok else 'FAIL'}] {os.path.basename(path)}")
    print(f"  字数 {n} {'✓' if 2000<=n<=2500 else '✗(需2000-2500)'} | 对话 {ratio:.1f}% {'✓' if 25<=ratio<=50 else '✗(需25-50)'}")
    print(f"  逗号密度 {cratio:.1f}% {'✓' if cratio<=16 else '✗(断句碎裂红线)'} | 心理词 {len(psy)} {'✓' if len(psy)<=6 else '✗(女频限≤6):'+str(set(psy))}")
    print(f"  省略号 {eratio:.1f}/千字 {'✓' if eratio<=4 else '⚠(冷声口建议≤4，仅提示)'} | 感叹号 {xratio:.1f}/千字 {'✓' if xratio<=2 else '⚠(冷声口建议≤2，仅提示)'}")
    print(f"  A类禁用词 {'无✓' if not ban else '✗'+str(set(ban))} | 末300字钩子 {'✓'+str(hook[:4]) if hook else '✗无'}")
    return ok
if __name__=='__main__':
    r=[check(p) for p in sys.argv[1:]]
    sys.exit(0 if all(r) else 1)
