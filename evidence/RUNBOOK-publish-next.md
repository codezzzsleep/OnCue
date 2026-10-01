# RUNBOOK — 下一版 OnCue 的 hub 发布（为下一版发布准备）

编写方式：**只读源码 + 只读实测**（未执行任何 `hub publish`，未改动 `oncue/bundle/` 与镜像）。
文中标注约定：**【实测】**= 本次在 /tmp 副本上真跑过并看到该输出；**【代码】**= 读 pinned 源码得出的结论（行号给出，未执行）。
hub 源码根：`/root/.cargo/git/checkouts/OctoSense-App-Hub-0f87f6c76fe4766d/0f33211/`（下称 `$HUB_SRC`）。

---

## 0. 现状快照（发布前必须重新核对，别信本文的数字）

| 项 | 值（本次实测时） |
|---|---|
| hub 二进制 | `/tmp/hubbuild/app-hub/target/release/hub`，sha256 `6d7fc89eb46043a1d4b2afea005f5dc6671a3a42e858f8bdf7c48ba8001232ef` |
| 发布脚本 | `/root/oncue-runtime/deploy/publish-local-hub.sh`，sha256 `65255f58442291877691abfa9113a0324042812d5b49d75f23a352952f313af9` |
| 评审脚本 | `/root/oncue-runtime/deploy/oncue-reviewer.sh`，sha256 `9b0087c74c48c24e4f19c54605a182cf6604e61c1555094845080eda052246bf` |
| 镜像目录 | `/root/oncue-runtime/state/hub-mirror/`（`catalog.json` + `artifacts/<id>-<ver>.bundle` + `.pack.json`） |
| 密钥目录 | `/root/oncue-runtime/state/hub-keys/`（`anchor.key/.pub/.cert.hex`、`working.key/.pub`，600） |
| catalog.json | **sequence 6**，6 个条目：oncue-screening-room 0.1.0 / 0.1.1 / 0.2.0 / 0.3.0 / 0.3.1 / 0.4.0（全部 offered），sha256 `d1fc8d07e13cf3f6fb612a5740da67ec927a07498431970f5f2b2d6e210219fb` |
| 当前 bundle | `/root/oncue-runtime/dev/OnCue/oncue/bundle`，manifest version **0.4.0**，与已发布的 0.4.0 artifact **逐字节相同**（`diff -r` 实测 IDENTICAL） |
| repo HEAD | 编写时 `af8534675519787f3b7e93911f44b565e5f2bbd2`；**另一名操作者正在同一 repo 提交**（分析期间 HEAD 从 `4e47c4d` 前进到 `af85346`），HEAD 以发布瞬间为准 |

**勘误**：任务背景说 "catalog.json 当前 sequence 5"——磁盘上实际是 **6**（0.1.0→0.4.0 共 6 条）。下一次成功发布将是 **sequence 7**。发布前用 `hub verify` 打印的 sequence 兜底核对，不要硬编码。

**发布前 30 秒检查单**：

```bash
MIRROR=/root/oncue-runtime/state/hub-mirror
/tmp/hubbuild/app-hub/target/release/hub verify "$MIRROR/catalog.json" \
  --anchor "$(cat /root/oncue-runtime/state/hub-keys/anchor.pub)"
# 预期（实测）：catalog sequence 6 verified, 6 entries   ← 记下这个数，发布后应 +1
cp "$MIRROR/catalog.json" "$MIRROR/catalog.json.bak-seq6"   # 发布前备份（强烈建议）
```

---

## 1. 源码行为定位（file:line 清单）

### 1.1 publish 怎么写 catalog 条目

| 事实 | 位置 |
|---|---|
| `publish` 命令主体（CLI 分发） | `$HUB_SRC/crates/app-hub/src/bin/hub.rs:87-144` |
| 条目构造 `entry_for()` | `$HUB_SRC/crates/app-hub/src/gate.rs:386-410` |
| artifact 相对路径 `artifacts/<app_id>-<version>.bundle` | `gate.rs:400` |
| `source` 字段来自 `--repo` / `--commit` 原样填入 | `gate.rs:406`（结构定义 `index.rs:65-70`） |
| `status` 恒为 `Offered`、`admitted` = 系统当天日期 | `gate.rs:407-408`（日期函数 `remote.rs:48-66`） |
| publisher / publisher_key 来自 `--publisher` 与匹配 id 的 `--publisher-key` | `hub.rs:97, 105-111`（写成 entry：`gate.rs:404-405`） |
| **只能追加，无覆盖**：`catalog.entries.push(entry)` | `hub.rs:137` |
| **sequence 递增**：`catalog.sequence += 1`，`published = today()` | `hub.rs:138-139` |
| catalog 用 working key 重签（签名+锚点证书） | `hub.rs:140` → `signing.rs:50-58` |
|  catalog 写回 `--catalog` 路径（输入输出同一个文件） | `hub.rs:141` |
| bundle 复制到 `--out/artifacts/<id>-<ver>.bundle`，并写 `<artifact>.pack.json` | `hub.rs:114-122`（pack 格式 `pack.rs:16-31`） |
| 成功输出 `published <id> <ver> (catalog sequence N)` | `hub.rs:142` |

### 1.2 重复版本判据

| 事实 | 位置 |
|---|---|
| 判据 = **(app_id, version) 二元组**已在 catalog 中即拒，与内容无关 | `gate.rs:240-248`（拒绝文案 `gate.rs:243-246`："version X of Y is already published; publish a new version"） |
| publish 先跑同一 gate，失败即 `refusing to publish a bundle the gate refused`，**不写任何文件** | `hub.rs:90-94` |
| 附加 continuity 规则：新版本的签名 key_id 必须等于该 app 上一条目的 `publisher` | `gate.rs:249-265` |
| gate 的 `previous` 目录**只在 `--catalog` 路径真实存在时才读** | `bin/hub.rs:250-253` |

### 1.3 sequence / 新鲜度 / 设备侧

| 事实 | 位置 |
|---|---|
| `sequence` 每次 publish / withdraw / remove 都 +1 | `hub.rs:138`、`hub.rs:159`、`hub.rs:195` |
| 设备拒绝更旧 sequence 的 catalog（防回放撤销 withdrawal） | `client.rs:97-104` |
| catalog 超过 14 天（`CATALOG_FRESHNESS_DAYS`）暂停**安装**（不影响运行） | `client.rs:16, 122-130` |
| catalog schema 必须为 1 | `index.rs:168`、`client.rs:93-95` |

### 1.4 stamp / sign / digest / 签名覆盖范围（顺序陷阱的根源）

| 事实 | 位置 |
|---|---|
| bundle digest = blake3 over **除 manifest.json 外所有文件**（排序、路径+NUL+长度+字节） | `app-policy/src/bundle.rs:19-35`（manifest 排除 `bundle.rs:51-53`） |
| `hub stamp` 把该 digest 写进 `manifest.json integrity.bundle_blake3` | `bin/hub.rs:55-65` |
| 清单签名覆盖**整个 manifest（含 `version` 与 `bundle_blake3`）**，签名时先清空旧签名再签 | `app-policy/src/manifest.rs:413-418`、`signing.rs:135-143` |
| gate 校验 digest 相符 + 签名有效（working key 之外还需 `--publisher-key` 注册） | `gate.rs:106-122`、`bin/hub.rs:243-248` |
| catalog 签名覆盖除 `signature`/`key` 外的整个 catalog（canonical JSON） | `index.rs:184-190` |

---

## 2. `hub publish` 各参数作用

用法（`bin/hub.rs:87-144`，与 `bin/hub-usage.txt:9-10, 18-20` 一致）：

```
hub publish <bundle> --catalog <f> --key <f> --anchor-cert <hex>
            --publisher <id> [--repo <url>] [--commit <sha>] [--out <dir>]
            [--publisher-key id=hex] [--reviewer <cmd>] [--reviewed]
```

| 参数 | 作用 | 缺失时 |
|---|---|---|
| `<bundle>` | 待发布 bundle 目录 | 报错 usage |
| `--catalog` | **既读又写**：读旧 catalog 做身份检查，追加条目后写回同一路径 | 报错；**路径不存在且可写时会新建空 catalog（sequence 0→1）并覆盖该路径**（`hub.rs:102`）【代码】 |
| `--key` | hub working 私钥，签 catalog | 报错 |
| `--anchor-cert` | 锚点对 working key 的证书 hex，随 catalog 下发供设备验链 | 报错 |
| `--publisher` | 发布者 id，写入 `entry.publisher`；也是 `--publisher-key` 的匹配键 | 报错 |
| `--publisher-key id=hex` | 发布者公钥（写入 entry，随签名 catalog 下发）；gate 用它验 manifest 签名。可重复多次 | 该 publisher 的 entry `publisher_key` 为空；gate 若无匹配 id 的 key 则拒签【实测】 |
| `--repo` | 写入 `entry.source.repository`，仅透明性用途，安装时不抓取 | 空字符串（允许）【代码】 |
| `--commit` | 写入 `entry.source.commit`，**hub 不验证该 commit 是否存在或包含这些字节** | 空字符串（允许）【代码】 |
| `--out` | artifact 输出根（`--out/artifacts/...`） | 默认 `.`（当前目录） |
| `--reviewer` | 走 `sh -c <cmd>` 执行评审，packet 走 stdin、verdict 从 stdout 解析 | 不评审直接发布 |
| `--reviewed` | 评审给 human-review 时，人工过目后加此 flag 放行 | human-review 拒绝发布【代码】 |

publish 内部顺序（重要）：gate → 复制 artifact → 写 pack.json → 跑 reviewer → push 条目 → sequence+1 → 重签 → 写 catalog（`hub.rs:90-141`）。**reviewer 拒绝时 artifact 已落盘但 catalog 未动**，该版本仍未发布，修完可重跑【代码】。

---

## 3. reviewer 契约（对照 `deploy/oncue-reviewer.sh`）

reviewer 由 `scan()` 以 `sh -c <cmd>` 启动，**packet JSON 全量写 stdin**（`scan.rs:155-187`，spawn 于 `scan.rs:160`）。

### 3.1 stdin：packet 格式（`scan.rs:26-58`，构造 `scan.rs:78-149`）

顶层键（实测 dump：`hub scan --packet`）：`schema`(=1)、`app_id`、`version`、`manifest`、`listing`、`grants`（人话权限清单）、`entry`（`main.splash` 或 `page.card`）、`card_source`（入口文件源码）、`card_data`（`page.data.json` 内容或 null）、`agent_files`（有则含 `tools.json`/`AGENT.md`/skills，空则省略）、`screenshots`（hub CLI 恒为空数组）、`questions`（7 问；带 agent files 时第 8 问插入末问前，`scan.rs:129-134`）。

### 3.2 stdout：verdict 契约

- 一个 JSON 对象 `{"route": "pass"|"human-review"|"reject", "reasons": [<string>...]}`（`scan.rs:60-76`；`deny_unknown_fields`，`reasons` 可省）。
- 允许外包散文：取 stdout 中**最外层第一段 `{...}`**（`scan.rs:178-182`）。
- **退出码必须为 0**（`scan.rs:173-175`）。
- stderr 原样继承到发布者终端（`scan.rs:160`）。
- 任何失败（起不来、读不完、非 0 退出、解析失败、含未知字段）一律回落 `human-review`——**坏掉的评审永远不会变成 pass**（`scan.rs:189-191`）。注释里提到 timeout，但此版本代码无超时实现【代码】。
- publish 中：`reject` → 中止；`human-review` → 中止并提示加 `--reviewed`；`pass` → 继续（`hub.rs:130-135`）。

### 3.3 oncue-reviewer.sh 行为（`deploy/oncue-reviewer.sh`）

`PACKET=$(cat)` 全读 stdin（L5）→ 副本落 `/tmp/oncue-reviewer-packet.json`（L6）→ 逐题答案写 `dev/OnCue/evidence/hub-review-answers.md` 并记录 packet 的 sha256（L7-38）→ stdout 打 `{"route":"pass","reasons":[...7 条...]}`（L40-52）。它是**静态通过型**评审（答案写死在脚本里），换版本一般不须改；但如果新版 capability/界面明显变化，答案文本与 reasons 应同步更新，否则评审记录与事实不符。

---

## 4. 完整发布序列（以 0.4.0 → 0.5.0 为例）

```bash
HUB=/tmp/hubbuild/app-hub/target/release/hub
REPO=/root/oncue-runtime/dev/OnCue
BUNDLE=$REPO/oncue/bundle
KEYS=/root/oncue-runtime/state/hub-keys
MIRROR=/root/oncue-runtime/state/hub-mirror
CATALOG=$MIRROR/catalog.json
PK="oncue.local=$(cat "$KEYS/working.pub")"
```

### 步骤 0 — 准备 bundle（易错，详见 §5）

```bash
cd "$REPO"
# 0.1 若发新版：改 manifest.json 的 "version": "0.4.0" -> "0.5.0"（其余字段不动）
# 0.2 换同版本截图：替换 oncue/bundle/screenshots/*.png，并保证 listing.json 的
#     "screenshots"/"icon" 名字与包内文件一致（gate 强制：至少 1 张截图 + 图标，gate.rs:188-198）
git add -A && git commit -m "0.5.0 ..."        # ★ 先提交，再发布：让 source.commit 真的包含这些字节（见 §6）
git rev-parse HEAD > /tmp/publish-head.txt     # 记录发布时 HEAD
```

### 步骤 1 — stamp（digest 写回 manifest）

```bash
"$HUB" stamp "$BUNDLE"
# 预期（实测同构输出）：打印一个 64 hex 摘要，例如 0ce4962c...
# 之后 manifest.json 的 integrity.bundle_blake3 = 该值
```

### 步骤 2 — sign-manifest（working key 签清单）

```bash
"$HUB" sign-manifest "$BUNDLE" --key "$KEYS/working.key" --key-id oncue.local
# 预期（实测）：signed oncue-screening-room 0.5.0 with oncue.local
```

### 步骤 3 — check（两道门）

```bash
"$HUB" check "$BUNDLE" --publisher-key "$PK"
# 预期（实测）：oncue-screening-room 0.5.0 — PASSED + grants 行，exit 0

"$HUB" check "$BUNDLE" --publisher-key "$PK" --catalog "$CATALOG"
# 预期（实测 0.5.0 场景）：同上 PASSED。
# 若还是 0.4.0：REFUSED [version] "version 0.4.0 ... already published; publish a new version"，exit 1
```

### 步骤 4 — publish

```bash
"$HUB" publish "$BUNDLE" \
  --catalog "$CATALOG" \
  --key "$KEYS/working.key" \
  --anchor-cert "$(cat "$KEYS/anchor-cert.hex")" \
  --publisher oncue.local \
  --publisher-key "$PK" \
  --repo "https://github.com/codezzzsleep/OnCue" \
  --commit "$(cat /tmp/publish-head.txt)" \
  --reviewer /root/oncue-runtime/deploy/oncue-reviewer.sh \
  --out "$MIRROR"
```

预期输出（前两段实测同构；publish 尾行为【代码】因为未实跑）：

```
oncue-screening-room 0.5.0 — PASSED
  grants: capabilities {...}, hosts {}, storage 65536 bytes, agent none
  scan: Pass — <reasons 用 "; " 连接>
published oncue-screening-room 0.5.0 (catalog sequence 7)
```

> 也可以直接用 `/root/oncue-runtime/deploy/publish-local-hub.sh`（它内含等价序列，L26-47），但它把 `--commit` 固定为 `$(cd "$REPO" && git rev-parse HEAD)`（L42）。用脚本前先 `git commit`，否则记录的 commit 不含 bundle（见 §6 的 0.4.0 实例）。脚本 `set -euo pipefail`，任一步失败整体中止。

### 步骤 5 — verify --anchor

```bash
"$HUB" verify "$CATALOG" --anchor "$(cat "$KEYS/anchor.pub")"
# 预期（实测同构，本次为 sequence 6）：catalog sequence 7 verified, 7 entries
```

### 步骤 6 — 核对新条目（发布后 30 秒）

```bash
python3 - <<'EOF'
import json
c=json.load(open('/root/oncue-runtime/state/hub-mirror/catalog.json'))
e=c['entries'][-1]
print('sequence', c['sequence'], '| entries', len(c['entries']))
print('entry:', e['manifest']['id'], e['manifest']['version'])
print('admitted:', e['admitted'], '| publisher:', e['publisher'])
print('source.commit:', e['source']['commit'])
print('digest:', e['manifest']['integrity']['bundle_blake3'])
EOF
# 人工核对：version=0.5.0；admitted=今天；source.commit == /tmp/publish-head.txt；
# digest == 步骤 1 打印值；artifact 文件存在：
ls "$MIRROR/artifacts/oncue-screening-room-0.5.0.bundle" \
   "$MIRROR/artifacts/oncue-screening-room-0.5.0.bundle.pack.json"
```

### 步骤 7 —（如需让设备用到新版）重启 OctoSense

```bash
OCTOSENSE_HUB=$MIRROR OCTOSENSE_HUB_ANCHOR=$(cat "$KEYS/anchor.pub")   # publish 脚本 L49-52 的提示
```
（`deploy/oncue-env.sh:37-38` 已默认导出这两个变量；具体重启方式见 `deploy/start.sh` / README，不属本文范围。）

---

## 5. 版本号 / digest 更新顺序陷阱

根因：digest 覆盖**除 manifest 外所有文件**（`bundle.rs:19-35`），而签名覆盖**含 version 和 digest 的整个 manifest**（`manifest.rs:413-418`）。因此：

**正确顺序（AI1 #122 纠正）：内容改动 → 改 version → stamp → sign-manifest → check → 把最终签名工件（manifest/source/listing）提交 main 并 push → 记录该 commit → `publish --commit <该 commit>` → verify / 留证。**

关键点：`stamp` 与 `sign-manifest` 都会改 `manifest.json`，所以"先 commit 再签"会让 catalog 里的 `source.commit` 指向**签名前的字节**——克隆那个提交复现不出这份签名包。只有**实际签名后的工件**进入对应 Git 提交，克隆该 commit 才能复现同一份包。`publish` 本身不再改 bundle（只复制工件、写 pack、签 catalog），因此 `--commit` 必须取**签名工件所在的那个提交**。

| 操作 | 后果 | 必须的动作 |
|---|---|---|
| stamp 之后又改任何 bundle 文件（换截图、改卡片） | gate 拒：`[refused] digest`【实测】 | 重新 `hub stamp` → `hub sign-manifest` |
| 只改 manifest.json 的 version，不改其他文件 | digest **不变**（manifest 被排除）【实测：stamp 重算值不变】 | 仍须重签（signing_bytes 变了） |
| sign-manifest 之后再改 version（或改其他文件） | gate 拒：`[refused] publisher-signature: the signature from key "oncue.local" does not match the manifest`【实测】 | 重新 stamp（若文件动过）→ 重新 sign-manifest |
| 换 key_id 签新版本 | gate 拒：`[refused] continuity`（与上一条目 publisher 不一致）【代码，`gate.rs:253-259`】 | 用回 `oncue.local`；换 key 是"reviewed change"，要走 §7 |
| 漏带 `--publisher-key` 或 hex 不对 | gate 拒：`publisher key "oncue.local" is not registered with this hub`【实测】 | 公钥从 `hub pubkey "$KEYS/working.key"` 取 |
| `--catalog` 指向**不存在**的文件 | check 静默 PASSED（身份检查被整体跳过）【实测】——这是最隐蔽的坑 | 发布前 `hub verify` 确认 catalog 存在且 sequence 符合预期 |
| publish 的 `--catalog` 路径打错且文件不存在 | 会用**空 catalog（sequence 0→1）覆盖该路径**，历史条目全部消失【代码，`hub.rs:102,137-141`】 | 与上一条同解；另外发布前备份 catalog |
| 忘记 `--out` | artifact 落到当前目录 | 始终显式 `--out "$MIRROR"` |

经验法则：**stamp 和 sign 一旦跑完就冻结 bundle**；此后任何字节变动都从 stamp 重来。签名只在"manifest 内容 + bundle 内容"不变时有效。

---

## 6. 如何确认新条目 `source.commit` 等于当时 HEAD

1. 发布前：`git -C "$REPO" rev-parse HEAD` 存证（步骤 0.2）。
2. 发布后：步骤 6 打印 `source.commit`，与存证字符串比对。
3. **hub 不校验 `--commit`**（`hub.rs:99` 原样传入，`gate.rs:406` 原样写入）——写错也发布成功，只能靠事后核对。`--commit ""` 同样合法。
4. **真实反面教材（实测）**：本镜像 0.4.0 条目的 `source.commit = 47cbbd5...`（0.3.1 提交），而 0.4.0 的提交是 `4e47c4d...`——即发布时 bundle 已是 0.4.0 但尚未提交，`git rev-parse HEAD` 拿到的是父提交。结论：**先把签名后的工件提交并 push，再 `publish --commit` 那个提交**。任何"先 commit 再签"或"先发布后提交"的做法，都会让 catalog 的 `source.commit` 无法定位到可复现的字节（0.4.1 条目就是这个情形：它记的是签名前的 `c1485ba`，签名后的精确字节在同仓库的后续提交里）。
5. 另注意：另一名操作者可能在同一 repo 推进 HEAD（本次分析期间即如此）。发布窗口内若 HEAD 变化，以 `/tmp/publish-head.txt` 为准核对，并在证据里记录两个值。

---

## 7. 需要刷新已发布版本的溯源时（hub 不允许覆盖）

publish 只能**追加新条目**（`hub.rs:137`）；(app_id, version) 已存在即拒（`gate.rs:242-246`）。合规做法按情节二选一：

**A. 正常情况——发新版 + 撤下旧版**（首选）

```bash
# 发 0.5.0（§4 全流程）后，把 0.4.0 撤下：
"$HUB" withdraw oncue-screening-room --version 0.4.0 \
  --reason "superseded by 0.5.0" \
  --catalog "$CATALOG" --key "$KEYS/working.key" \
  --anchor-cert "$(cat "$KEYS/anchor-cert.hex")"
# 预期【代码】：withdrew oncue-screening-room 0.4.0: superseded by 0.5.0 (catalog sequence 8)
```

withdraw 保留条目、只改 `status = Withdrawn(reason)`（`hub.rs:145-165`）；设备侧已安装的该版本会停止运行（`client.rs:278-293`）。**withdraw 也 +1 sequence 并重签**。旧条目及其溯源记录仍在 catalog 里，可追溯。

**B. "本就不该发布"（发错版本、测试发布、溯源写错且必须原地纠正）**

```bash
"$HUB" remove oncue-screening-room --version 0.4.0 \
  --catalog "$CATALOG" --key "$KEYS/working.key" \
  --anchor-cert "$(cat "$KEYS/anchor-cert.hex")" \
  --out "$MIRROR"          # ★ 不传则 artifact 清理静默失败（默认 "."）
# 预期【代码】：removed oncue-screening-room 0.4.0 + "N of M entries remain (catalog sequence 8)"
# 之后同一版本号可重新发布（重复判据只查现存条目）
```

remove 会删条目、artifact 目录、`.pack.json` 和 `index/<id>-<ver>.json`（`hub.rs:188-194`，删除失败被 `let _ =` 吞掉），并 +1 sequence 重签。注意：(a) remove+重发 = 两次 sequence 递增；(b) 已安装该版本的设备不会回滚，`may_run` 会以"catalog 未提供该版本"拒绝运行（`client.rs:278-293`）；(c) 不带 `--version` 会删该 app 的**全部**条目。能 withdraw 就别 remove。

---

## 8. 典型报错与处置

| 症状（stderr/stdout） | 含义 | 处置 | 依据 |
|---|---|---|---|
| `hub: the bundle was refused` + `[refused] digest: the bundle hashes to X, the manifest claims Y` | stamp 后文件又变 | 重 stamp → 重 sign-manifest | 实测（`gate.rs:106-111`） |
| `[refused] publisher-signature: the signature from key "oncue.local" does not match the manifest` | 签名后 manifest 被改（典型：改 version） | 重新 sign-manifest（文件动过则先 stamp） | 实测（`gate.rs:112-116`） |
| `[refused] publisher-signature: publisher key "oncue.local" is not registered with this hub` | 漏 `--publisher-key` 或 hex 错 | 补 `--publisher-key oncue.local=$(cat "$KEYS/working.pub")` | 实测（`signing.rs:121-131`） |
| `[refused] version: version 0.4.0 of oncue-screening-room is already published; publish a new version` | 同 (id,version) 重发 | 发新版（bump version 后重跑 §4）；或 §7-B remove 后重发 | 实测（check 层）；publish 层措辞为 `hub: refusing to publish a bundle the gate refused`【代码】 |
| `[refused] continuity: ... was published by "oncue.local"; this version is signed by ...` | 换了签名 key_id | 用回 oncue.local；确需换钥走 §7-B | 代码（`gate.rs:249-265`） |
| `[refused] listing: no screenshots / no icon / <asset> is named by the listing but is not in the bundle` | 截图/图标与 listing.json 不一致 | 修 bundle 或 listing，重新 stamp+sign | 代码（`gate.rs:179-201`） |
| `hub: the scan asks for human review; publish again with --reviewed once a person has looked` | reviewer 输出 human-review（含 reviewer 故障回落） | 人工看 packet（`/tmp/oncue-reviewer-packet.json`）后重跑并加 `--reviewed` | 代码（`hub.rs:133-135`、`scan.rs:189-191`） |
| `hub: the scan rejected this bundle` | reviewer 输出 reject | 按 reasons 改 bundle 后从 stamp 重跑 | 代码（`hub.rs:132`） |
| `hub verify` 失败：`the catalog's signature does not match its contents` / `the anchor did not certify this working key` | catalog 被手改过 / anchor 与 working key 不配对 | 恢复备份（发布前 `catalog.json.bak-seqN`）；确认用 `anchor.pub` | 代码（`signing.rs:79-95`） |
| check 静默 PASSED 但其实版本已发布过 | `--catalog` 路径不存在，身份检查被跳过 | 发布前 `hub verify` 兜底；确认 `--catalog` 路径拼写 | 实测 |
| 发布后 `hub verify` 的 entries 没变多 / 镜像历史消失 | `--catalog` 路径写错（不存在时 publish 新建空 catalog 覆盖） | 从备份恢复；重发；映射一个固定的 `$CATALOG` 变量 | 代码（`hub.rs:102`） |
| 设备侧 `installs pause`（安装被暂停） | catalog `published` 超过 14 天 | 重新发布任意版本刷新 `published`（publish 必设 `today()`） | 代码（`client.rs:16,122-130`、`hub.rs:139`） |

---

## 9. 本次分析实测记录（可复现）

执行者仅使用只读命令与 `/tmp` 副本；未执行 `hub publish`，未修改 `oncue/bundle/`、镜像与密钥。

```bash
HUB=/tmp/hubbuild/app-hub/target/release/hub
KEYS=/root/oncue-runtime/state/hub-keys
CAT=/root/oncue-runtime/state/hub-mirror/catalog.json
PK="oncue.local=$(cat "$KEYS/working.pub")"

# [实测 1] 现 catalog 验签
"$HUB" verify "$CAT" --anchor "$(cat "$KEYS/anchor.pub")"
# → catalog sequence 6 verified, 6 entries

# [实测 2] 副本上同版本 0.4.0 + catalog  attached → 重复版本拒绝
cp -a /root/oncue-runtime/dev/OnCue/oncue/bundle /tmp/rb-demo/bundle
"$HUB" check /tmp/rb-demo/bundle --publisher-key "$PK" --catalog "$CAT"
# → REFUSED [version] ... exit 1（hub: the bundle was refused）

# [实测 3] 去掉 --catalog → PASSED（身份检查被跳过）
# [实测 4] --catalog 指向不存在文件 → 同样 PASSED

# [实测 5] stamp 后追加一行 main.splash → REFUSED [digest]
# [实测 6] version 改 0.5.0 + stamp + sign-manifest → check --catalog → PASSED
# [实测 7] 签名后再改 version 0.5.0→0.5.1 → REFUSED [publisher-signature]
# [实测 8] hub scan --packet → 7 questions；packet 顶层键见 §3.1
# [实测 9] reviewer 打 {"route":"pass",...} → 打印 verdict，exit 0
# [实测 10] reviewer exit 3 → {"route":"human-review", reasons:["the reviewer exited with exit status: 3"]}
# [实测 11] reviewer 散文包裹 reject → 解析为 reject，exit 1（hub: rejected）
# [实测 12] verdict 带未知字段 extra → human-review（did not parse: unknown field `extra`）
# [实测 13] 不带 --publisher-key 跑 scan（manifest 已签）→ REFUSED [publisher-signature: not registered]
# [实测 14] diff -r dev bundle vs artifacts/oncue-screening-room-0.4.0.bundle → IDENTICAL
# [实测 15] catalog 0.4.0 条目 source.commit=47cbbd5 ≠ 当时 HEAD 4e47c4d（0.4.0 提交本身）
```

未执行（仅代码推断）：publish 全流程落盘、`--reviewed` 放行、withdraw、remove、sequence 递增后的设备行为。执行前按 §0 核对 catalog sequence 与 HEAD。

---

## 10. 一页速查

```
改内容 → 改 version → git commit → hub stamp → hub sign-manifest
      → hub check (--publisher-key) → hub check (--publisher-key --catalog)
      → 备份 catalog.json → hub publish (--catalog/--key/--anchor-cert/--publisher/
         --publisher-key/--repo/--commit HEAD/--reviewer/--out)
      → hub verify --anchor → 核对末条目的 version/admitted/source.commit==HEAD/digest
冻结纪律：stamp/sign 之后不动 bundle；动就从 stamp 重来。
--catalog 路径必须真实存在，否则身份检查静默跳过；publish 甚至会用空 catalog 覆盖它。
已发布版本不能覆盖：withdraw（保留记录）优先，remove（删条目释放版本号）仅用于本就不该发的。
```
