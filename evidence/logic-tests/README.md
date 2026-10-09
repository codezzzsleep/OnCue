# 逻辑测试结果

2026-10-10，0.5.2 同一生产源码的 **12 套 368 项断言全部通过**。入口SHA-256：`049bced508c020c9c3240f154afc8c47c5e150d2cd881a650dd7503da72801a5`；154个生产函数原样进入真实card-host。

| 套件 | 断言 | 内容 |
|---|---:|---|
| parser | 39 | 生成协议、标记、段落顺序、长度 |
| pagination | 15 | 文本守恒、组合字符、分页导航 |
| retry | 38 | 一次修复、实际拒绝原因及原请求保留、输入身份、许可、候选暂存与应用 |
| deadline | 6 | 真实90秒共享期限、迟到回包；观察窗口约93秒 |
| playback | 18 | 真实1.4秒计时、暂停/重播/切换 |
| storage | 56 | 规范格式、真实I/O失败、房间隔离、容量、草稿保护 |
| grounding | 96 | 来源、数字/单位（含中文数字、半天/半小时、复合单位）、承诺规则 |
| envelope | 25 | 异常回包、失败载入保留旧房间、切换确认、授权/账号/未登录错误 |
| send | 44 | 发送正文边界、窗口校验、匹配器、确认与单次发送、延迟/错误/重发 |
| send2 | 21 | 迟到回调、读回对抗、Unicode前缀、选句/修订采用门 |
| send3 | 7 | 已核验本人消息采用门、发送记录元数据、显式保存 |
| send4 | 3 | 真实30秒发送超时、迟到成功不重写、无意外模型服务 |

## 复核

在仓库根目录运行：

```sh
for s in parser pagination retry deadline playback storage grounding envelope send send2 send3 send4; do
  python3 oncue/tests/check_result.py --run-dir evidence/logic-tests/$s --wait-seconds 0 \
    --current-source bundle/main.splash || exit $?
done
```

已执行，每套输出 `PASS: N assertions; source/provenance/assertion inventory verified`。这只读取既有结果并核对生产源码、探针与断言清单，不重新运行应用。重跑方法见[测试说明](../../oncue/tests/README.md)。

宿主服务返回值受控注入，没有真实 Matrix 发送；send4 含真实30秒传输超时窗口。文件系统、UI、计时器及时间真实；deadline观察约93秒，playback超过6.5秒。存储结果另有独立文件内容校验，不以成功提示代替保存。

各套保存当时的生产源码、探针、provenance和运行结果。探针包内复制的截图仅用于准入，不是本次交互证据；实际原生截图见[验证记录](../../oncue/VERIFICATION.md)。
