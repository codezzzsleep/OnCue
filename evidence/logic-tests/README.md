# 0.4.7 受控测试原始证据恢复

## 结论与时间

- **恢复日期：2026-10-04（UTC；北京时间 UTC+08:00 同日）。这是本地原件归档与只读复核，不是本轮执行测试。**
- 已恢复 **8 套、146 项**原始通过结果。原 run 与本归档分别执行当前结果检查器，均退出 **0**。
- 原件来源唯一为 `/tmp/oncue-full5.MzauQ6/<suite>`，由已读的 [final5-workdir.txt](<../../build/current/final5-workdir.txt>) 明确指向。只在另外九个已读 workdir 指针目录发现 provenance 路径，没有读取其旧 run 内容或混入旧结果；没有扫描无关临时目录。
- 原结果自带的 Unix 时间转换为 UTC 后，首个 parser 开始于 **2026-10-03T17:50:50.822583+00:00**，最后 deadline 观察结束于 **2026-10-03T17:52:53.734762+00:00**（北京时间 2026-10-04 01:50:50–01:52:53）。这些是原记录的时钟值，不是恢复执行时间，也没有外部时间戳认证。
- 复制 **67 个原文件、1,818,251 字节**；复制前后对源/目标逐项计算 SHA-256 并比较原始字节，全部相同。除本说明外没有新造数据文件，没有重建或补写 provenance。

## 当前版本与哈希核对

以下不是只相信原 provenance 声明：对当前文件、原 production 快照、原 probe 内嵌内容分别核对了实际字节。

| 对象 | SHA-256 | 核对结果 |
| --- | --- | --- |
| 当前 [production source](<../../oncue/bundle/main.splash>) / 各套原 production 快照 | `4b2fd02fb3e893dd15214a22f7ce173eed3d11c5cab1cbda4c72ef8038e472b5` | 8/8 当前且相同 |
| 当前 [fixtures](<../../oncue/tests/fixtures.json>) / 各套原 probe 内嵌 fixture | `7e250d395132108f85065681f9a41478f08570303caf65a212507ad4b76373b1` | 8/8 字节相同，非旧 fixture |
| 当前 [harness](<../../oncue/tests/probe_harness.splash>) / 各套原 probe 内嵌 harness | `88461e61108a9bd07fae165cae29b9bba69f19267957879ff80bc5216f3aa9b5` | 8/8 字节相同，非旧 harness |
| 各套 [production-functions 示例](<parser/production-functions.splash>) | `a3960d3489215b66958e545a8f28fb0be25c319c85538b42325db4c9d8b8c08e` | 8/8 为当前 **65** 个函数的原始逐字拼接 |
| 本轮使用的 [check_result.py](<../../oncue/tests/check_result.py>) | `6115ff218756ddba00333fffe55c848d768fda80c91b2cfab4f76312caa61f98` | 只读结果收集器 |
| 本轮读取的 [generate_probe.py](<../../oncue/tests/generate_probe.py>) | `a8bd2577f4d66f1e8f00101e21a3c3bca0262cd1b703b6715485d0181d9fed84` | 仅调用纯静态函数提取；未调用生成或运行入口 |

原 run 不另存独立 fixture/harness 文件；它们完整嵌入各套原 probe 入口，已直接解码提取 fixture 原文字节、截取 harness 原文字节并核对上述哈希，没有用当前 fixture 替换原内容，也没有生成新的独立副本。

对每套额外静态核对：

1. 原 probe 入口的 SHA-256 等于其原 provenance 的 `generated_sha256_before_stamp`。
2. 当前 fixture 的该 suite 断言 ID 列表与原 provenance 完全一致，结果断言 ID 的多重集合完全一致，全部 `passed: true`。
3. 当前 production、原 production 快照、原 probe 中的 **65 个** `cue_*` 函数逐字相同；函数名、起止行和各函数 SHA-256 与原 provenance 一致。
4. 在内存中去掉受控 header/harness、恢复 provenance 记录的原初始化语句后，完整 probe 生产页面与当前 source 字节相同。未写回文件、未执行应用逻辑。
5. 所有复制路径逐层拒绝 symlink，要求普通文件并限制在明确原 run 内；结果相对路径必须恰为 `app-data/oncue-probe-<suite>/probe-result.json`。目标目录原先不存在，文件用独占创建，未覆盖或删除。

**计数纠正：这组原件实际是 65 个生产函数，不是部分历史文档写的 64。**恢复前自编额外静态审计曾因沿用 64 的假设退出 1；调查确认当前源码与原 provenance 均为 65，修正审计假设后全部通过。该退出 1 不是原受控测试失败，也没有修改其结果。

## 各 suite 原 run、结果与只读校验

每行原 run 是完整绝对路径；归档中的 provenance 与 result 均保持原相对位置和原始内容。

| Suite | 原 run | 原 provenance | 归档原 result | 断言 | 原 run / 归档检查退出码 | 原观察区间 |
| --- | --- | --- | --- | ---: | --- | ---: |
| parser | `/tmp/oncue-full5.MzauQ6/parser` | [provenance](<parser/provenance.json>) | [result](<parser/app-data/oncue-probe-parser/probe-result.json>) | 30 | 0 / 0 | 0.005444 s |
| pagination | `/tmp/oncue-full5.MzauQ6/pagination` | [provenance](<pagination/provenance.json>) | [result](<pagination/app-data/oncue-probe-pagination/probe-result.json>) | 15 | 0 / 0 | 0.002894 s |
| retry | `/tmp/oncue-full5.MzauQ6/retry` | [provenance](<retry/provenance.json>) | [result](<retry/app-data/oncue-probe-retry/probe-result.json>) | 8 | 0 / 0 | 0.004530 s |
| deadline | `/tmp/oncue-full5.MzauQ6/deadline` | [provenance](<deadline/provenance.json>) | [result](<deadline/app-data/oncue-probe-deadline/probe-result.json>) | 6 | 0 / 0 | 92.996863 s |
| playback | `/tmp/oncue-full5.MzauQ6/playback` | [provenance](<playback/provenance.json>) | [result](<playback/app-data/oncue-probe-playback/probe-result.json>) | 18 | 0 / 0 | 6.797523 s |
| storage | `/tmp/oncue-full5.MzauQ6/storage` | [provenance](<storage/provenance.json>) | [result](<storage/app-data/oncue-probe-storage/probe-result.json>) | 14 | 0 / 0 | 0.002795 s |
| grounding | `/tmp/oncue-full5.MzauQ6/grounding` | [provenance](<grounding/provenance.json>) | [result](<grounding/app-data/oncue-probe-grounding/probe-result.json>) | 51 | 0 / 0 | 0.004232 s |
| envelope | `/tmp/oncue-full5.MzauQ6/envelope` | [provenance](<envelope/provenance.json>) | [result](<envelope/app-data/oncue-probe-envelope/probe-result.json>) | 4 | 0 / 0 | 0.000822 s |
| **合计** | | | | **146** | **全部 0** | |

[deadline 原结果](<deadline/app-data/oncue-probe-deadline/probe-result.json>)的 `deadline.timeout_elapsed.detail.observed_elapsed` 为 **90.04759526252747 秒**。上表原观察区间是 `observed_at - started_at`，不是本轮收集器等待时间；本轮全部使用 `--wait-seconds 0`。

### 原结果与入口哈希

| Suite / 原 result | Result SHA-256 | 原 probe 入口 SHA-256 |
| --- | --- | --- |
| [parser](<parser/app-data/oncue-probe-parser/probe-result.json>) / [入口](<parser/bundle/main.splash>) | `6b9a1a9bb701cb08933db9654fe27d4926a5ee139c2ef27c4fdfa2d5534342e3` | `cefb095b211a602564bc44989dd524c7228ddaff090deacdad5cc5c614b713d5` |
| [pagination](<pagination/app-data/oncue-probe-pagination/probe-result.json>) / [入口](<pagination/bundle/main.splash>) | `f2f8e8a26ab198e2d811cfb53e65530f9b187fbe3fda6ebe2160508c0595da6e` | `4cdfa62cbb8fd9d77a6291bad174d99e29ec3ec0df8114db0584bbc05f8ad884` |
| [retry](<retry/app-data/oncue-probe-retry/probe-result.json>) / [入口](<retry/bundle/main.splash>) | `c09393677586b47b023fc49f6b4a5d4762b3f14711d22a610543c1007040fde5` | `9a8b156cc2c45d425d508e1bb30c88f82fb2f4e6638e7f0632ec1ba0400ad26e` |
| [deadline](<deadline/app-data/oncue-probe-deadline/probe-result.json>) / [入口](<deadline/bundle/main.splash>) | `ee246420235a670bdc2d2e0167c717473b7fb7de8b494a4b67e716bc350a6cda` | `f18b23b9ab6a491cb1437b9070670dc945ef911be9456d1d88a3aa51dbdb764d` |
| [playback](<playback/app-data/oncue-probe-playback/probe-result.json>) / [入口](<playback/bundle/main.splash>) | `778dd4618e95c3b8ff36a1813007dbfea199353d1fa095487513381301599c69` | `d8ed095ffc4be0bd077254c5657dc2cdc5af4c6d0abe9104d6c14a444b53c76f` |
| [storage](<storage/app-data/oncue-probe-storage/probe-result.json>) / [入口](<storage/bundle/main.splash>) | `63c8ece70ac7e4dd663d6921442e033b0e2d7f1100440deab80379eb9c8739a8` | `5f95e23380be85c8b792126d7eb0265ea8ee97a018b386dad1205b89e6eb5176` |
| [grounding](<grounding/app-data/oncue-probe-grounding/probe-result.json>) / [入口](<grounding/bundle/main.splash>) | `e24e6d24e9c4a8f1ac7edf847736c908108998f4edbf6a11549d3f7c5e695c8c` | `0e4c55c81c0836bff48cfb8dc20a854eabee38b1398231233c73defdf4915cad` |
| [envelope](<envelope/app-data/oncue-probe-envelope/probe-result.json>) / [入口](<envelope/bundle/main.splash>) | `c539d51eb048f13d966cc535a15b6f05b3521e9eef909210bab66f3b793d40e7` | `581e00cdf724cbbb11e7edddc9203fba3f99fbc9010e25ffcd8f70d7f62cba3b` |

## 三份合成 storage 原文件

这三份是明确 probe jail 中原有的合成夹具落盘文件，不是账号草稿或真实房间数据。分别与当前 fixture 字符串的 UTF-8 原始字节、原 provenance 哈希和原 result 元数据一致。

| 原文件归档 | 字节数 | SHA-256 |
| --- | ---: | --- |
| [draft.txt](<storage/app-data/oncue-probe-storage/draft.txt>) | 92 | `4bf1da45b4c2a5f5db2a532f1e10d438aa45dc8b29ef8d466fb05e2522be27ec` |
| [take-a.txt](<storage/app-data/oncue-probe-storage/take-a.txt>) | 77 | `2855e3997808cd5049620e645aca4f2e467fa17d3263f62db9be155b81a153b6` |
| [take-b.txt](<storage/app-data/oncue-probe-storage/take-b.txt>) | 95 | `7a24a74983409ccf7b7f12c22f853918f8074f96051b93735de0d9a798f8a3ba` |

## 归档范围与明确排除

每套只保留以下原路径；storage 另加上表三文件：

```text
<suite>/
  provenance.json
  production-main.splash
  production-functions.splash
  bundle/
    main.splash
    manifest.json
    listing.json
    assets/icon.svg
  app-data/oncue-probe-<suite>/probe-result.json
```

**隐私优先的完整性限制：本归档不是完整可重新 admission/运行的 bundle。**原 bundle 的两张上市截图包含真实测试房间消息，本轮按“不复制真实房间 data”要求，全部排除（8 套共 16 个 PNG）。未裁切、脱敏、替换或制造截图；未改原 manifest/listing 或重新 stamp。原 listing 仍引用未归档的截图，原 manifest 摘要也没有重算。因此这里只保证结果检查器所需证据完整，不声称归档 bundle 的资源完整、摘要可重新通过 admission，亦不以这些截图作 probe 证据。

[parser 原 listing 的归档](<parser/bundle/listing.json#L27>)仍原样包含“138 项”的历史文案；其余各套 listing 字节相同。该文案不是本恢复的计数依据，146 以本次核对的原断言 inventory/result 为准。没有为了同步数字改动这些原文件。

没有复制日志、其他 app-data、真实房间数据、账号目录或任何秘密；没有访问凭据/私钥。没有运行 VM、card-host、Rinx、OctoSense、模型、生成器入口或 Git 命令；没有更改已有 bundle、已有文档或 `/tmp` 原件。本目录之外没有本轮写入。

## 只读复核命令

原 run 校验实际逐套使用如下命令形态（替换 `<suite>` 为表中八个名称）：

```sh
python3 -B /root/hackthon/OnCue/oncue/tests/check_result.py \
  --run-dir /tmp/oncue-full5.MzauQ6/<suite> \
  --wait-seconds 0 \
  --current-source /root/hackthon/OnCue/oncue/bundle/main.splash
```

归档后也逐套执行同一命令，将 `--run-dir` 改为：

```text
/root/hackthon/OnCue/evidence/checkpoint-0.4.7-recovered/<suite>
```

全部输出 `PASS: N assertions; source/provenance/assertion inventory verified`，其中 N 为表中各套数，退出码全部 0。收集器不执行应用逻辑；其本身不验证当前 fixture/harness 或逐函数字节，故本恢复另做了前述静态核对，不能只凭 `--current-source` 推导那些额外结论。

## 证据边界

原结果明确 `controlled_injection: true`、`natural_model_test: false`、`semantic_fact_verification: false`。这些恢复证据是此前受控 OctoScript 测试的本地原记录，不是自然模型输出、不是本轮端到端宿主验证、不是接收者授权或账号隔离验证、不是语义级事实证明，也不能单独证明真实进程重启恢复或 App Hub 上架。哈希提供本地字节一致性与来源链核对，不等于独立第三方运行见证或不可伪造的签名认证。
