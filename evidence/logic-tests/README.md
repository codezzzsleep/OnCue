# 逻辑测试结果

8 套共 149 项断言的结果文件，2026-10-04 运行，全部通过。对应的 `main.splash` SHA-256 是 `a42e0216d1b81caccb486f57b7c60bec994f0e631da3c1f78a4d388c7cf89d58`。

| 套件 | 断言数 | 结果文件 |
| --- | --- | --- |
| parser | 30 | [probe-result.json](parser/app-data/oncue-probe-parser/probe-result.json) |
| pagination | 15 | [probe-result.json](pagination/app-data/oncue-probe-pagination/probe-result.json) |
| retry | 9 | [probe-result.json](retry/app-data/oncue-probe-retry/probe-result.json) |
| deadline | 6 | [probe-result.json](deadline/app-data/oncue-probe-deadline/probe-result.json) |
| playback | 18 | [probe-result.json](playback/app-data/oncue-probe-playback/probe-result.json) |
| storage | 14 | [probe-result.json](storage/app-data/oncue-probe-storage/probe-result.json) |
| grounding | 53 | [probe-result.json](grounding/app-data/oncue-probe-grounding/probe-result.json) |
| envelope | 4 | [probe-result.json](envelope/app-data/oncue-probe-envelope/probe-result.json) |

## 复核

在仓库根目录运行：

```sh
for s in parser pagination retry deadline playback storage grounding envelope; do
  python3 oncue/tests/check_result.py --run-dir evidence/logic-tests/$s --wait-seconds 0 \
    --current-source oncue/bundle/main.splash
done
```

每套输出 `PASS: N assertions; source/provenance/assertion inventory verified`。这条命令只读取结果文件并与当前源码比对，不运行测试。重跑方法见[测试说明](../../oncue/tests/README.md)。

## 说明

- 宿主服务的返回值由测试脚本模拟，没有调用模型。
- 每套目录里的 `bundle/` 是当时的测试包，包含生成时复制的资源和旧截图，不是发布包。
