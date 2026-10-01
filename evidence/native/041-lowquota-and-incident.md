# 0.4.1 低配额验证尝试与镜像污染事件（如实记录）

日期：2026-10-01。本文件只记录路径、命令、日志原文与哈希，不含任何凭据内容。

## 1. 目的

验证 0.4.1 新增的 catch 失败反馈：容量不足时，写入+回读外包的 `try/catch` 应给出
「…没有保存完成；编辑框内容仍在。请检查应用存储空间，再重试。」并保留编辑框内容。
正常 4 MiB 配额下这条分支不会触发，因此需要一个小配额环境。

## 2. 尝试一：替换磁盘上的 manifest 配额（**未生效**）

做法：把仓库外诊断副本 `/tmp/oncue-diag-lowquota`（与正式 `oncue/bundle` 用
`diff -rq` 比对**只有 `manifest.json` 一处不同**，且顶层键完全一致，仅
`storage.max_bytes` 由 `4194304` 改为 `4096`）覆盖到
`/srv/oncue-apps/oncue-screening-room/bundle` 并重启宿主。

结果：**4 KiB 没有生效**，写入仍然成功。证据：

- 日志：`card: oncue-screening-room running under 6 capability(ies), 1 host(s), 4194304 bytes of storage`
  （同时磁盘 manifest 写的是 4096）；
- 行为：点「用这句」→ 草稿 37 字符；点「存A」→「版本 A 已保存并回读确认；关闭后可以取回。」；
  `take-a.txt` 被真实写入（149 B → 103 B）。

原因（源码）：App Hub card 路径的策略（含配额）来自**已验证 catalog 条目**，不是磁盘上的
bundle manifest：

- `crates/appstore/src/cardapp.rs:69-77`：`store.accept_catalog(root/catalog.json)` →
  `store.may_run(&app_id)` → 用返回的 policy 建 `isolate_settings`；
- `crates/app-policy/src/policy.rs:186`：`storage_bytes: clamp(manifest.storage.max_bytes, limits.max_storage_bytes)`；
- `crates/app-policy/src/containers.rs:76` → `crates/app-policy/src/splash_adapter.rs:32` → `splash.set_storage_quota(...)`；
- 安装包本身就在 jail 里：`crates/app-hub/src/client.rs:202-204`（`install_dir = app_data_root/<app>/bundle`）
  与 OctoSense `crates/shell/src/app_storage/mod.rs:210`（`jail = apps_root/<app>`）。

**结论**：卡片路径要复现"容量不足"，必须让**catalog 条目**给出小配额；改磁盘 manifest 无效。

## 3. 尝试一的副作用：镜像工件被污染（**已修复并复核**）

诊断副本被执行体误覆盖进已发布工件
`state/hub-mirror/artifacts/oncue-screening-room-0.4.1.bundle`。当场验证了两件事：

- `hub check` **拒绝**该工件（签名覆盖 manifest，改 quota 即令原签名失效）；
- 该工件显示 `storage 4096 bytes`。

修复：用仓库里提交 `9cb14a5`（0.4.1 签名后的精确字节）覆盖回来，并复核：

| 检查 | 结果 |
| --- | --- |
| `jail bundle` 与 git 工作树 `diff -r` | 完全一致 |
| 镜像工件与 git 工作树 `diff -r` | 完全一致 |
| `hub check`（带发布者公钥） | PASSED，`storage 4194304 bytes`，签名有效 |
| `hub verify catalog.json --anchor` | `catalog sequence 7 verified, 7 entries` |

建议的流程约束：**诊断副本禁止写入 `state/hub-mirror/`**。

## 4. A/B 基准的如实说明（不假称仍有 149 B 的 A）

| 文件 | 原始基准（历史） | 当前磁盘 | 说明 |
| --- | --- | --- | --- |
| `draft.txt` | 103 B / `a5668eea5b258efe` | 103 B / `a5668eea5b258efe` | 未变 |
| `take-a.txt` | 149 B / `b8772f55c599205f` | **103 B / `a5668eea5b258efe`** | 被第 2 节那次**真实写入**覆盖；旧 149 B 仅作已覆盖历史保留 |
| `take-b.txt` | 136 B / `0a3c860464c504af` | 136 B / `0a3c860464c504af` | 未变 |

因此当前回读的正确描述是：**A 与 draft 相同、与 B 不同**；不能再以 149 B 作为 A 的当前
基准（AI1 #142 明确要求）。A/B 的"两份不同内容"证据由 `take-b.txt`（136 B）与
AI1 的独立截图 `evidence/native/22-041-ab-browser.jpg`（sha256 `017361bf…`）共同支撑。

## 5. 下一步：低配额 catch 的正确做法（AI1 #142 指示）

在 **Rinx Developer 私有 unsigned 导入路径**上、用**隔离的测试 app id** 验证：

1. 复制 bundle 到仓库外，改 **app id**（例如 `oncue-lowquota-probe`）并把
   `storage.max_bytes` 设小（例如 4096）——app id 不同才能避开已验证 catalog 的既有授权；
2. 在 Rinx Developer 里导入该副本（私有、unsigned、走官方未签名开发者路径）；
3. 复现失败路径并记录：UI 状态原文、编辑框内容是否保留、目标文件是否未创建/未变动；
   **日志有什么记什么**（catch 抓住 trap 后不一定再打印未捕获行）；
4. **不写 `state/hub-mirror/`、不预写 consent、不动正式包**。

状态：**未完成**（等桌面交回后执行）。
