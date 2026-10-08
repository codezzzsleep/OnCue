# 逻辑测试结果

2026-10-08，0.5.0同一生产源码的 **8套257项断言全部通过**。入口SHA-256：`015d7666fd58152955cb8931f54b894f5fa62789f033a8483a2bc2ce10bd43f9`；120个生产函数原样进入真实card-host。

| 套件 | 断言 | 结果 |
|---|---:|---|
| parser | 39 | [结果](parser/app-data/oncue-probe-parser/probe-result.json) |
| pagination | 15 | [结果](pagination/app-data/oncue-probe-pagination/probe-result.json) |
| retry | 38 | [结果](retry/app-data/oncue-probe-retry/probe-result.json) |
| deadline | 6 | [结果](deadline/app-data/oncue-probe-deadline/probe-result.json) |
| playback | 18 | [结果](playback/app-data/oncue-probe-playback/probe-result.json) |
| storage | 56 | [结果](storage/app-data/oncue-probe-storage/probe-result.json) |
| grounding | 72 | [结果](grounding/app-data/oncue-probe-grounding/probe-result.json) |
| envelope | 13 | [结果](envelope/app-data/oncue-probe-envelope/probe-result.json) |

## 复核

在仓库根目录运行：

```sh
for s in parser pagination retry deadline playback storage grounding envelope; do
  python3 oncue/tests/check_result.py --run-dir evidence/logic-tests/$s --wait-seconds 0 \
    --current-source oncue/bundle/main.splash || exit $?
done
```

已执行，每套输出 `PASS: N assertions; source/provenance/assertion inventory verified`。这只读取既有结果并核对生产源码、探针与断言清单，不重新运行应用。重跑方法见[测试说明](../../oncue/tests/README.md)。

宿主服务返回值受控注入，没有调用模型。文件系统、UI、计时器及时间真实；deadline观察约93秒，playback超过6.5秒。存储结果另有独立文件内容校验，不以成功提示代替保存。

各套保存当时的生产源码、探针、provenance和运行结果。探针包内复制的旧截图仅用于准入，不是本次交互证据；0.5.0实际截图见[验证记录](../../oncue/VERIFICATION.md)。
