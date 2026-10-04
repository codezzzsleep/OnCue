# AGENTS.md

给在这个仓库里工作的 AI 编码助手看的说明。

## 这是什么

OnCue 是参加 GOSIM Agentic App 2026 的 OctoScript 小程序，运行在 Rinx 里。提交的应用包是 `oncue/bundle/`，其余是说明、测试和证据。产品说明见 `oncue/BRIEF.md`，运行方法见 `oncue/docs/RUNNING.md`。

## 不能做的事

1. 不向任何 Matrix 房间发送消息。应用没有发送能力，测试时也不要用别的工具发。
2. 不把密钥、令牌、密码写进仓库，也不打印到输出里。签名私钥放在仓库外。
3. 不签名，不打标签，不推送，不在外部仓库开 issue 或评论。这些由作者做。
4. 不伪造测试结果、截图和审核结论。没跑过的就写“未验证”。
5. 不改写已经推送的历史。

## 改了应用包之后

`oncue/bundle/` 下任何文件有改动，都要做完下面几步再交给作者：

1. 把 `manifest.json` 里的版本号加一。同一个版本号只能对应一份内容。
2. 跑工具单元测试：`python3 -m unittest discover -s oncue/tests -p 'selftest_*.py'`。
3. 如果改了 `main.splash`：按 `oncue/tests/README.md` 重跑 8 套逻辑测试，用新结果替换 `evidence/logic-tests/`，更新 `oncue/VERIFICATION.md` 里的 SHA-256。
4. 如果改了界面文案：先搜 `oncue/tools/` 和 `oncue/tests/`，验收脚本和测试数据引用了一部分文案，要一起改。
5. 在 `CHANGELOG.md` 里加一条。
6. 列出需要作者做的事：盖章和签名、打标签、在 Rinx 里验证、重截图、重录屏。

## 常用命令

```sh
# 工具单元测试
python3 -m unittest discover -s oncue/tests -p 'selftest_*.py' -v

# 检查已签名的包（OCTO_HUB 指向本地构建的 hub）
"$OCTO_HUB" check oncue/bundle --publisher-key oncue.dev=50578fd7e0d8ac51a1e9e590835427ce8e71f46dba491860c75ae4e7c8c78042

# 生成未签名副本，用于 card-host 和 Rinx 本地导入
python3 oncue/tools/prepare_dev_bundle.py "$(mktemp -d)/bundle" --hub "$OCTO_HUB"
```

## 已知的坑

- card-host 不提供 `matrix.*` 和 `octos.*`，调用会返回 `no service answers "…" on this device`。读取群聊和试映只能在 Rinx 里验证。
- 已签名的包不能直接用于 card-host 和 Rinx 的本地导入，要先生成未签名副本。
- 比赛用的 Matrix 服务器是 `matrix.rinx.chat`，不是 `matrix.org`。登录走浏览器单点登录。
- 在 Linux aarch64 + Xvfb 上，`tools/octo shot` 截不了图（`grab timeout`）。用 `ffmpeg -f x11grab` 抓窗口。抓之前用 `xwininfo` 取窗口的位置和大小，抓取区域要对准窗口。
- 同一台机器上开多个宿主实例时，每个实例用不同的 `OCTOS_APP_CORE_DIR`。
- 清理进程用 `curl 127.0.0.1:<端口>/quit`，不要用 `pkill -f`。
- Splash 语法：
  - 十六进制颜色写成 `#x1e1e2e`。
  - 不支持 `0x` 字面量，没有 `range()`，循环写 `for i in n`。
  - 空代码块后面不能接 `else`。`ok` 是保留名。
  - `ui` 在脚本主体执行完之后才可用，启动逻辑放进 `start_timeout(0.05, …)`。
  - `View` 的背景在 card-host 里不绘制，用 `SolidView` 或 `RoundedView`。
  - `ButtonFlat` 不能有子控件。`TextInput` 必须给数值高度。文字默认是白色。

## 文档规则

- 读者是评委和想试用的人。只写这是什么、怎么运行、验证过什么、没验证什么。
- 过期的内容直接删，不要加“本文件已过期”的标注。
- 不写修改过程，不写“此前写错、现更正”，不写作者在对话里说过什么。
- 没做的事统一写在“未验证”里，每件事写一次。不要在别处反复写“不代表”“不等于”“不证明”。
- 不写本机路径、完整的账号和房间号、进程号。这些放在 `.private/ENV.md`，不入库。
- 不引用仓库里不存在的文件。
- 不新增文档，除非作者要求。状态变化写进 `CHANGELOG.md`。

## 提交规则

- 一个提交只做一件事。改应用包的提交，标题带版本号。
- 提交说明写改了什么，一句话。不写“全部完成”“已验证通过”这类结论。
- 不引用仓库外的编号。
- 作者身份用 `git config` 里已经设置好的，不要改。
