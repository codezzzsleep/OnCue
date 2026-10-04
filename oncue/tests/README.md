# OnCue 真实 OctoScript 受控测试

8 套共 146 项断言在真实 card-host OctoScript VM 中执行，宿主回调受控注入。历史运行与当前发布包源码哈希一致（`4b2fd02f…`），[原始 run 与逐条结果](<../../evidence/checkpoint-0.4.7-recovered/README.md>)已恢复，可用下方 checker 逐套只读复核。

Python 只负责生成探针、字节校验与结果检查，不移植生产算法；探针内生产函数逐字节保留（65 个），90 秒与 1.4 秒定时器为真实计时。

## 套件与覆盖

| 套件 | 断言 | 覆盖 |
| --- | --- | --- |
| parser | 30 | 七节协议、包装/行末分隔、歧义混合拒绝、无分隔符标记切分 |
| pagination | 15 | 字符守恒、组合字符/emoji/CRLF、长文本跨页 |
| retry | 8 | 格式重试一次、停止/编辑/新请求隔离、服务错误不重试 |
| deadline | 6 | 完整 90 秒期限（含 session 与重试），超时实测 90.0476 秒 |
| playback | 18 | 1.4 秒定时器、暂停/续播/重播、切路线旧计时器隔离 |
| storage | 14 | 真实 jail 写读、空白不覆盖、三份文件字节哈希 |
| grounding | 51 | 原文摘录、数字/编号核查、承诺词门禁（明确不证明语义） |
| envelope | 4 | `data:nil` 畸形回调不抛错、不发布结果 |

## 离线基础设施自检

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s oncue/tests -p 'selftest_*.py' -v
```

91 项（11 生成器/checker + 28 验收工具 + 51 helper），不连宿主。CI 跑同一套，不运行 VM 断言。

## 评审复跑（VM 断言）

前置：card-host 二进制（App Hub `0f332112` 构建）、Python 3.9+、独立 X display（如 `:101`，与宿主分离）。从 `/root/hackthon` 操作：

```bash
WORK="$(mktemp -d /tmp/oncue-octoscript-probe.XXXXXX)"
for SUITE in parser pagination retry deadline playback storage grounding envelope; do
  PYTHONDONTWRITEBYTECODE=1 python3 OnCue/oncue/tests/generate_probe.py --workdir "$WORK" --suite "$SUITE" || exit $?
done
. /root/hackthon/refs/octo-env.sh
: "${DISPLAY:?独立 display}"
```

每次只跑一个 suite（串行，端口可复用；`envelope` 放最后）：

```bash
SUITE=parser; PORT=8197; RUN="$WORK/$SUITE"; WAIT=15
[ "$SUITE" = deadline ] && WAIT=105
[ "$SUITE" = playback ] && WAIT=25
python3 /root/hackthon/refs/OctoScript-App-Design-Flow/tools/octo run \
  "$RUN/bundle" --port "$PORT" --hidden --detach --timeout 20 --app-data "$RUN/app-data" \
&& PYTHONDONTWRITEBYTECODE=1 python3 OnCue/oncue/tests/check_result.py \
  --run-dir "$RUN" --wait-seconds "$WAIT" \
  --current-source /root/hackthon/OnCue/oncue/bundle/main.splash
TEST=$?
curl --fail --silent --show-error "http://127.0.0.1:$PORT/quit"
echo "suite=$SUITE test_exit=$TEST"
```

产物：`$WORK/<suite>/` 下 `bundle/`、`provenance.json`、生产快照、`app-data/oncue-probe-<suite>/probe-result.json`。`complete:true` 且全部断言 PASS 才算通过；storage 套 checker 额外逐字节复核三份真实落盘文件。源码改动后用新的 `WORK` 重新生成，`--current-source` 防止旧快照冒充新结果。
