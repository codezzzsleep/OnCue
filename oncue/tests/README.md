# 测试说明

仓库里有三种测试。

| 测试 | 测什么 | 怎么跑 | 数量 |
| --- | --- | --- | --- |
| 逻辑测试 | `main.splash` 里的函数 | card-host 的脚本虚拟机，本地运行 | 8 套 260 项 |
| 工具单元测试 | 测试包生成器、结果检查器、实机验收脚本 | Python，CI 在相关路径变更时运行 | 99 项 |
| 实机验收 | 应用在 Rinx 里的完整流程 | 脚本驱动一个正在运行的 Rinx | 4 种模式 |

CI 只跑第二种，不运行应用的代码。

## 逻辑测试

`generate_probe.py` 把 `main.splash` 的 120 个函数原样复制进一个测试包，加上测试脚本 `probe_harness.splash` 和测试数据 `fixtures.json`。测试包在 card-host 里运行，宿主服务的返回值由测试脚本模拟。超时和播放用的是真实计时，deadline 一套要等 90 多秒。

各套的内容见[验证记录](../VERIFICATION.md)。最近一次的结果在 [evidence/logic-tests](../../evidence/logic-tests/README.md)。

### 重跑

需要：按 OctoScript-App-Design-Flow 的 QUICKSTART 构建好 `hub` 和 `card-host`，`tools/octo doctor` 通过；Python 3.9 以上；一个 X display。

```bash
export OCTO=/path/to/OctoScript-App-Design-Flow/tools/octo
WORK="$(mktemp -d)"
for SUITE in parser pagination retry deadline playback storage grounding envelope; do
  python3 oncue/tests/generate_probe.py --workdir "$WORK" --suite "$SUITE" || exit $?
done
```

一次跑一套，`envelope` 放最后：

```bash
SUITE=parser; PORT=8197; RUN="$WORK/$SUITE"; WAIT=15
[ "$SUITE" = deadline ] && WAIT=105
[ "$SUITE" = playback ] && WAIT=25
python3 "$OCTO" run "$RUN/bundle" --port "$PORT" --hidden --detach --timeout 20 --app-data "$RUN/app-data" \
&& python3 oncue/tests/check_result.py --run-dir "$RUN" --wait-seconds "$WAIT" \
     --current-source bundle/main.splash
echo "suite=$SUITE exit=$?"
curl --fail --silent --show-error "http://127.0.0.1:$PORT/quit"
```

每套输出 `PASS: N assertions` 才算通过。`--current-source` 用来确认结果对应的是当前源码。改了 `main.splash` 之后要用新的 `WORK` 目录重新生成。

## 工具单元测试

```sh
python3 -m unittest discover -s oncue/tests -p 'selftest_*.py' -v
```

99 项：生成器和检查器 12 项，实机验收脚本 35 项，底层工具 52 项。不需要宿主和网络。

## 实机验收

`oncue/tools/native_acceptance.py` 驱动一个已经在运行的 Rinx：导入应用包、授权、按模式执行操作、读取界面文字核对、保存截图和记录。它会关闭当前打开的小程序；routes/playback会点击一次生成（应用最多修复一次），draft/reopen读取房间并覆盖所选测试槽，不调用模型。每一类操作都需开关明确允许。四种模式不覆盖真实R1修订，不能把通过记录外推为全部功能验收。

```sh
python3 oncue/tools/native_acceptance.py \
  --port 8771 --out /path/to/new-output-dir \
  --bundle "$DEV_ROOT/bundle" --release-bundle bundle --hub "$OCTO_HUB" \
  --account '@you:matrix.rinx.chat' --data-dir /path/to/rinx-data \
  --room '!yourRoomId:matrix.rinx.chat' \
  --host-binary /path/to/octosense \
  --display :99 --xauthority /path/to/xauthority \
  --mode routes --allow-import --allow-real-turn --trial '那我们中午出发、当天回来，先确认预算可以吗？'
```

| 模式 | 做什么 | 需要的开关 |
| --- | --- | --- |
| `routes` | 读取房间，试映一次，读完三种说法和相关原文 | `--allow-import --allow-real-turn --trial` |
| `playback` | 同上，再检查播放、暂停、切换路线 | `--allow-import --allow-real-turn --trial` |
| `draft` | 载入房间、保存草稿 A/B 并独立比对文件 | `--allow-import --allow-room-read --allow-draft-write` |
| `reopen` | 关闭、重新导入并载入同一房间后恢复主稿 | `--allow-import --allow-room-read --allow-draft-write` |

脚本靠界面上的状态文案判断成功和失败。改了 `main.splash` 里的文案，要同步改 `native_acceptance.py` 和 `selftest_native_acceptance.py`。

playback计时检查从确认的「重播0/N」开始，播放/暂停只点击当前视口内的按钮，不在计时中滚动寻找。观察不到足够推进仍失败，不把未判定记成通过。


`native_bridge.py`、`rinx_session.py`、`collect_native_reading.py` 是它用到的底层工具。`prepare_dev_bundle.py` 生成未签名副本，`stamp_bundle.py` 计算包摘要。
