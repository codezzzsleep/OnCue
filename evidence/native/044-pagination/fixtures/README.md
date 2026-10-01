# fixtures/ — 分页测试用例

每个用例均 **≥ 200 个字符（码点）**，覆盖"不依赖源换行"的极端形态。
文件按 UTF-8 无 BOM 保存，可直接喂给宿主或 `simulate_paginate.py`。

| 文件 | 字符数 / 字节数 | 覆盖目标 | 说明 |
| --- | --- | --- | --- |
| `01-long-single-line-zh.txt` | 263 / 783 | 目标 1、3、7 | 一条长中文（无源换行），验证不能把源换行当视觉行 |
| `02-continuous-ascii.txt` | 311 / 311 | 目标 3、7 | 连续 ASCII、无空格，验证硬折行 |
| `03-continuous-spaces.txt` | 303 / 501 | 目标 3、7 | 大段连续空格，验证空格不 trim、不吞 |
| `04-multiline-ab.txt` | 259 / 739 | 目标 2、3、7 | 多行 A/B 对照文本，验证源换行处断页正常 |
| `05-long-dialogue.txt` | 336 / 968 | 目标 2、7、8 | 长对白 + 建议台词，用于 `body + "\n" + draft` 组合路径 |
| `06-emoji-combining.txt` | 309 / 646 | 目标 6、7 | emoji、ZWJ 序列、肤色、旗帜、NFD 组合字符 |
| `07-space-boundary.txt` | 276 / 428 | 目标 7 | 多空格正好压在分页边界，检查跨页处字符不多不少 |
| `08-minimal.txt` | 307 / 912 | 目标 3、7 | 极短行 + 300 个"字"，检查页数上界与末页空行 |

## 使用方式

1. **离线自查**（不需要宿主，本次已运行）：
   `python3 fixtures/simulate_paginate.py`
   逐行复刻 `cue_paginate`，检查"所有页拼接后 == 原文"与"每页视觉行数 ≤ 预算"。
2. **宿主 probe**（未运行，见 `../probe-plan.md`）：把 fixture 内容灌进
   `cue_sources[i].body` / `cue_routes[i].body` / `cue_summary` /
   `take-a.txt` / `take-b.txt`，逐页核对。

## 组合路径（与真实应用一致）

- 对白/建议（模式 0）实际分页文本 = `body + "\n" + draft`
- 现场摘要（模式 1）实际分页文本 = `cue_summary`（Agent 的第 1 块）
- A/B 对照（模式 2）实际分页文本 = `take-a.txt` / `take-b.txt` 的文件内容
- 原消息实际分页文本 = `cue_sources[i].body`

`simulate_paginate.py` 里也构造了这三类组合文本（A/B body + 换行 + draft、
长对白 + 建议、摘要 + 说明）一并验证。
