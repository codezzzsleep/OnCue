# 远程桥驱动交互 + 空/错误/重启三态（DoD 第 3、4 条）

> 官方要求（`OctoScript-App-Design-Flow/AGENTS.md`）：
> - DoD 3："brief 里每个交互在 `card-host` 中**用远程桥原生驱动**（click/type/tap）并观察到效果"
> - DoD 4："**空、错误、重启**状态都跑过"
> - `flows/script-app/FLOW.md` 第 7 步："`/click?x=&y=`、`/t?t=…`、`/k?k=down`；每个动作后用截图或 `/snap` 观察"

## 运行方式（官方命令）

```sh
. /root/hackthon/refs/octo-env.sh
python3 tools/octo run /tmp/oncue-bridge/bundle --port 8151 \
        --app-data /tmp/oncue-bridge/.local-state --detach
# → card-host: oncue-screening-room 0.4.4 admitted — capabilities {...}
# → ready: first frame drawn
```
**坐标不靠猜**：先用 `curl "127.0.0.1:8151/snap?q=Button"` 拿到每个按钮的 `r=[x,y,w,h]`，
再取中心点点击。

## 逐项结果（全部由远程桥驱动）

| # | 状态 | 驱动方式 | 观察到 |
| --- | --- | --- | --- |
| 1 | **空状态**（初始，未操作） | — | 状态行 `虚构群聊与预设路线，仅供体验玩法。` |
| 2 | **错误状态**（服务不可用） | `/click?x=123&y=125`（载入群聊） | 状态行 **`没有读到群聊：no service answers "matrix" on this device`** —— 应用如实反馈，不崩、不伪造 |
| 3 | 样例路径 | `/click?x=53&y=259`（试映下一幕） | 状态行 `样例预设已展开；这些对白不是对真实群友的预测。`（样例明确标注为虚构） |
| 4 | **真实输入** | `/click?x=306&y=135` + `/t?t=BRIDGE-DRAFT-2026` | 返回 `{"ok":1,"f":78}` |
| 5 | 保存 | `/click?x=379&y=185`（存 A） | 状态行 `版本 A 已保存并回读确认；关闭后可以取回。` |
| 6 | 落盘 | — | `.local-state/oncue-screening-room/take-a.txt` = `BRIDGE-DRAFT-2026` |
| 7 | **重启持久化** | `/quit` → 重新 `octo run` → `/click?x=277&y=225`（取 A） | 状态行 **`版本 A 已放回编辑框；尚未发送。`**；文件仍在 |

## 截图
- `evidence/screenshots/bridge-1-error-state.png` —— 服务不可用时的如实反馈
- `evidence/screenshots/bridge-2-draft-saved.png` —— 存 A 成功
- `evidence/screenshots/bridge-3-restart-persist.png` —— 重启后取回

## 说明与限制
- **`tools/octo shot` 在本机不可用**（`/g?raw=1` → `grab timeout`，见 `OFFICIAL-FLOW-AUDIT.md` §3）。
  因此截图用 `ffmpeg -f x11grab` 抓 X11 窗口；**驱动仍全程走远程桥**。
- 未用 `--hidden`：本机 `/g` 抓帧失败，需要真实窗口才能截图。若要无头运行，
  `/snap`、`/click`、`/t` 仍可用，但没有可截的画面。
- `card-host` **不注册任何宿主服务**，所以第 2 项只能得到"服务不可用"，这是**预期行为**
  （`matrix.*` 只在 Rinx 中提供，已在 `RINXCHAT-VERIFICATION.md` 实测）。
