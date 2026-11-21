# -*- coding: utf-8 -*-
"""累积式回归用例集。

每条用例写成可判真假的陈述句，编号固定，新用例只追加、不删除。
直接运行：python tests/test_regression.py
不依赖 PsychoPy。
"""
import csv
import io
import math
import os
import random
import statistics as st
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

import run as R
import score as S

CFG = R.load_config(os.path.join(ROOT, 'config.yaml'))
CASES = []


def case(cid, desc, cond, detail=''):
    CASES.append((cid, desc, bool(cond), detail))


def build(order='T', layout=None, seed=7):
    cfg = dict(CFG)
    if layout:
        cfg['experiment'] = dict(CFG['experiment'], layout=layout)
    return R.build_blocks(cfg, order, random.Random(seed))


def combined(blocks):
    return [b for b in blocks if b['kind'] == 'combined']


# ---------------------------------------------------------------- 结构

b1 = build(seed=7)
b2 = build(seed=7)
case('R1', '同一种子两次生成的试次序列完全一致',
     [[t['word'] for t in b['trials']] for b in b1] ==
     [[t['word'] for t in b['trials']] for b in b2])

b3 = build(seed=8)
case('R2', '不同种子生成的试次序列不全相同',
     [[t['word'] for t in b['trials']] for b in b1] !=
     [[t['word'] for t in b['trials']] for b in b3])

case('R3', 'greenwald7 各区块试次为 20/20/20/40/30/20/40',
     [b['n_trials'] for b in build(layout='greenwald7')] == [20, 20, 20, 40, 30, 20, 40],
     str([b['n_trials'] for b in build(layout='greenwald7')]))

alt_ok = True
for blk in combined(b1):
    kinds = ['T' if t['type'] in (R.T_CONCEPT_1, R.T_CONCEPT_2) else 'A' for t in blk['trials']]
    if any(kinds[i] == kinds[i + 1] for i in range(len(kinds) - 1)):
        alt_ok = False
case('R4', '联合区块内目标词与属性词严格交替', alt_ok)

worst = 0
for blk in combined(b1):
    run = mx = 1
    for i in range(1, len(blk['trials'])):
        if blk['trials'][i]['side'] == blk['trials'][i - 1]['side']:
            run += 1
            mx = max(mx, run)
        else:
            run = 1
    worst = max(worst, mx)
case('R5', '联合区块同键连续不超过四个', worst <= 4, '实际最长 %d' % worst)


import copy as _copy

_c2 = _copy.deepcopy(CFG)
del _c2['experiment']['layout']
case('R13', '配置缺少 experiment.layout 时校验直接报错，不静默套用某个布局',
     bool(R.validate(_c2)), str(R.validate(_c2))[:60])

case('R14', '区块结构由配置里的 layout 决定：显式写 nosek7 时区块 5 为 40 试次',
     [b['n_trials'] for b in build(layout='nosek7')] == [20, 20, 20, 40, 40, 20, 40],
     str([b['n_trials'] for b in build(layout='nosek7')]))


# ---------------------------------------------------------------- 计分

def rows_of(pairs, mode='advance', block_trials=4):
    """pairs: [(block_no, pairing, correct_flag, rt_ms), ...]"""
    out = []
    for no, pairing, ok, rt in pairs:
        out.append(dict(
            participant='T001', order='T', layout='test',
            block=str(no), block_kind='combined', pairing=pairing,
            error_mode=mode, block_trials=str(block_trials), trial_in_block='1',
            trial_type='concept_1', stimulus='虫', stim_side='left', correct_key='e',
            first_key='e' if ok else 'i', first_key_correct='1' if ok else '0',
            rt_first='%.4f' % (rt / 1000.0), rt_correct='%.4f' % (rt / 1000.0),
            n_errors='0' if ok else '1', timestamp=''))
    return out


OPT = dict(S.DEFAULTS, sd_basis='all')

golden = rows_of([(3, 'compatible', 1, 600), (3, 'compatible', 1, 600),
                  (3, 'compatible', 1, 700), (3, 'compatible', 1, 700),
                  (6, 'incompatible', 1, 900), (6, 'incompatible', 1, 900),
                  (6, 'incompatible', 1, 1000), (6, 'incompatible', 1, 1000)])
res = S.score_participant('T001', golden, OPT)

# 手算：相容均值 (600+600+700+700)/4 = 650；不相容 (900+900+1000+1000)/4 = 950
# 合并 SD：八个数与均值 800 的离差平方和 4*200^2 + 4*100^2 + 4*100^2 + 4*200^2 = 200000
# 样本方差 200000/7 = 28571.4286，SD = 169.0308
# D = (950-650)/169.0308 = 1.774829
hand_sd = math.sqrt(200000.0 / 7.0)
hand_d = 300.0 / hand_sd
case('R6', 'D 值黄金用例：八个试次手算 1.774824，程序输出一致（容差 5e-5，因输出保留四位小数）',
     abs(float(res['D1']) - hand_d) <= 5e-5,
     '手算 %.6f / 程序 %s' % (hand_d, res['D1']))

allwrong = rows_of([(3, 'compatible', 0, 800), (3, 'compatible', 0, 800),
                    (3, 'compatible', 0, 800), (3, 'compatible', 0, 800),
                    (6, 'incompatible', 0, 800), (6, 'incompatible', 0, 800),
                    (6, 'incompatible', 0, 800), (6, 'incompatible', 0, 800)])
resw = S.score_participant('T001', allwrong, OPT)
case('R7', '全错数据不崩溃，正确率为 0，D 有定义或明确剔除',
     abs(float(resw['accuracy'])) < 1e-9 and (resw['D1'] != '' or resw['exclude'] == 'YES'))

onlycomp = rows_of([(3, 'compatible', 1, 600), (3, 'compatible', 1, 700),
                    (3, 'compatible', 1, 800), (3, 'compatible', 1, 900)])
resc = S.score_participant('T001', onlycomp, OPT)
case('R8', '缺少不相容条件时 D 为空且标记剔除，原因含 D 分数无法计算',
     resc['D1'] == '' and resc['exclude'] == 'YES' and 'D 分数无法计算' in resc['exclude_reason'],
     'exclude=%s reason=%s' % (resc['exclude'], resc['exclude_reason']))

errrows = rows_of([(3, 'compatible', 0, 700)] * 4 + [(6, 'incompatible', 0, 900)] * 4)
rese = S.score_participant('T001', errrows, dict(OPT, error_rate_exclude=0.2))
case('R9', '错误率超过阈值 20% 时被试被剔除',
     rese['exclude'] == 'YES' and '错误率' in rese['exclude_reason'],
     rese['exclude_reason'])

slow = rows_of([(3, 'compatible', 1, 600), (3, 'compatible', 1, 700),
                (3, 'compatible', 1, 20000), (3, 'compatible', 1, 800),
                (6, 'incompatible', 1, 900), (6, 'incompatible', 1, 950),
                (6, 'incompatible', 1, 1000), (6, 'incompatible', 1, 1050)])
ress = S.score_participant('T001', slow, OPT)
case('R10', '超过 10000ms 的试次被剔除，但不计入试次总数',
     ress['n_test_trials'] == 8 and float(ress['mean_rt_compatible']) < 800,
     'n=%s 相容均值=%s' % (ress['n_test_trials'], ress['mean_rt_compatible']))


# ---------------------------------------------------------------- 数据文件

src = open(os.path.join(ROOT, 'run.py'), encoding='utf-8').read()
import re
m = re.search(r"fields = \[(.*?)\]", src, re.S)
fields = re.findall(r"'([a-z_]+)'", m.group(1)) if m else []
case('R11', '写入的 csv 共 19 列，且覆盖计分所需的全部列',
     len(fields) == 19 and S.REQUIRED_COLS <= set(fields),
     '%d 列' % len(fields))

tmp = tempfile.mkdtemp()
bad = os.path.join(tmp, 'bad.csv')
with open(bad, 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f)
    w.writerow(['participant', 'block'])
    w.writerow(['T001', '3'])
buf = io.StringIO()
old = sys.stdout
sys.stdout = buf
try:
    S.main()
except SystemExit:
    pass
finally:
    sys.stdout = old
sys.argv = ['score.py']
buf2 = io.StringIO()
sys.stdout = buf2
try:
    sys.argv = ['score.py', bad, '--out', os.path.join(tmp, 'p.csv')]
    S.main()
except SystemExit:
    pass
finally:
    sys.stdout = old
case('R12', '缺少必填列的文件被跳过并给出提示，不中断整个计分',
     '缺少列' in buf2.getvalue(), buf2.getvalue().strip()[:60])


# ---------------------------------------------------------------- 结果

passn = sum(1 for c in CASES if c[2])
print('用例 %d 条，通过 %d 条，未通过 %d 条' % (len(CASES), passn, len(CASES) - passn))
for cid, desc, good, detail in CASES:
    print('  %-4s %-4s %s%s' % (cid, 'PASS' if good else 'FAIL', desc,
                                ('  [' + detail + ']') if detail else ''))
if passn != len(CASES):
    sys.exit(1)
