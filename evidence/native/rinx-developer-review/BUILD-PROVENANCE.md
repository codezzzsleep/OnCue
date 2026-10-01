# Rinx `import_form.room` 修复：构建来源与差异证据

**任何"通过"都必须标注：固定 `0879548` + 本地 lookup patch。不得写成"官方原版已通过"。**

## 补丁来源
- 文件名：`rinx-import-room-control.patch`（AI1 #300 发来，见同目录）
- 大小 **2165 B**；声明 sha256 `a893c28424cb2fba0c039ef6841b5c58300c5b04b6d9dd58f2ef84a302bc96c0`
- **实算 sha256 与之逐字一致**（`getpatch.py` 校验通过）
- `base_commit` = `0879548ba826c786eb6ad3f60dfba7bd342bd750`
- 内容：`src/miniapps/ui.rs` 4 处 `ids!(room)` → `ids!(import_form.room)`
  （`@@ -218 / -326 / -349 / -739`，1 file changed, 4 insertions(+), 4 deletions(-)）

## 应用位置（按 AI1 #301：只用 /tmp 固定基准树）
- 基准树：**`/tmp/rinx-0879548-fixed`**，`git rev-parse HEAD` = `0879548ba826c786eb6ad3f60dfba7bd342bd750`
- 流程：`cp -r <cargo checkout> → /tmp/rinx-0879548-fixed` → `git apply --check` **通过** → `git apply` **成功**
- 应用后核对：`import_form.room` 计数 **4**，残留 `ids!(room)` 计数 **0**
- 差异存档：同目录 `rinx-0879548-local-lookup.diff`
- **cargo 官方 checkout 已还原为干净官方树**（`import_form.room` 计数 0），
  未把改动留在 cargo 依赖树里。

## 构建方式（不改工作区 Cargo.toml）
用 cargo CLI 的 `--config` 做 path override（配置存档：同目录 `path-override-config.toml`）：
```toml
[patch."https://github.com/hagency-org/Rinx.git"]
rinx = { path = "/tmp/rinx-0879548-fixed" }
```
已验证 `cargo metadata` 下 `rinx` 的 source 为 `(path)`、manifest 为 `/tmp/rinx-0879548-fixed/Cargo.toml`。
构建命令：`CARGO_BUILD_JOBS=2 cargo build --release -p octosense --config /tmp/rinx-patch-config.toml`

## 官方二进制备份（AI1 #301 要求）
- 官方：`/opt/src/OctoSense/target/release/octosense`
- 备份：`/root/oncue-runtime/backup/octosense-official-20261002`
- **sha256（官方与备份一致）：`6ee5eb1565bafbe53c38e972a916ce546d928c0d54ac238b100d542971e25fc3`**
- 大小：195396864 B
- 备份 sha 存档：`/root/oncue-runtime/backup/octosense-official.sha256`
- 新构建二进制若 sha 与官方**不同**，即证明补丁进了二进制；运行时须明确标注为
  "fixed 0879548 + local lookup patch"。

## 纪律（AI1 #301）
- **禁止预写 consent/lease**
- 房间当前只有 **8** 条消息 → 只能如实证明"读到现有 8 条（服务上限 12）"，**不得补造 12 条**，
  也不得自动向房间发消息
- 验收顺序：① 无效 room 必须明确 `Invalid Matrix room ID`；② 有效 room 必须显示精确 `Allowed room`（报告不回贴私有 room id）；
  ③ 通过后 Run 最新 044，由 **OnCue 自身**读取真实消息并与事件 ID/时间/发送者/正文摘要核对；④ 再做共享 Octos 七块回合与 stop/90 秒/过期回调隔离
