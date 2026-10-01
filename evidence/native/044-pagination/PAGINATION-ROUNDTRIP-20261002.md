# 044 分页：逐字符往返自证（**应用自己跑出来的**，2026-10-02）

## 这份证据解决什么

`probe-plan.md` 的 Probe 2 要验证"拼接后逐字符等于原文"，`test-plan.md` 此前状态是**未运行**。
本文是**运行结果**：让**应用自己的 `cue_paginate`** 在真实宿主里分页，再由应用自己拼接并比较，
把结果经 `fs.write` 落盘后读回。**不是 Python 模拟、也不是我的复刻。**

## 怎么做（可复现）

1. 复制候选包到仓库外：`/root/oncue-runtime/dev/probe-044/PG/`
2. 在该副本 **`main.splash` 末尾追加**一段只读探针（不改产品逻辑）：
   - 把夹具 `01-long-single-line-zh.txt` 作为字面量内联为 `pv_text`
   - 调 **产品自己的** `cue_paginate(pv_text, 4)`（现场原消息区的行数常量是 `cue_msg_rows=4`）
   - 用 `for` 把各页拼回 `pv_join`，算 `pv_join == pv_text`
   - `fs.write("pages.txt", …)`
3. manifest：`id=ai2-probe-pg`、`version=0.0.1`、`capabilities=["storage"]`、去掉签名
4. `card-host --bundle <PG> --app-data <jail> --stamp --allow-unsigned --size 412x892`
   （独立 display `:97`、`LP_NUM_THREADS=2`、一次只跑一个 card-host）
5. 读回 `<jail>/ai2-probe-pg/pages.txt`

## 原始输出（逐字复制，未改写）

```
pages=14
equal=true
orig_chars=263
join_chars=263
orig_bytes=783
join_bytes=783
P1_chars=20
P2_chars=20
P3_chars=20
P4_chars=20
P5_chars=20
P6_chars=20
P7_chars=20
P8_chars=20
P9_chars=21
P10_chars=20
P11_chars=20
P12_chars=20
P13_chars=20
P14_chars=2
```

核对：`12 × 20 + 21 + 2 = 263` ✔ 与 `orig_chars` 一致；`join_bytes == orig_bytes == 783` ✔

## 三方吻合（互相独立）

| 来源 | 页数 | 说明 |
| --- | --- | --- |
| **应用自身**（本文件） | **14** | `cue_paginate` 真实运行，且 `equal=true` |
| **像素实测** | **14** | 真实截图上的 `第 N 页 / 共 14 页`，14 张截图 sha 全唯一 |
| **独立复刻** | **14** | 按 `main.splash` 常量用 Python 复刻 |

`equal=true` 是**运行时结论**：分页→拼接**逐字符无损**，`orig/join` 的字符数(263)与字节数(783)双双相等。

## 因此缺陷定位（与本仓库 `FAILURES-AND-CORRECTIONS.md` 同一口径）

分页**算法本身正确**（无损、无溢出）。缺陷在**写死的几何常量**：

```
main.splash:20-22
let cue_page_cols = 11     // 写死
let cue_page_rows = 5      // 写死
let cue_msg_rows  = 4      // 写死（现场原消息区用它）
```

- **页数与视口宽度无关**：同一夹具 412 宽与 990 宽**都是 14 页**（像素实测），990 宽每行能装约 2.4 倍字，本该少一半。
- **矮窗口正文被截断**：990×613 下仍按 4 行切一页，但真实可见高度不足 4 行，`#1 夹具` 正文只显示约 1.5 行即被页脚压掉（截图可见）。

## 边界说明（不夸大）

- 本文件证明的是**分页与拼接无损**，**不是**"两视口显示都正确"。后者因上述常量问题**尚不成立**。
- 8 个夹具中，**01 与 06** 有像素实测；其余 6 个的页数来自复刻（算法层），已用 01/06 两点校准，但**未逐页截图**。
