# 运行说明

## 需要什么

- 官方 Rinx 1.3.0 发布包（验证所用版本，独立运行）。OctoSense `0209df1` 自带的构建钉在 Rinx v1.1.0，照它构建会碰到导入表单读错房间号的问题（症状见下文「Rinx 房间绑定修复」），需要先打下文印出的补丁。
- 比赛服务器 `matrix.rinx.chat` 的账号，和一个有消息的房间。登录走浏览器单点登录。
- 宿主里已经配置好助手。
- （可选）本地构建的 `hub`，用来生成与仓库隔离的未签名副本。构建方法见 [OctoSense App Flow](https://github.com/OctoSense-org/OctoSense-App-Flow) 的 QUICKSTART。

card-host 可以打开应用并看内置样例，但它不提供 Matrix 和助手服务，读取群聊和试映只能在 Rinx 里进行。

## 宿主基线

以下版本是 0.5.3 的实际验证范围；细节与证据见[验证记录](../VERIFICATION.md)。

| 组件 | 仓库 | 提交 |
| --- | --- | --- |
| Rinx（真实闭环宿主） | `hagency-org/Rinx` | 官方 [1.3.0 发布包](https://github.com/hagency-org/Rinx/releases/tag/v1.3.0)（`rinx_1.3.0_x86_64.tar.gz`，零本地补丁；早期实测为官方源码 `c515e5fc`，对应界面升级前源码） |
| App Hub（card-host 与 hub 的来源） | `OctoSense-org/OctoSense-App-Hub` | `386359153ed6377b5f047bd9ed2767a6a2ac2bc7` |
| Makepad | `OctoSense-org/makepad` | `d653bc4493619ab979ccff165cf48c0c63b77d19` |
| OctoScript | `octos-org/octoscript` | `2e37d9e657a246f16718d9a475e167ccd2d5b5fa` |
| OctoScript-Makepad | `OctoSense-org/octoscript-makepad` | `6cf2d90aa33ff4ae603f49c7557f3ecf986207f0` |
| App Flow（octo 工具） | `OctoSense-org/OctoSense-App-Flow` | `15b1da01a769a770aaf12bd3012d17c6ff267b6c` |

平台是 Linux x86_64（X11，软件渲染）。macOS、Windows、Android、iOS 没有测过。

## Rinx 房间绑定修复（官方已含；v1.1.0 需回移植）

**0.5.3 最终源码的验证宿主是官方 Rinx [1.3.0 发布包](https://github.com/hagency-org/Rinx/releases/tag/v1.3.0)（零本地补丁）**，2026-10-13 完整跑通主流程与第二账号反响、确认期间新消息 N16（实测记录见 [evidence/native-130/](../../evidence/native-130/)；早期实测用官方源码 `c515e5fc`，对应界面升级前源码）。官方自 v1.2.0 起已修复房间绑定（`src/miniapps/ui.rs` 用 `ids!(import_form.room)` 限定导入表单），评委使用官方新版 Rinx 不需要任何补丁。

**只有仍钉在 v1.1.0（`4b89097d`）的构建需要下面的回移植**。OctoSense 的 `Cargo.toml` 用 `[patch."https://github.com/hagency-org/Rinx.git"] rinx = { path = "../rinx" }` 指向本地检出即可带上它（补丁全文见下文，上游 PR 素材 `build/RINX-PR-room-binding.md`）。

**症状**（未修复的 v1.1.0）：导入面板里填写的房间号在 Review/Run 路径上读到的是隐藏库组件里的同名输入框（`ids!(room)` 的深度优先匹配先命中库里的 DropDown，而不是导入表单里的 `import_form.room`），应用最终以无房间状态启动。

**补丁全文**（4 处，同一改动）：

```diff
--- a/src/miniapps/ui.rs
+++ b/src/miniapps/ui.rs
@@ -218,7 +218,7 @@ impl MiniAppsPanel {
             self.package = None;
             let package = Package::load_builtin(&app.manifest.id, &crate::app_data_dir().join("miniapps/imports"))?;
             self.show_import(cx);
-            self.view.text_input(cx, ids!(room)).set_text(cx, "");
+            self.view.text_input(cx, ids!(import_form.room)).set_text(cx, "");
             self.review_package(cx, package)?;
         }
         Ok(())
@@ -326,7 +326,7 @@ impl MiniAppsPanel {
         self.review_package(cx, package)
     }
     fn review_package(&mut self, cx: &mut Cx, package: Package) -> Result<(), String> {
-        let room = self.view.text_input(cx, ids!(room)).text();
+        let room = self.view.text_input(cx, ids!(import_form.room)).text();
         if !room.trim().is_empty() {
             ruma::RoomId::parse(room.trim()).map_err(|_| "Invalid Matrix room ID")?;
         }
@@ -349,7 +349,7 @@ impl MiniAppsPanel {
         let account = crate::sliding_sync::current_user_id()
             .ok_or("Log in to Matrix before running a mini app")?
             .to_string();
-        let room = self.view.text_input(cx, ids!(room)).text();
+        let room = self.view.text_input(cx, ids!(import_form.room)).text();
         if room.trim() != self.reviewed_room {
             return Err("Room access changed. Review the bundle again".into());
         }
@@ -732,7 +732,7 @@ impl Widget for MiniAppsPanel {
                             if crate::sliding_sync::current_user_id().is_none_or(|user| user.as_str() != account) { continue; }
                             self.return_to_hub = true;
                             self.reviewed_room = room.clone().unwrap_or_default();
-                            self.view.text_input(cx, ids!(room)).set_text(cx, &self.reviewed_room);
+                            self.view.text_input(cx, ids!(import_form.room)).set_text(cx, &self.reviewed_room);
                             let result = Package::load_verified(bundle.clone(), &crate::app_data_dir().join("miniapps/imports"))
                                 .and_then(|package| { self.package = Some(package); self.run(cx) });
                             if let Err(error) = result {
```

**未补丁对照运行记录**（2026-10-11，本机，未补丁二进制直接由上游 v1.1.0 构建）：导入表单填入包路径与房间 `!2TfO…`，Review 正常列出服务；点 Run 后 Rinx 提示 "this mini-app is not attached to a room"，OnCue 状态行显示「这次打开没有选房间。请关闭应用，导入时填上房间再打开。」主流程（读群、试映、发送）全部无法进行。截图证据：`evidence/rinx-patch/unpatched-no-room.png`。同机同包在打过补丁的二进制上走完整主流程，见 `evidence/native-053/`。

问题、复现、修法和回归建议整理在 `build/RINX-PR-room-binding.md`。上游 v1.2.0 已含同义修复，升级后不再需要本地补丁。

## 本地导入

仓库里的 `bundle/` 本身是未签名包，可以直接作为包路径导入（2026-10-13 在官方 Rinx 1.3.0 发布包上实测，Review 面板显示「Local unsigned bundle」），这时跳过第 1 步。需要一份与仓库隔离的独立副本时，再按第 1 步生成。

1. 生成未签名副本。Rinx 的本地导入不接受已签名的包。

   ```sh
   export OCTO_HUB=/path/to/OctoSense-App-Hub/target/release/hub
   DEV_ROOT="$(mktemp -d)"
   python3 oncue/tools/prepare_dev_bundle.py "${DEV_ROOT}/bundle" --hub "$OCTO_HUB"
   ```

2. 在 Rinx 里打开 **Discover → Mini apps → Import an app**。包路径填上一步打印出的目录，房间填你的 Matrix 房间 ID。小程序将在独立的「Rinx · Mini apps」窗口（1000×800）中打开。
3. 点 **Review bundle**。面板会列出应用名、版本、八项服务和 Allowed room。
4. 点 **Run**。每次打开都要重新授权，点 Back 关闭后授权失效。

## 使用

1. 打开后进入本地样例；选定房间的应用打开即读群，不用点按钮，最多30条、显示最近12条；需要宿主提供稳定房间ID。
2. 展开下方参考消息，核对并勾选本次范围。写台词，选澄清、拒绝或推动下一步，可补充边界。
3. 在数据范围卡允许当前范围内的试映与修订。点击「允许并试映」，三种说法带来源依据，推荐句自动放进草稿框；每次请求总限150秒，含至多一次修复；某条不合格只拦那一条并写明原因。
4. 点击「选用这句」或当前路线的「用这句」换一条。可直接编辑，也可填写修订要求、准备候选，核对后点击「应用修订」。
5. 「保留这句 / 存 A / 存 B」保存到当前房间，状态确认逐字回读后才完成。可切换原句/当前对照及A/B对照。发送后经「看反响」对照目标取下一句。
6. 重新打开后先载入同一房间再取回草稿。旧来源不自动当作当前消息，应重新核对。
7. 展开「本地草稿管理 / 删除 / 旧版迁移」可重新读取存储、删除本房间记录、手动复制旧版主稿/A/B或删除旧版文件。删除30秒确认，编辑变化后须重新确认。

未保存编辑切换房间会要求先保存或明确放弃。文件损坏、未知版本或其他窗口改写时停写；先关闭其他写入窗口并重新读取，无法恢复时只有明确清空全部新格式记录，不会自动覆盖空数据。

## 常见问题

- **点 Review 之后房间号被清空**：Rinx 早于 `bb2a4d4` 的版本有这个问题，升级 Rinx。
- **状态行显示“助手暂时不可用”**：宿主的助手没有启动或没有配置模型。独立 Rinx 1.3.0 在导入表单内直接填写（Assistant on this device: provider / Model / Base URL / API key，密钥留在 Rinx 运行时，配置位于 `RINX_DATA_DIR` 下）；OctoSense 桌面壳在 Settings → Accounts → AI providers 里检查。
- **同一台机器上开两个宿主实例时，第二个实例的助手启动失败**：每个实例要用不同的 `OCTOS_APP_CORE_DIR`。
- **状态行显示“这次打开没有选房间”**：导入时没有填房间。关闭应用，填上房间后重新导入。

## 几个时间限制

| 时间 | 是什么 |
| --- | --- |
| 150 秒 | 应用等待助手回答的上限，包含自动重试 |
| 185 秒 | Rinx 等待一次宿主服务调用的上限 |
| 1 小时 | 一次授权的有效期 |
