# 新容器联调：失败记录与纠正（2026-10-02）

本文记的是**实际发生过的失败与纠正**，不是"应该怎么做"的说明。
工具在 [`deploy/tools/`](tools/)，**全部无密钥**：密文只从仓库外的私有文件按运行时路径读取，
脚本里没有任何凭据字面量（已 `grep` 自检）。

---

## 1. RFB 键盘注入会把大写与符号静默打错（**最关键的一条**）

### 现象
用 RFB `KeyEvent(keysym=ord(ch))` 把 `A_z9!@#-_` 打进一个**非密文**输入框，
界面实际得到 **`az9-rg`**：大写变小写、`_ ! @ #` 丢失或串位。

### 后果
Rinx 真实登录连续两次返回 **`[403 / M_FORBIDDEN] Invalid username/password`**，
而**同一份凭据**用 `deploy/tools/matrix_login_probe.py` 直连 Matrix API 得到 **HTTP 200 + `Logged in successfully.`**。
也就是说：**"服务端拒绝"当时并不是凭据问题，而是我自己的输入层把密码打错了。**

### 根因
`x0vncserver` 把 RFB keysym 翻成 keycode 时**不补修饰键**：
`A`（keysym 0x41）与 `a`（0x61）共用同一个 keycode，不按 Shift 就出 `a`；
`_ ! @ #` 这类 Level-1 字符更是直接丢失。仅显式发一个 `Shift_L` keysym 也无效——
说明不能依赖 RFB 的映射实现。

### 纠正
新增 [`deploy/tools/xtype.py`](tools/xtype.py)：用 `libX11 + libXtst` 直接走 XTest，
`XKeysymToKeycode` + **`XkbKeycodeToKeysym(kc, group=0, level)`** 按**服务器自己的键映射**
找出该字符落在哪一层，只有 `level==1` 才按 `Shift_L`。不假设 US 布局。

过程中另踩并修掉一个坑：`XStringToKeysym("_")` 返回 0（它要的是键名 `underscore`）；
X11 约定 `0x20..0x7e` 的可打印 ASCII **其 keysym 值等于字符码**，所以直接用 `ord(ch)`。

修后同一串复测：字段正确显示 `A_z9!@#-_`；随后 Rinx 登录**一次通过**：
`sliding_sync.rs:246 - Logged in successfully.`

### 教训
**"服务端返回错误" ≠ "凭据错误"**。中间还隔着输入层、代理层、格式层。
分层的办法是：用一条**独立于 UI 的通道**（直连 API）先固定住"凭据是否有效"这个事实。

---

## 2. homeserver 不接受带 scheme 的写法

凭据里存的是 `https://matrix.org`，Rinx 报
`Could not check this server: Enter a valid server name, such as matrix.org.`
→ 只填 `matrix.org` 即可。发现流程随后给出 `Selected server: matrix-client.matrix.org`。

---

## 3. 宿主要出网必须带代理

- 本机**直连 matrix.org 超时**（`curl` 6.2s connection timed out）
- 走 `127.0.0.1:17888`：`/_matrix/client/versions` **200 / 0.83s**，`.well-known/matrix/client` **200**
- 给宿主补 `HTTPS_PROXY`/`HTTP_PROXY`/`NO_PROXY=localhost,127.0.0.1,::1` 后，Rinx 的 homeserver 发现立刻成功
- `deploy/env.sh` 里是**无密钥开关** `ONCUE_HOST_PROXY` / `ONCUE_HOST_PROXY_SOCKS`（默认关）

---

## 4. provider profile：密钥不进 profile（区分 host vault 与 octos keychain）

`host-service/src/model.rs:284-300` 的 `save()` 写得明确：
**vault 写成功 → profile 的 `config.env_vars.<ENV>` 只放 `"keychain:"` 标记**；
只有 vault 写失败才回退把原文写进 profile。而 `vault.rs:79` 的 vault 目录是
`<core_dir>/secrets`（0600 文件 / 0700 目录）。

**灾后恢复实测纠正（2026-10-02）**：上述是 OctoSense `ai-providers` host
写入侧的 vault；当前固定 octos CLI 在 Linux 解引用 `keychain:` 时读取的是
`$HOME/.octos/secrets/<ACCOUNT>`（`octos-cli/src/auth/keychain.rs:235-292`），不是
`<core_dir>/secrets`。把两者混为一处会导致 `MINIMAX_API_KEY not set or empty`。

本项目直接生成 profile 后启动共享 octos kernel，正确运行时布局是：

| 内容 | 位置 | 权限 |
| --- | --- | --- |
| 原始 provider 密钥（未加密） | `$HOME/.octos/secrets/<ENV>`（如 `MINIMAX_API_KEY`） | **0600**，目录 **0700** |
| profile | `<core_dir>/profiles/_main.json`，`env_vars.<ENV> = "keychain:"` | **0600** |

`deploy/tools/make_provider_profile.py` 就按这个运行时布局写，并自检
**profile 里没有原始密钥**（只放 `keychain:` 标记）。这个脚本没有加密 secrets 文件，
权限隔离与加密是不同的保证；密钥文件留在宿主私有目录，不进应用包或 Git。
`<core_dir>/secrets` 若由 AI Providers GUI 维护，仍属于另一套 host vault；不要用它
替代 octos CLI keychain，也不要在两处长期保留同一密钥副本。
另外：profile 必须是**完整 envelope**（`id/name/created_at/updated_at/config`），
裸 `{config}` 会被 octos 当作"没有 profile"。core dir 的权威变量是 **`$OCTOS_APP_CORE_DIR`**，
而且**显式设置它会关闭**从 `$HOME/octos-home/.octos` 的自动 profile 迁移
（`crates/kernel/src/dirs.rs:18-56`）。

> 注意区分：凭据交接用的**传输封套**（RSA+AES 密文）只是交付手段，
> **不能**把它或任何 ciphertext 当作 provider 可用的 Key；能用的是解出来的明文 key。

---

## 5. 窗口坐标每次重启会漂移

同一控件从 `(725,532)` 漂到 `(695,470)`。所以每一步都用**当次截图**定位，
不套用上一轮的坐标；也不盲扫坐标。

---

## 6. 进程身份：同名 ≠ 同一个

- `pgrep -f "<关键字>.*<端口>"` 会命中**调用者自己的命令行**
- `setsid cmd &` 的 `$!` 常是 `setsid`/`nohup` **包装进程**，不是真守护进程
- 旧 PID 会被复用，`kill -0` 通过不代表是同一个进程
- 停 Xvfb 会把连在它上面的 X 客户端一起带走（= 变相误杀宿主）

`deploy/start.sh` / `stop.sh` / `health.sh` 因此按
`(pid, starttime, exe, display, port)` 复核身份；宿主没停成时**保留 Xvfb**。
详见 [`DEPENDENCIES.md`](DEPENDENCIES.md) §6.1 与
`evidence/deploy-identity-test.txt`、`evidence/deploy-clean-shell.txt`。
