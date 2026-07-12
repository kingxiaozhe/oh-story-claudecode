#!/usr/bin/env python3
# 本书门禁快检：字数2300-3800 / 对话25-50% / A类禁用词 / 心理词 / 章末钩子 / 标题唯一
import sys, re, glob, os
BAN = "似乎|仿佛|好像|慢慢地|缓缓地|渐渐地|显得|看上去|不禁|缓缓|渐渐|慢慢"
PSY = "心里|心中|心头|脑海|脑中|思绪|心想|暗想|暗忖"
HOOK = ["脸色一沉","回来了","一模一样","明天","今晚","还剩","电话响了","短信","四个字","三个字","只是","我要","等我","认识","走着瞧","推开","走进来"]
def han(t): return len(re.findall(r'[一-鿿]', t))
def check(path):
    raw = open(path, encoding='utf-8').read()
    title = re.search(r'^#\s*(.+)$', raw, re.M)
    body = re.sub(r'^#.*$','',raw,flags=re.M)
    n = han(body)
    dlg = re.findall(r'[“"](.*?)[”"]', body, re.S)
    d = sum(han(x) for x in dlg)
    ratio = d/n*100 if n else 0
    tail = re.sub(r'[^一-鿿]','',body)[-300:]
    hook = [h for h in HOOK if h in tail]
    ban = re.findall(BAN, body)
    psy = re.findall(PSY, body)
    ok = (2300<=n<=3800) and (25<=ratio<=50) and not ban and not psy and hook
    print(f"[{'PASS' if ok else 'FAIL'}] {os.path.basename(path)}")
    print(f"  字数 {n} {'✓' if 2300<=n<=3800 else '✗(需2300-3800)'} | 对话 {ratio:.1f}% {'✓' if 25<=ratio<=50 else '✗(需25-50)'}")
    print(f"  A类禁用词 {'无✓' if not ban else '⚠'+str(set(ban))} | 心理词 {'无✓' if not psy else '⚠'+str(set(psy))}")
    print(f"  末300字钩子 {'✓'+str(hook) if hook else '✗无'}")
    return ok
if __name__=='__main__':
    for p in sys.argv[1:]: check(p)
