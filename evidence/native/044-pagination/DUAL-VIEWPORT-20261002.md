# 044 双视口实测：缺陷与精确定位（2026-10-02）

> 本文是**实测记录**。所有"页数"数字都标了来源（应用自证 / 像素 / 算法复刻），
> 未做实测的地方明确写"未逐页截图"。截图在 [`screenshots/`](screenshots/)。

## 0. 结论先说

| 事项 | 结论 |
| --- | --- |
| 分页**算法** | **正确**：逐字符无损（应用自证 `equal=true`，见 [`PAGINATION-ROUNDTRIP-20261002.md`](PAGINATION-ROUNDTRIP-20261002.md)），8 夹具 0 行溢出/0 列溢出/0 字素切断 |
| 分页**几何** | **错误**：`cue_page_cols=11` / `cue_page_rows=5` / `cue_msg_rows=4` 是**写死常量**，与真实视口无关 |
| 后果 A | **页数与宽度无关**：同一夹具在 412 与 990 宽**都是 14 页** |
| 后果 B | **矮窗口正文被截断**：990×613 下仍按 4 行切一页，真实可见高度不足 → 正文被页脚压掉 |

## 1. 怎么跑的（可复现）

- **独立 display `:97`**（不碰生产 `:99`）、**一次只跑一个 card-host**、**`LP_NUM_THREADS=2`**
- 探针包：仓库外 `/root/oncue-runtime/dev/probe-044/…`，`id=ai2-probe-*`、`version=0.0.1`、`capabilities=["storage"]`、**无签名**
- 夹具内联方式见 [`deploy/tools/make_probe_bundle.py`](../../../deploy/tools/make_probe_bundle.py)：
  **必须替换 `cue_show_demo()` 里的消息数组**，只改 `main.splash` 第 1 行无效（启动时会被覆盖）
- 输入注入用 [`deploy/tools/xclick.py`](../../../deploy/tools/xclick.py)（XTest）。
  **不要用 `rfb_input.py`**：它是 RFB/VNC 客户端，只连 `127.0.0.1:5901`（即 `:99`），
  **驱动不了 `:97`/`:98` 的 card-host**——我第一轮因此拿到 14 张 sha 完全相同的**假结果**

## 2. 412×892（夹具 01，263 字符 / 783 UTF-8 字节）

| 项 | 实测 |
| --- | --- |
| 消息计数 | `1 / 1` |
| 页数 | **`第 1 页 / 共 14 页`** |
| 翻页 | 点 `下翻` ×13，**14 张截图 sha 全部唯一** |
| 末页 | **`第 14 页 / 共 14 页`**，正文只剩结尾的 `。` |
| 越界 | 末页再点 `下翻`，画面与末页**完全一致**（不越界、不环绕） |
| 遮挡 | 412 高 892，未见按钮/页脚遮挡正文 |

截图：[`412-f1-page01.png`](screenshots/412-f1-page01.png)、[`412-f1-page14.png`](screenshots/412-f1-page14.png)

## 3. 990×613 —— 两个缺陷的实际证据

| 项 | 实测 |
| --- | --- |
| 页数 | **仍是 `共 14 页`**，与 412 宽**完全相同**（990 每行能装约 2.4 倍字，本该约 5–6 页） |
| 正文 | `#1 夹具` 只显示约 1.5 行即被页脚「虚构群聊与预设路线…」**截断**，该页其余正文**不可见** |

截图：[`990-f1-page01-clipped.png`](screenshots/990-f1-page01-clipped.png)

## 4. 源码根因

`oncue/bundle/main.splash`：
```
20: let cue_page_cols = 11     ← 写死列数
21: let cue_page_rows = 5      ← 写死行数
22: let cue_msg_rows  = 4      ← 现场原消息区写死行数
```
折行判据（约 95 行）：`let w = 1; if cue_is_wide(c) { w = 2 }; if cols + w > cue_page_cols { … }`

即每页 = 固定的 **11 列 × 4 行**（消息区）。`cue_is_wide` 只是"宽字符按 2 列"的启发式，
**整个模型与 Makepad 的真实排版无关**——这正是早先评审指出的"列宽是启发式"的量化版本。

## 5. 为什么修法不是"改一行常量"

查证结果（三处，均为只读）：

1. **宿主知道尺寸但不给应用**：`card-host/src/host.rs:231-239`
   `if let Some((w,h)) = args.size { … configure_window(size); resize(size); log!("card-host: window sized {w}x{h}") }`
   —— 尺寸只用于本机窗口配置与日志，**未注入脚本作用域**。
2. **应用侧无尺寸查询**：`main.splash` 全文无 `width()/height()/size()` 之类用法；Splash 根是 `width: Fill height: Fill`。
3. **脚本层未找到尺寸 API**：`makepad/widgets/src/splash.rs` 只有内部 `fn area()`；
   `tweaker.rs` 里的 `"width"` 属开发工具 Tweaker。（这是"**未找到**"，不是"不存在"。）

**两条可行修法**：
- **(A) 宿主侧**：eval 前把窗口尺寸注入 Splash 作用域（如 `win_w`/`win_h`），应用据此算 cols/rows。
  **不动 bundle，摘要不变。**
- **(B) 应用侧**：若该 revision 确有脚本可达的尺寸接口，则把 3 个常量改为按尺寸计算。
  **会改变 bundle 内容与摘要，需先确认再 stamp。**

## 6. 8 个夹具的页数（算法层，已用两点校准）

01=14、02=8、03=10、04=14、05=18、06=11、07=9、08=17（`cue_msg_rows=4`）。

**校准依据**：01 与 06 有**像素实测**（`共 14 页` / `共 11 页`）与复刻一致；
**其余 6 个只有算法层结果，未逐页截图**。

## 7. 边界（不夸大）

- 本文证明的缺陷是**几何常量与真实视口脱节**；**不**主张算法有损（算法已被应用自证为无损）。
- `990-f1-page01-clipped.png` 是 **1100×700 屏幕**上的 990×613 窗口截图（早先用 900 宽屏幕拍的一张右侧被裁，已作废）。
- emoji 夹具（06）在 412 下 `第 3 页 / 共 11 页`，13 个 emoji 完整渲染、无半个字形：
  [`412-f6-emoji-page03.png`](screenshots/412-f6-emoji-page03.png)
