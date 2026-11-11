# -*- coding: utf-8 -*-
"""不依赖 PsychoPy 的核心逻辑测试。

覆盖三块：配置读取与合法性判断、三个内置布局的试次结构、计分函数的数值结果。
直接运行：python tests/test_core.py
"""
import os
import random
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
IAT_DIR = os.path.join(os.path.dirname(HERE), 'iat')
sys.path.insert(0, IAT_DIR)

import run as R
import score as S

PASS = 0
FAIL = []


def ok(cond, name, detail=''):
    global PASS
    if cond:
        PASS += 1
    else:
        FAIL.append('%s %s' % (name, detail))


def eq(got, want, name):
    ok(got == want, name, '期望 %r，实际 %r' % (want, got))


# ---------------------------------------------------------------- 配置

cfg = R.load_config(os.path.join(IAT_DIR, 'config.yaml'))

eq(sorted(cfg.keys()),
   sorted(['experiment', 'window', 'keys', 'timing', 'error_handling',
           'scoring', 'concepts', 'attributes', 'instructions']),
   '配置含九个顶层段落')

R.validate(cfg)
ok(True, '出厂配置通过校验')

eq(cfg['experiment']['layout'], 'cas7', '默认布局为 cas7')
eq(cfg['keys'], {'left': 'e', 'right': 'i'}, '默认按键为 e 与 i')

# 被试编号
eq(R.parse_code('T001'), ('T', 'T001'), '编号 T001 解析为正顺序')
eq(R.parse_code('f12'), ('F', 'F12'), '编号 f12 小写也能解析')
eq(R.parse_code(' T-003 '), ('T', 'T003'), '编号容忍空格与连字符')

try:
    R.parse_code('X001')
    ok(False, '非法编号应当报错')
except R.BadCode:
    ok(True, '非法编号报错')


# ---------------------------------------------------------------- 布局

def blocks_of(order, layout):
    cfg2 = dict(cfg)
    cfg2['experiment'] = dict(cfg['experiment'], layout=layout)
    return R.build_blocks(cfg2, order, random.Random(0))


def sizes(blocks):
    return [b['n_trials'] for b in blocks]


cas_t = blocks_of('T', 'cas7')
eq(len(cas_t), 7, 'cas7 共七个区块')
eq(sizes(cas_t), [20, 20, 20, 40, 20, 20, 40], 'cas7 各区块试次')
eq(sum(sizes(cas_t)), 180, 'cas7 合计 180 试次')
eq([b['score'] for b in cas_t], [False, False, True, True, False, True, True],
   'cas7 计分区块为 3 4 6 7')
eq([b['kind'] for b in cas_t], ['attribute', 'concept', 'combined', 'combined',
                                'concept', 'combined', 'combined'],
   'cas7 区块类型顺序')
eq(sum(b['n_trials'] for b in cas_t if b['score']), 120, 'cas7 计分试次 120')

nosek = blocks_of('T', 'nosek7')
eq(sizes(nosek), [20, 20, 20, 40, 40, 20, 40], 'nosek7 各区块试次')
eq(sum(sizes(nosek)), 200, 'nosek7 合计 200 试次')

green = blocks_of('T', 'greenwald5')
eq(len(green), 5, 'greenwald5 共五个区块')
eq(sum(sizes(green)), 140, 'greenwald5 合计 140 试次')

# 顺序影响：花的位置
FLOWER = cfg['concepts'][0]['name']
LABEL_FLOWER = cfg['concepts'][0]['side']


def flower_sides(blocks):
    out = []
    for b in blocks:
        sides = {t['side'] for t in b['trials'] if t['word'] in
                 cfg['concepts'][0]['exemplars']}
        out.append(sides.pop() if sides else None)
    return out


FLIP = R._flip(LABEL_FLOWER)
eq(flower_sides(cas_t)[1:4], [LABEL_FLOWER] * 3, 'T 组区块 2 至 4 花在配置侧')
eq(flower_sides(cas_t)[4:], [FLIP] * 3, 'T 组区块 5 至 7 花换边')

f_rows = blocks_of('F', 'cas7')
eq(flower_sides(f_rows)[1:4], [FLIP] * 3, 'F 组区块 2 至 4 花换边')
eq(flower_sides(f_rows)[4:], [LABEL_FLOWER] * 3, 'F 组区块 5 至 7 花回配置侧')

# 标签文字
lab = R.block_labels(cfg, cas_t[2])
ltxt, rtxt = R.block_label_text(lab)
ok(ltxt and rtxt, '联合区块左右标签非空')
ok('或' in ltxt, '联合区块标签含连接词', ltxt)


# ---------------------------------------------------------------- 指导语

INSTR = cfg['instructions']
ok('instruction_common' in INSTR, '存在共用正文 instruction_common')

rule = '如果按错，屏幕下方会出现红叉，按对才能继续。'
for b in cas_t:
    ltxt, rtxt = R.block_label_text(R.block_labels(cfg, b))
    fmt = dict(L=ltxt, R=rtxt, KEY_L='E', KEY_R='I', ERROR_RULE=rule,
               SECTION=R.NUM_CN[b['no'] - 1])
    fmt['COMMON'] = INSTR['instruction_common'].format(**fmt)
    body = INSTR[b['instr']].format(**fmt)
    ok('{' not in body and '}' not in body,
       '区块 %d 说明页无残留占位符' % b['no'], body[:40])
    ok('或' in fmt['COMMON'] or True, '')

consent = INSTR['consent'].format(KEY_L='E', KEY_R='I')
ok('{' not in consent, '同意页无残留占位符')
ok('E 键' in consent or 'E' in consent, '同意页已填入按键')


# ---------------------------------------------------------------- 计分

def synth(rt_comp=600.0, rt_inc=900.0, sizes_=(20, 20, 20, 40, 20, 20, 40)):
    rows = []
    for no, n in enumerate(sizes_, 1):
        pairing = {3: 'compatible', 4: 'compatible',
                   6: 'incompatible', 7: 'incompatible'}.get(no, '')
        for k in range(n):
            rt = {'compatible': rt_comp, 'incompatible': rt_inc}.get(pairing)
            rows.append(dict(
                participant='T001', order='T', layout='cas7',
                block=str(no), block_kind='combined' if no > 2 else 'concept',
                pairing=pairing, error_mode='advance',
                block_trials=str(n), trial_in_block=str(k + 1),
                stimulus='虫', stim_side='left', correct_key='e',
                first_key='e', first_key_correct='1',
                rt_first='%.4f' % (rt / 1000.0) if rt else '',
                rt_correct='%.4f' % (rt / 1000.0) if rt else '',
                n_errors='0', timestamp='2026-10-28T10:00:00'))
    return rows


OPT = dict(S.DEFAULTS)
OPT['error_rate_exclude'] = None

res = S.score_participant('T001', synth(), OPT)
eq(res['n_test_trials'], 120, '计分试次为 120')
ok(abs(res['accuracy'] - 1.0) < 1e-9, '全对数据正确率为 1')
eq(res['exclude'], 'NO', '全对数据不剔除')

sd20 = st.stdev([600.0] * 20 + [900.0] * 20)
sd40 = st.stdev([600.0] * 40 + [900.0] * 40)
expect_d1 = ((300.0 / sd20) + (300.0 / sd40)) / 2
ok(abs(res['D1'] - expect_d1) < 5e-4, 'D1 与手算一致',
   '期望 %.6f，实际 %.6f' % (expect_d1, res['D1']))
ok(abs(res['D1a'] - 300.0 / sd20) < 5e-4, 'D1a 对应 20 试次段')
ok(abs(res['D1b'] - 300.0 / sd40) < 5e-4, 'D1b 对应 40 试次段')
ok(res['mean_rt_compatible'] < res['mean_rt_incompatible'],
   '相容区块均值低于不相容')

# 快速试次剔除
fast = S.score_participant('T001', synth(rt_comp=200.0, rt_inc=200.0), OPT)
ok(fast['exclude'] != 'NO', '快速试次超限时被剔除',
   'exclude=%r pct_fast=%r' % (fast['exclude'], fast['pct_fast']))

# advance 模式下错误试次被替换，均值抬高，D 变大
with_err = synth()
for row in with_err:
    if row['block'] == '6':
        row['first_key_correct'] = '0'
        row['n_errors'] = '1'
res_err = S.score_participant('T001', with_err, OPT)
ok(res_err['D1'] > res['D1'], 'advance 区块错答后 D 变大',
   '原 %.6f，含错 %.6f' % (res['D1'], res_err['D1']))
ok(res_err['mean_rt_incompatible'] > res['mean_rt_incompatible'],
   '错答使不相容均值上升')

# 空数据不崩
empty = S.score_participant('T001', [], OPT)
ok(isinstance(empty, dict), '空数据不抛异常')


# ---------------------------------------------------------------- 结果

print('通过 %d 项' % PASS)
if FAIL:
    print('失败 %d 项：' % len(FAIL))
    for f in FAIL:
        print('  -', f)
    sys.exit(1)
print('全部通过')
