"""B 主故障（缓存 key 忽略范围）的复现、干预、修复、回归、变体与边界。

纯标准库，无第三方依赖。运行：
    python tests_b.py
逐项打印 PASS/FAIL，并把结构化结果写到 runs/tests_b_summary.json。
"""
import copy
import json
from pathlib import Path

from challenge import Engine as BaselineEngine
from engine_fixed import Engine as FixedEngine

ROOT = Path(__file__).parent
data = json.loads((ROOT / 'data.json').read_text(encoding='utf-8'))
corpus = data['corpus']


def case_by_id(cid):
    return next(c for c in data['cases'] if c['id'] == cid)


results = []


def check(name, cond, detail=''):
    results.append({'name': name, 'pass': bool(cond), 'detail': str(detail)})
    print(('PASS ' if cond else 'FAIL ') + name + (('  -> ' + str(detail)) if detail != '' else ''))


# ---------- 1. 原始失败复现（baseline：R01 后接 R02 共享状态） ----------
eng = BaselineEngine()
r01, r02 = case_by_id('R01'), case_by_id('R02')
o1 = eng.evaluate(r01['request'], corpus, r01['draft'])
o2 = eng.evaluate(r02['request'], corpus, r02['draft'])
check('复现: R02 命中缓存(cache_hit=true)', o2['cache_hit'] is True, f"cache_hit={o2['cache_hit']}")
check('复现: R02 返回旧结论「30秒」', o2['answer'].startswith('请求超时阈值为30秒'), o2['answer'])
check('复现: R02 证据是 v1 的 b01', o2['evidence'] and o2['evidence'][0]['id'] == 'b01',
      [b['id'] for b in o2['evidence']])
check('复现: R02 假加速(elapsed<R01)', o2['elapsed_ms'] < o1['elapsed_ms'],
      f"R01={o1['elapsed_ms']:.4f}ms R02={o2['elapsed_ms']:.4f}ms")

# ---------- 2. 区分性干预：全新 engine 跑 R02（清空缓存） ----------
eng_fresh = BaselineEngine()
o2f = eng_fresh.evaluate(r02['request'], corpus, r02['draft'])
check('干预: 全新 R02 不命中缓存', o2f['cache_hit'] is False, f"cache_hit={o2f['cache_hit']}")
check('干预: 全新 R02 返回正确「12秒」', o2f['answer'].startswith('请求超时阈值为12秒'), o2f['answer'])
check('干预: 全新 R02 证据是 v2 的 b02', o2f['evidence'] and o2f['evidence'][0]['id'] == 'b02',
      [b['id'] for b in o2f['evidence']])
check('干预结论: 原因A(缓存污染)成立、原因B(检索错误)被排除',
      o2f['cache_hit'] is False and o2f['evidence'] and o2f['evidence'][0]['id'] == 'b02')

# ---------- 3. 最小修复验证（engine_fixed：R01→R02 共享状态） ----------
fix = FixedEngine()
f1 = fix.evaluate(r01['request'], corpus, r01['draft'])
f2 = fix.evaluate(r02['request'], corpus, r02['draft'])
check('修复: R01 仍正确(v1/b01)', f1['evidence'] and f1['evidence'][0]['id'] == 'b01',
      [b['id'] for b in f1['evidence']])
check('修复: R02 现在返回正确「12秒」', f2['answer'].startswith('请求超时阈值为12秒'), f2['answer'])
check('修复: R02 证据是 v2 的 b02', f2['evidence'] and f2['evidence'][0]['id'] == 'b02',
      [b['id'] for b in f2['evidence']])
check('修复: R02 不再误命中缓存', f2['cache_hit'] is False, f"cache_hit={f2['cache_hit']}")

# ---------- 4. 两个原本正常的回归（修复后仍正确） ----------
r05, r06 = case_by_id('R05'), case_by_id('R06')
o5 = FixedEngine().evaluate(r05['request'], corpus, r05['draft'])
o6 = FixedEngine().evaluate(r06['request'], corpus, r06['draft'])
check('回归 R05: metadata beta 证据 b05 且 valid', o5['evidence'] and o5['evidence'][0]['id'] == 'b05' and o5['locator_status'] == 'valid',
      [b['id'] for b in o5['evidence']] + [o5['locator_status']])
check('回归 R06: worker 证据 b06 且 valid', o6['evidence'] and o6['evidence'][0]['id'] == 'b06' and o6['locator_status'] == 'valid',
      [b['id'] for b in o6['evidence']] + [o6['locator_status']])

# ---------- 5. 变体一：资料版本 v1→v2→v1 不得串 ----------
fv = FixedEngine()
va = fv.evaluate(dict(r01['request']), corpus, r01['draft'])
vb = fv.evaluate(dict(r02['request']), corpus, r02['draft'])
vc = fv.evaluate(dict(r01['request']), corpus, r01['draft'])
check('变体(v1→v2→v1): 三个版本各取各的证据',
      va['evidence'][0]['id'] == 'b01' and vb['evidence'][0]['id'] == 'b02' and vc['evidence'][0]['id'] == 'b01',
      [va['evidence'][0]['id'], vb['evidence'][0]['id'], vc['evidence'][0]['id']])

# ---------- 6. 变体二：query 分词顺序（语义等价） ----------
fq = FixedEngine()
req_reorder = dict(r02['request'])
req_reorder['query'] = 'request threshold timeout'
oq = fq.evaluate(req_reorder, corpus, r02['draft'])
check('变体(query 词序重排): 证据仍是 b02（词袋等价）', oq['evidence'] and oq['evidence'][0]['id'] == 'b02',
      [b['id'] for b in oq['evidence']])

# ---------- 7. 自构造边界：缓存不随语料内容变化而失效（未解决） ----------
fb = FixedEngine()
req = dict(r01['request'])
fb.evaluate(req, corpus, r01['draft'])  # 先缓存 (alpha,v1)
corpus2 = copy.deepcopy(corpus)
for b in corpus2:
    if b['id'] == 'b01':
        b['text'] = '实验A timeout request threshold 改为99秒。'
ob = fb.evaluate(req, corpus2, r01['draft'])  # 同一 key -> 命中缓存 -> 旧文本
stale = ob['cache_hit'] is True and ob['evidence'][0]['text'].startswith('实验A timeout request threshold 为30秒')
check('边界(未解决): 语料改版后仍返回旧缓存文本', stale, ob['evidence'][0]['text'])

# ---------- 汇总 ----------
summary = {
    'total': len(results),
    'passed': sum(1 for r in results if r['pass']),
    'results': results,
}
out = ROOT / 'runs' / 'tests_b_summary.json'
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
print(f"\n{summary['passed']}/{summary['total']} 通过，结果已写入 {out.name}")
if summary['passed'] != summary['total']:
    raise SystemExit(1)
