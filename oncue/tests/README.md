# OnCue 真实 OctoScript 受控探针

这些文件是测试基础设施，不属于发布包。**历史 0.4.6 的 49 项受控断言已运行通过**，见[0.4.6检查点](<../../evidence/submission/CHECKPOINT-0.4.6.md>)和[归档结果](<../../evidence/checkpoint-0.4.6/native/>)，不覆盖下述当前扩充。

**本轮聚焦扩充仅做 Python 基础设施自检，未启动 card-host / display / Rinx，未生成或更改归档证据。** 当前 8 套共 138 个运行时断言：保留 parser25 / pagination14 / retry8 / deadline6，新增 playback18 / storage14 / grounding49 / envelope4。交给主线程按当前生产字节重新生成并串行实跑；`envelope` 的恶意 nil 数据可能触发生产错误，必须如实 FAIL，不能把这一套的失败豁免后宣称全通过。

宿主回调为受控注入，不代表真实模型输出质量或 Rinx 全链路已验收。Python 仅负责打包、字节校验、等待与结果检查，**没有移植生产 parser、分页、重试、播放、存储或 grounding 算法到 Python**。

## 组成与边界

- [generate_probe.py](<generate_probe.py>)：每次读取**当前工作树**的 [生产入口](<../bundle/main.splash>)，抽取所有 `fn cue_*` 的精确文本、行号、SHA256；生成完整生产页面，保留真实 `ui` 依赖。
- [fixtures.json](<fixtures.json>)：可审阅的字面量输入、明确预期、必需断言 ID；不是模型输出证据。
- [probe_harness.splash](<probe_harness.splash>)：运行在真实 card-host OctoScript 中的断言与受控回调。
- [check_result.py](<check_result.py>)：检查 jail JSON、完成状态、全部断言 ID、生产与 harness/fixtures 哈希；失败/缺项/旧源码不冒充通过。
- [selftest_infrastructure.py](<selftest_infrastructure.py>)：仅对生成器和 checker 做不写盘的自检，不测试应用运行时行为。

生成器的唯一页面改动：

1. 在生产状态声明之后、生产函数之前插入 `probe_*` harness、fixture 常量，以及只在探针内遮蔽的 `let host = {request: ...}`。
2. 把已知的 `start_timeout(0.05, fn(){ cue_show_demo() cue_refresh_takes() })` 初始化替换为 `start_timeout(0.20, fn(){ probe_boot() })`，避免默认样例/历史存储干扰。
3. 所有生产函数，包括 `cue_deadline` 内 **90.0 秒**与 `cue_play_pulse` 内 **1.4 秒**定时器，保持逐字节一致。生成后再次抽取逐一比较；初始化结构、必需生产函数或 harness 调用清单改变则失败，要求显式审查，不猜位置。
4. 生成器拒绝 harness 遮蔽 `fs` / `ui` / `start_timeout` / `time_now`；provenance 写明真实 jail、非语义事实验证，以及 storage 的三份 UTF-8 原始夹具哈希。

probe manifest 改为唯一 `oncue-probe-<suite>` id，仅申请 `storage`，无 network、无 agent、无签名。fake host 只**记录**服务调用并保存回调，不转发到 native host；意外服务也只记录为失败。没有 Matrix 请求被发出，没有真实模型被启动。原始图标/截图复制仅为 gate 入场，**不是本次探针运行证据**。

`fs`、字符串/数组、`ui`、`start_timeout`、`time_now` 均是真实运行时 API；不替换生产函数、不伪造 UI、不缩短 90 秒。API 依据为 [SCRIPT-API](<https://github.com/OctoSense-org/OctoScript-App-Design-Flow/blob/caa5d3648be9289f11056c386a645038af14e5a5/docs/SCRIPT-API.md#L96-L147>)（若从 OnCue 仓库单独浏览，该跨工作区链接可能不可用）。

## 覆盖与契约

### `parser`（25 个断言，保留原断言）

- 标准七块、首尾 wrapper 七块、单侧 wrapper、CRLF、行末贴附 `@@@`（含 wrapper）。
- 分隔行空白、内部空行保留、内部空块拒绝、六/八块拒绝、全空拒绝、多重 wrapper 拒绝。
- 正文中间 `@@@` 保留；标准七块语法成立时，正文行末 `@@@` 不应被宽松解析误切。
- 歧义混合分隔：原本六块的某一正文行末 `@@@`，不能被拿来凑成七块。
- 通过生产 `cue_accept_reply` 写入 summary/routes，检查七块标记/对应顺序；生产对白拼接、建议台词、草稿选择、摘要分页均精确比对。
- 保留已有摘录逐字/改写与重复拒绝、未见价格与越界编号检查；更细的边界另见 `grounding`。

**安全契约说明**：纯标准七块优先；纯行末贴附七块是兼容格式。混合分隔若必须把正文尾标当边界才能凑满七块，fixture 要求拒绝。这是显式回归契约，不是声称可以从任意文本推知模型原意。若产品另定混合语法，先调整契约并记录，不偷偷放宽断言。

### `pagination`（14 个断言）

- 空串、16/17 ASCII、9 中文字的精确短例边界。
- 换行、首换行、CRLF 边界；组合音标、ZWJ 家庭 emoji、肤色修饰、连续旗帜对、Hangul Jamo。
- 每例所有页重拼必须与原文逐字符一致，非空原文不产生空页，指定字素簇完整出现在同一页。
- 生产消息/摘要阅读器上一页、下一页上下限与内容保全。

不在 Python 中复制视觉宽度算法；不声称上述断言证明字体排版高度或完整 UAX #29。视觉布局仍由主线程实机查看。

### `retry`（8 个断言）

使用真实 `cue_rehearse → session.open 回调 → cue_start_turn → cue_accept_reply`，仅宿主回复受控：

- 第一次格式异常、第二次正常：只发两次 turn、prompt 相同、revision 不变、输出正确。
- 两次格式异常：停止等待，空结果，提示手动重试，不第三次请求。
- 第二次等待中 stop / edit：revision 作废，调用 interrupt，迟到正常回复不覆盖状态。
- 旧请求的迟回调不覆盖新请求已完成的结果。
- 完成后的重复回复不覆盖（额外防御测试；正常宿主原则上一次回调）。
- `is_ok:false` 的**宿主服务错误**当前不做格式重试；与“格式异常”区分，单独固定现有行为。
- 所有 fake host 服务都在预期只读排练 allowlist 内。

普通 retry 用例在同一真实 timer 回合中显式交付保存的回调，无网络随机性。它验证应用状态机，而非真实宿主调度/模型自然输出。

### `deadline`（6 个断言，完整约 93 秒）

- t=0：真实 `cue_rehearse` 开启生产 90 秒期限。
- t=5：交付 session.open，证明 session 等待也包含在预算内。
- t=80：第一次 turn 回复格式异常，生产函数启动第二次 turn，仍用原 revision。
- 真实生产 t≈90 定时器应停止 busy、递增 revision、interrupt、清空结果。
- 每 0.1 秒只**观察** busy，记录 `time_now`；91.5 秒核对，容差 89.5–91.5 秒，报告原始时长。
- t=92：交付第二次正常但迟到的回复；t=93：确认不覆盖超时状态并完成。

**没有额外开启一个用于结束请求的期限，没有重置/快进生产时钟。** 5/80/91.5/92/93 秒都是夹具交付/观察用 timer。collector 的 105 秒只是外部等待结果的上限，不影响应用状态。若生产在重试时偷偷另开 90 秒，本测试约 91.5 秒就明确失败，不会等待额外 90 秒掩盖问题。

### `playback`（18 个断言，约 6.8 秒；collector 建议 25 秒）

- 无路线空态、非法路线索引不改变播放状态、选中路线从零句隐藏开始。
- 播放立即第一句，暂停保留进度且 epoch 作废；等待 1.8 秒核对真实已排队的旧 timer 不推进。
- 续播从当前进度走下一句；真实生产 1.4 秒 timer 再推进一句。
- “下一句”暂停、逐句上限、完整正文/建议/分页重拼精确一致；重播回零。
- 切 A→B 清零并隔离 epoch；特意在 **B 正在播放时**调用 A 的旧 `cue_play_pulse(epoch)`，避免仅靠 `!playing` 通过。再等待真实 timer，B 只能推进一次。
- 真实 timer 播完自动暂停；终点再播放会从第一句重来。无 host 服务调用。

使用与按钮相同的生产处理函数、真实 UI 句柄和计时器，不冒充坐标点击、视觉布局或宿主端到端验证。观察有 0.4 秒调度余量；严重事件循环延迟会诚实失败，应检查日志/时间，不靠加速或手工改 count 伪造通过。

### `storage`（14 个断言 + checker 三份真实文件字节核对）

- **`fs` 是 card-host 真正的应用 jail 文件 API，不是内存 mock，不是 fake host。** 生产 `cue_save_text` 实际写入、exists 与回读。只用本次 `oncue-probe-storage` 的全新 jail；已有同名文件时先失败且不覆盖，使用新 `WORK` 重跑，不删除历史证据。
- 无路线时保存草稿/A/B；多行、首尾空格、空行、TAB、组合音标、ZWJ/肤色/旗帜 emoji 保存/回读/恢复精确一致。
- 空内容恢复不覆盖编辑框；全空白文本既不创建文件，也不覆盖已有草稿/A/B。
- 清空**内存中的** A/B 后生产 refresh 从真实文件读取；无路线 A/B 阅读、分页边界、取 A/取 B 与草稿内容准确。
- 运行完成保留三份文件；checker 从真实 jail 读取 bytes 并与生成时的 UTF-8 夹具 SHA256 逐一比对。仅 Splash 自报 PASS 不能绕过这一外部字节检查。

**不是进程关闭/重启测试，不是 Rinx 跨账号隔离测试，也不覆盖磁盘满/宿主拒绝写盘。** 本套仅覆盖生产保存/回读/刷新/恢复处理函数；重启与账号边界仍须主线程验收。

### `grounding`（49 个断言）

- `cue_source_excerpt`：合法/重排/CRLF 选择、原 body 多行空格 emoji 全保留；重复、零/负/越界/前导零、改写、同一行多个编号、空白/内部空行、五个编号都拒绝。
- **当前实现允许 1–4 个编号**，prompt 请求 2–4；单编号接受是明确的生产现状断言，不声称 prompt 与代码完全一致。
- `cue_numeric_tokens` / `cue_numbers_grounded`：ASCII 连续数字 token 精确匹配，不接受数字子串或额外前导零；授权原文、用户草稿和消息编号中的数字都在 allowed 集。
- 显式记录限制：同数字换单位/虚构支付也可通过；草稿的 77 与编号 5 不能因此称事实；`500.9` 被当成两个已有 token、负号不校验、全角/中文数字不在 ASCII token 检查范围。**通过只意味着当前有限检查的布尔值符合预期，不代表内容真实/安全。**
- `cue_references_valid`：`#` 后只读 ASCII 数字并检查编号范围；允许重复和普通后缀；无 `#` 文本不被语义核验，`#2.9` 仅检查 `#2`；裸 `#`、`##2`、负号/全角/前导零/越界拒绝。
- 七块生产协议层串联验证：合法接受，摘录重复/错号/改写、数值/引用非法都拒绝；另有**无数字却声称全员同意/已订票仍通过**的局限性用例。

绝不声称任意事实语义检验、群体共识验证、模型无幻觉或真实来源房间授权已被本套证明。

### `envelope`（4 个断言；独立负向健壮性套）

真实 `cue_rehearse → session.open → turn.start` 后，通过保存的生产 callback 交付 `{is_ok: true, data: nil, error: ""}`。仅 harness 用 `try/catch` 记录生产异常，使完整结果仍能落盘；**没有对生产函数加 guard、改数据或吞成 PASS**。

`envelope.nil_data_handled_without_runtime_error` 要求真实调用无运行时异常，并已退出 busy 或确实启动唯一格式重试，不能把无异常但搁置请求算妥善处理。当前生产直接读取 `reply.data.text`，静态预期可能 FAIL；实际结论必须看 OctoScript。异常时该断言为 `false`，checker 返回 1，不提供 XFAIL/skip/allow-failure。其余断言记录正常开回合、未发布路线和 host allowlist；记录后停止受控等待。若运行时错误无法被该 catch 捕获，会缺完成结果，checker 应为 INCOMPLETE 而非 PASS。

## 重跑命令（当前扩充尚未执行运行时）

从工作区 `/root/hackthon` 操作；使用**主线程自行管理、已存在且与宿主分离**的 display，例如 `:101`。不要使用宿主 display，不读取其授权文件，不启动/重建宿主，不安装工具。

```bash
# 无 display 的基础设施自检；不会生成 probe，也不写 __pycache__。
PYTHONDONTWRITEBYTECODE=1 python3 OnCue/oncue/tests/selftest_infrastructure.py

# 新目录可重跑；生成器拒绝覆盖旧 run，也拒绝写进 OnCue 仓库。
WORK="$(mktemp -d /tmp/oncue-octoscript-probe.XXXXXX)"
printf 'Probe workspace: %s\n' "$WORK"
for SUITE in parser pagination retry deadline playback storage grounding envelope; do
  PYTHONDONTWRITEBYTECODE=1 python3 OnCue/oncue/tests/generate_probe.py \
    --workdir "${WORK:?}" --suite "$SUITE" || exit $?
done

# 使用现有二进制，不 install / build。
. /root/hackthon/refs/octo-env.sh
# DISPLAY 应由主线程预先设置为自己管理的独立 display。
: "${DISPLAY:?先设置主线程专用的独立 display}"
# 不沿用生产宿主 XAUTHORITY；若独立 display 有自己的授权，由主线程提供。
```

**每次只运行一个 suite**，可重复使用已释放的端口。推荐把以下整段作为一次 managed background job 运行，记录其 job id；不要再额外 `&`，不要并行启动多个 card-host。建议将 `envelope` 放最后，它的真实失败不能盖掉其他套结果，也不能被忽略为总通过：

```bash
SUITE=parser                    # 再依次 pagination retry deadline playback storage grounding envelope
PORT=8197                       # 先确认空闲，不触碰其它实例
RUN="${WORK:?}/${SUITE:?}"
WAIT_SECONDS=15
if [ "$SUITE" = deadline ]; then WAIT_SECONDS=105; fi
if [ "$SUITE" = playback ]; then WAIT_SECONDS=25; fi

# octo --detach 自己核对端口所属 PID；失败时不会 quit 其它占用者。
python3 /root/hackthon/refs/OctoScript-App-Design-Flow/tools/octo run \
  "${RUN:?}/bundle" --port "$PORT" --hidden --detach --timeout 20 \
  --app-data "${RUN:?}/app-data"
START_STATUS=$?
if [ "$START_STATUS" -eq 0 ]; then
  PYTHONDONTWRITEBYTECODE=1 python3 OnCue/oncue/tests/check_result.py \
    --run-dir "${RUN:?}" --wait-seconds "$WAIT_SECONDS" \
    --current-source /root/hackthon/OnCue/oncue/bundle/main.splash
  TEST_STATUS=$?
  # 只在本段成功启动自己的实例后退出它，不使用 pkill。
  curl --fail --silent --show-error "http://127.0.0.1:${PORT}/quit"
  QUIT_STATUS=$?
  printf '\n[probe exit code: %s] [quit exit code: %s]\n' "$TEST_STATUS" "$QUIT_STATUS"
  if [ "$TEST_STATUS" -ne 0 ]; then exit "$TEST_STATUS"; fi
  exit "$QUIT_STATUS"
else
  printf '\n[start exit code: %s]\n' "$START_STATUS"
  exit "$START_STATUS"
fi
```

运行时 jail 路径由生成的 provenance 给出，规则为：

```text
$WORK/<suite>/
  bundle/                          # 一次性、未签名、受控 probe 包
  provenance.json                  # 精确 source/fixtures/harness 哈希、生产函数行号与哈希
  production-main.splash           # 生成时生产源码完整快照
  production-functions.splash      # 从快照精确抽取的所有生产函数
  app-data/card-host.log            # tools/octo --detach 输出
  app-data/oncue-probe-<suite>/probe-result.json
```

结果 `complete:true` 且全部断言 PASS 才算该 suite 通过；只有 `admitted` / 首帧 / gate 通过不算逻辑通过。
源码有任何改动后请用新的 `WORK` 重新生成；`--current-source` 防止把旧快照结果归到新候选。
若未出现结果，先查看日志里的 parse/runtime 错误和 `complete:false` checkpoint，不以 timeout 代替测试结论。历史四组结果见检查点归档；当前扩充的词法/计时/UI/fs 行为尚需主线程首次实跑确认。storage 同 jail 下另有 `draft.txt` / `take-a.txt` / `take-b.txt`，必须是真实文件，checker 会逐字节复核。

## 基础设施自检记录（与应用原生测试分开）

执行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 OnCue/oncue/tests/selftest_infrastructure.py
```

本轮结果：`Ran 11 tests ... OK`，退出码 0。覆盖八套生成后函数字节一致、原90秒/1.4秒保留、新增ID清单完整、API缺失与基础API遮蔽拒绝、storage真实文件字节checker的内存单测、envelope失败不豁免，以及新provenance/播放时间窗检查。**这些 Python 单测的合成结果只在内存中用于测 checker，不是运行时证据，不计入 138 个 OctoScript 断言。**

源码旧风险与 fixture 对应见 [RISK-REVIEW.md](<RISK-REVIEW.md>)，仍保留修复前历史状态，未更新成当前结论。本轮只写 tests 内文件，未改 bundle/其他目录/归档证据，未构建/启动 display 或宿主，未访问聊天室或秘密，未操作 Git 提交或外部 Issue。
