# OctoSense 更新应对计划（2026-10-03 更新到来时执行）

> **来源**：用户 2026-10-02 告知"明天 octosense 会有一次更新"。非官方文档，待届时核对。

## 为什么要在意
我们的宿主 `octosense` 是**自己从源码构建**的（基线：官方 Rinx `c515e5fc9b6d` + OctoSense `c19da8d`）。
OctoSense 更新可能改动：Shell、`apps/`（系统应用与宿主服务）、`native-apps.json`、
`native-runtime.lock.json`（Makepad/Octoscript 锁定版本）、以及对 App Hub 的 pin。

## 执行步骤
```sh
cd /root/hackthon/refs/OctoSense
git fetch origin && git log --oneline -15 origin/main      # 看更新了什么
git diff --stat HEAD origin/main                            # 影响面
# 重点看这些路径是否变动：
#   apps/ (系统应用与宿主服务)  native-apps.json  native-runtime.lock.json
#   crates/shell/  crates/ai-host/  desktop/  rom/
# 同时看 App Hub 与 Rinx 是否也有新提交（它们的 pin 可能被改）
cd /root/hackthon/refs/OctoSense-App-Hub && git fetch origin && git log --oneline -5 origin/main
cd /root/hackthon/refs/Rinx && git fetch origin && git log --oneline -5 origin/main
```
## 若需要重建宿主
```sh
cd /root/hackthon/refs/Rinx && git checkout <新基线>            # 官方源码，零改动
cat > /tmp/rinx-official-config.toml <<'CFG'
[patch."https://github.com/hagency-org/Rinx.git"]
rinx = { path = "/root/hackthon/refs/Rinx" }
CFG
cd /opt/src/OctoSense
cp target/release/octosense /root/oncue-runtime/backup/octosense-before-update-$(date +%s)
CARGO_BUILD_JOBS=2 cargo build --release -p octosense --config /tmp/rinx-official-config.toml
```
## 重建后的回归清单（按 AGENTS.md §4.2 / ADR 0005）
1. `tools/octo check`（未签名副本）→ `PASSED`
2. 宿主换装 + `:99` 可访问
3. Rinx 登录赛事服务器 → 房间列表可见
4. `Import an app` → **Review 保留房间** → Run
5. 应用内 `载入群聊` → **真实房名 + 原消息已载入**
6. `试映下一幕` → **Agent 回合完成**（内核日志有 `LLM response received`）
7. **读房授权 sheet** 三选项与 45 秒拒绝（接收者演示要用）
8. 跨房间拒绝 / 实例撤销 / 迟回复处理
9. Back / 键盘 / 关闭-重开
10. 记录**未验证的平台/服务组合**，不得写"应该可以"

## 注意
- 更新可能**改动上限或能力名**：重建后重跑 `--dump-config` 与 `hub check` 的 `grants:` 行核对。
- 若官方同时更新 App Hub / Rinx 的 pin，**以它们的新 pin 为准**，不要混用旧版本结论。
- 所有新结论必须标注**服务器与版本**。
