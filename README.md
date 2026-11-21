# 内隐联想测验中文版

**简体中文** · [English](README.en.md)

![license](https://img.shields.io/badge/license-GPLv3-white)
![python](https://img.shields.io/badge/python-3.10%20~%203.12-white)
![psychopy](https://img.shields.io/badge/psychopy-2021%2B-white)
![platform](https://img.shields.io/badge/platform-Windows-white)

一个可以直接跑的中文内隐联想测验（IAT）程序，在 Ian Hussey 的开源版本基础上汉化，
按国内被试的使用习惯重新安排了材料、指导语与区块结构。

实验材料、指导语、按键、区块结构、计分参数全部写在一份 `config.yaml` 里，换实验材料不需要改代码。
它按 Greenwald 等（2022）附录 A 的标准七区组排试次，按同系列 2003 年的改进算法算 D 值，
每个试次的数据逐条落盘。它不带界面向导，不做数据分析图，也不联网。

**[使用说明](使用说明.md)** · [设计档案](docs/design.md) · [上游版本存档](upstream/README.md)

---

## 相对上游的改动

汉化与适配集中在三处：中文能正常显示，材料换了不用改代码，配对顺序写在编号里而不是靠奇偶反推。

| 项 | 上游（IAT.py） | 本版 |
|---|---|---|
| 运行环境 | Python 2 | Python 3.10 至 3.12，PsychoPy 2021 之后 |
| 中文显示 | 字体写死 Arial，中文显示为方框 | 自动查找系统中文字体 |
| 改实验材料 | 改 3 个 xlsx，左右位置靠约定 | 改 `config.yaml`，启动时校验 |
| 试次平衡 | 每个类别必须正好 5 个样例 | 任意数量，按类别轮转取词 |
| 配对顺序 | 靠被试编号奇偶反推 | 编号前缀 T / F 显式指定，并写入数据 |
| 计分 | 需要装 R 与 RStudio | `score.py`，纯 Python |
| 数据列 | `accuracy` 是反向的（1 表示错） | 拆成 `first_key_correct` 等自解释列 |

上游的 `IAT.py`、`IAT.psyexp`、三个 xlsx 与示例图片原样未动，整体收在 [upstream/](upstream/) 目录里，
连它自己的 README 与数据脚本一并保留。它们不参与本版运行，只作对照。

## 实验设计

七个区块，合计 190 试次，约需五分钟。区块 1 练目标词、区块 2 练属性词，
顺序不可颠倒（Greenwald 等 2022 建议 B5）；区块 3、4 为相容联合任务，区块 5 之后左右整体互换。

| 区块 | 左侧 | 右侧 | 试次 | 性质 |
|---|---|---|---|---|
| 1 | 虫 | 花 | 20 | 目标词辨别 |
| 2 | 消极 | 积极 | 20 | 属性词辨别 |
| 3 | 虫 或 消极 | 花 或 积极 | 20 | 相容联合（练习） |
| 4 | 虫 或 消极 | 花 或 积极 | 40 | 相容联合（正式） |
| 5 | 花 | 虫 | 30 | 相反目标词辨别 |
| 6 | 花 或 消极 | 虫 或 积极 | 20 | 不相容联合（练习） |
| 7 | 花 或 消极 | 虫 或 积极 | 40 | 不相容联合（正式） |

被试编号以 T 开头者先做相容配对，以 F 开头者先做不相容配对，两类交替安排以抵消顺序效应。
表中的左右安排是 T 组的样子，F 组整体镜像。

联合区块内目标词与属性词严格交替出现，同键连续不超过四个试次（建议 B3、B8）。
七个区块答错都显示红叉、按对才继续，反应时记的是改对之后的时刻（附录 A 的首选做法）。

概念词与属性词用不同颜色呈现，避免被试把属性词当成目标词归类（建议 A9）。
以上几条的依据见文末 [参考文献](#参考文献)。

## 工作原理

程序读一份 YAML 配置，校验通过后按布局定义生成七个区块，逐试次呈现并记录。

**计时基准。** 反应时从刺激真正出现在屏幕上的那一帧起算，取 `win.flip()` 返回的翻转时刻，
不用配置里标称的 0.3 秒。名义延迟与真实翻转之间有几十毫秒的浮动，拿标称值算会引入系统偏差。
按键时刻取自 `getKeys` 的事件时间戳，两者相减，实测误差在 1 毫秒以内。

**启动即校验。** 配置有问题就停下并说明原因，不带着错误把一整场做完才发现数据不可用。
校验覆盖布局引用、占位符能否填充、相容配对能否成立、计分参数是否合理。

**逐条落盘。** 每完成一个试次就写一行并刷新缓冲区。中途按 Esc 退出或程序异常，已完成的试次不会丢。

**配置快照。** 每次施测把当时的完整配置存成同名的 json。投稿后若被问起某个被试用的什么词、
什么参数，直接看这个文件。

## 四个脚本

| 脚本 | 作用 | 何时用 |
|---|---|---|
| `check.cmd` | 校验配置，打印七个区块的试次分配，不弹窗 | 每次改完配置 |
| `run.cmd` | 正式施测，会询问被试编号 | 每次施测 |
| `score.cmd` | 扫描 data 目录计分，输出 processed.csv | 收完数据 |
| `edit.cmd` | 用记事本打开 config.yaml | 改材料时 |

改完配置先跑 `check.cmd`。它会指出错在哪一行、哪个区块，比直接施测发现问题要省事得多。

## 安装

前置要求：Windows 10 以上，Python 3.10 至 3.12。

```bash
pip install psychopy pyyaml
```

PsychoPy 首次启动需要编译字体缓存，可能耗时数十秒，之后就快了。

装好后双击 `check.cmd`，看到「自检通过」即可开始。

## 换实验材料

打开 `config.yaml`，改 `concepts` 与 `attributes` 里的 `name` 和 `exemplars`，
保存后跑一次 `check.cmd`。

指导语不需要动。类别名用 `{L}` `{R}` 占位符自动替换，按键用 `{KEY_L}` `{KEY_R}` 替换，
改词表或改按键都不用回头找指导语。

七个说明页共用一段正文，写在 `instruction_common` 里，改一处七页同步。

## 计分

```bash
python score.py                      # 扫 data 目录
python score.py data/T001_xxx.csv    # 只算一个被试
```

按 Greenwald 等（2003）的 D 值算法、Greenwald 等（2022）附录 B 的现行写法：只取区块 3、4、6、7；
剔除慢于 10 秒的试次，剔除快速试次超过一成的被试；两段合并标准差用全部试次；
两个差值分别除以标准差后取平均。

标准差口径可在配置里切换。设成 `correct` 会只用正确试次，那是早期文献里的变体，
与现有口径算出的 D 不能直接比较。

输出 `processed.csv`，一人一行，含 D1、两个分项、正确率、快速试次占比与剔除原因。

## 常见疑问

1. **中文显示成方框**：系统缺中文字体。程序按微软雅黑、黑体的顺序查找，两个都没有时回落到默认字体。
   装任一中文字体即可。
2. **双击没反应或一闪而过**：多半是环境变量过长。PsychoPy 启动时把第三方包路径塞进环境变量，
   Windows 单个变量上限 32767 字符。四个脚本里已设置 `PSYCHOPYNOPACKAGES=1` 规避，
   直接用命令行启动时要自己设。
3. **控制台中文乱码**：中文 Windows 默认 GBK。脚本里已执行 `chcp 65001`，若仍乱码属终端问题，不影响数据。
4. **按 Esc 之后数据还有吗**：有。已完成的试次全部在 csv 里，只是该被试数据不完整，计分时会被标为缺少联合区块。
5. **能不能中途改配置**：不要。程序只在启动时读一次配置，中途改动不生效，却会让 json 快照与实际行为不符。
6. **错误率要不要剔除被试**：默认关闭。2003 年原文中这是可选步骤，若论文方法部分声明了，
   需把 `scoring.error_rate_exclude` 设为 0.10 或 0.20，否则代码不执行这一步。
7. **数据能不能用 Excel 编辑**：不要。保存动作会改编码与日期格式，程序再读时可能报错。
8. **一个被试做两遍会覆盖吗**：不会。文件名带时间戳，精确到秒。

## 开发

```bash
python tests/test_core.py        # 配置校验、区块生成、计分算法
python run.py --check-only   # 只校验配置，不弹窗
```

`tests/test_core.py` 不依赖 PsychoPy，可在任何装了 pyyaml 的解释器里跑。
它覆盖三块：配置读取与合法性判断、三个内置布局的试次结构、计分函数的数值结果。

图形呈现部分没有自动断言。反应时精度靠注入固定延迟的按键事件验证，方法见
[设计档案](docs/design.md) 的「验证方法」一节。

## 目录

```
├─ run.py                  施测主程序
├─ score.py                计分
├─ config.yaml             全部实验内容
├─ check.cmd               校验入口
├─ run.cmd                 施测入口
├─ score.cmd               计分入口
├─ edit.cmd                编辑配置
├─ data/                   被试数据，不入版本库
├─ tests/test_core.py      不依赖 PsychoPy 的单元测试
├─ docs/design.md          实现细节与设计取舍
├─ 使用说明.md             施测现场用的手册
├─ upstream/               上游版本原样存档，不参与运行
├─ LICENSE                 GPLv3
├─ .gitattributes          换行符规则
└─ .gitignore              数据与缓存排除规则
```

## 不要做的事

- **不要把被试数据提交到仓库。** `.gitignore` 已排除 `data/` 下的 csv 与 json，别手动加回来。
- **不要用 Excel 或 WPS 保存数据文件。** 要清理数据请用脚本另存，不要覆盖原始文件。
- **不要在施测途中改 `config.yaml`。** 改了不生效，却让快照失真。
- **不要手写「按错会怎样」这类提示。** 指导语里留 `{ERROR_RULE}` 让程序按配置生成，
  否则改了 `error_handling` 说明页就和实际行为脱节。
- **不要改 `error_handling` 却不改论文口径。** 程序行为与论文方法部分必须一致。

## 参考文献

- Greenwald, A. G., Brendl, C. M., Cai, H., et al. (2022). Best research practices for using the
  Implicit Association Test. *Behavior Research Methods, 54*, 1161–1180.
  本版的区块顺序、目标与属性交替、同键连续上限、配色区分、错误处理与计分口径均据此文的建议与附录 A、B。
- Greenwald, A. G., Nosek, B. A., & Banaji, M. R. (2003). Understanding and using the implicit
  association test: I. An improved scoring algorithm. *Journal of Personality and Social Psychology, 85*(2), 197–216.
- Greenwald, A. G., McGhee, D. E., & Schwartz, J. L. K. (1998). Measuring individual differences in
  implicit cognition: The implicit association test. *Journal of Personality and Social Psychology, 74*(6), 1464–1480.
- 施媛媛, 蔡华俭. (2016). 简式内隐联系测验原理及最新研究进展. 中国科学院心理研究所.
  https://www.psych.ac.cn/news/kyjz/202202/t20220224_6373690.html
  表 1 给出 IAT 的七组块设计（180 试次），`cas7` 布局据此实现。

## 声明

本仓库在 [ianhussey/IAT](https://github.com/ianhussey/IAT)（Ian Hussey, 2016）的基础上汉化并适配，
上游文件原样保留。实验范式源自 Greenwald, McGhee 与 Schwartz（1998），
计分遵循 Greenwald, Nosek 与 Banaji（2003），施测细节依 Greenwald 等（2022）的最佳实践。

## License

[GPLv3](LICENSE)
