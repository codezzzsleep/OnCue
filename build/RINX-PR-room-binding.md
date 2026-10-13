# Rinx PR 素材：导入表单房间号读到错误的输入框

> 用途：上游 Rinx 的修复 PR 素材。**是否提交由作者决定**（评审意见第 4 条：补丁若必需，准备好材料即可）。
> 核实于 2026-10-11：上游 main（已发布 1.3.0）的 `src/miniapps/ui.rs` 已含同义修复（`ids!(import_form.room)`）。因此本素材主要服务于仍钉在 v1.1.0（`4b89097d`）的下游：升级 Rinx ≥ 1.2.0 即可移除本地补丁。

## 标题

miniapps: qualify import-form room lookup (`ids!(import_form.room)`)

## 问题

Mini apps 导入面板（Discover → Mini apps → Import an app）里，房间号输入框的读取与清空用了不带路径的 `ids!(room)`。`ids!` 深度优先匹配整棵控件树，先命中的是内置库组件（DropDown）里同名的隐藏输入框，而不是导入表单里的 `import_form.room`。结果：

- `review_package` / Run 读到的房间号是空串；
- 导入后清空房间框清的是别人的框；
- 从 hub 带回 `reviewed_room` 时写入的也是别人的框。

应用最终以**无房间**状态启动：Rinx 提示 "this mini-app is not attached to a room"，应用侧只能提示用户重新导入。

## 复现

1. OctoSense 构建 Rinx v1.1.0（`4b89097d8791a7190d01de1c576979c93df0013d`），登录 Matrix。
2. Discover → Mini apps → Import an app：填一个未签名包路径，房间填合法房间 ID（如 `!abc:server`）。
3. Review bundle 正常通过（服务清单正常列出）。
4. 点 Run：Rinx 报 "this mini-app is not attached to a room"；应用读不到房间。

对照：同机同包，打上本补丁后 Review/Run 正常，房间绑定生效。

## 修法

`src/miniapps/ui.rs` 共 4 处，`ids!(room)` → `ids!(import_form.room)`：

```diff
-            self.view.text_input(cx, ids!(room)).set_text(cx, "");
+            self.view.text_input(cx, ids!(import_form.room)).set_text(cx, "");
@@
-        let room = self.view.text_input(cx, ids!(room)).text();
+        let room = self.view.text_input(cx, ids!(import_form.room)).text();
@@  (review_package)
-        let room = self.view.text_input(cx, ids!(room)).text();
+        let room = self.view.text_input(cx, ids!(import_form.room)).text();
@@  (run)
-                            self.view.text_input(cx, ids!(room)).set_text(cx, &self.reviewed_room);
+                            self.view.text_input(cx, ids!(import_form.room)).set_text(cx, &self.reviewed_room);
```

完整 diff 见 `oncue/docs/RUNNING.md` 的「Rinx 房间绑定补丁」一节。

## 回归建议

- 导入时填房间 → Review → Run，应用应以该房间启动（shell 无 "not attached to a room"）。
- 导入后再次打开导入面板，房间框应为空（清空的是正确的框）。
- 从 App Hub 带进房间启动时，导入面板的房间框应显示该房间。
- 库组件（DropDown）自身的 room 字段行为不受影响。

## 本地验证环境

旧机器（2026-10-11 前）：Linux aarch64 / X11 / 软件渲染；OctoSense 工作区以 `[patch]` 指向本地 Rinx 检出。现在的验证机器是 Linux x86_64。OnCue 0.5.3 的真机证据：`evidence/native-053/` 的大部分在打过补丁的二进制上取得；其中 10-11 下午那次完整闭环在官方 `c515e5fc`、零补丁的二进制上复验通过。
