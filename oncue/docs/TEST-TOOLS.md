# 开发与验收工具

本页说明本地工具的用法与边界。修复后的工具已于 2026-10-04 在钉定宿主上实跑通过（routes / playback / draft / reopen 四模式，证据在 `build/validation-2026-10-04/`）。

## 1. 离线检查（不连宿主）

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s oncue/tests -p 'selftest_*.py' -v
```

91 项：生成器/checker 基础设施 11 项、验收工具安全 28 项、helper 51 项，全部不触网、不启宿主、不写 `__pycache__`。CI（GitHub Actions）跑同一套，Python 3.9 与 3.11 两个版本。

## 2. 开发副本

```sh
. /root/hackthon/refs/octo-env.sh
DEV_ROOT="$(mktemp -d /tmp/oncue-dev.XXXXXX)"
python3 oncue/tools/prepare_dev_bundle.py "${DEV_ROOT}/bundle" --hub "$OCTO_HUB"
```

复制 → 移除签名 → stamp → `hub check --allow-unsigned`。拒绝已存在目的地、源目录内目的地、符号链接与畸形 JSON；失败保留副本供检查。destination 本身就是包目录。

## 3. 原生验收（显式授权）

`native_acceptance.py` 驱动**已运行的 Rinx 宿主实例**，会关闭当前小程序并执行新的 Review/Run，因此必须显式授权：

| 参数 | 作用 |
|---|---|
| `--port` / `--out` | 宿主远程桥端口 / 全新证据目录 |
| `--bundle` / `--release-bundle` | 未签名副本 / 发布参考包（逐文件比对，签名除外） |
| `--hub` | 本地 hub 可执行文件 |
| `--account` / `--data-dir` | 预期 Matrix 账号及对应 Rinx 数据目录（账号标记须一致） |
| `--room` | 明确房间；无房间传空字符串 |
| `--host-binary` / `--display` / `--xauthority` | 宿主二进制指纹 / 本地 X display / 认证文件 |
| `--mode` | `routes` / `playback` / `draft` / `reopen` |

许可开关：`--allow-import`（导入）所有模式必需；`routes`/`playback` 另需 `--allow-real-turn --trial`（一次真实读房与试映，应用内部最多重试一次，工具不外层重试）；`draft`/`reopen` 另需 `--allow-draft-write`（覆盖测试草稿）。

```sh
python3 oncue/tools/native_acceptance.py \
  --port 8771 --out build/validation-2026-10-04/routes \
  --bundle "$DEV/bundle" --hub "$OCTO_HUB" \
  --account '@codezzzsleep:matrix.rinx.chat' --data-dir /srv/oncue-rinx-data-rinxchat \
  --room '!2TfOHq2ZGCYO5WJmDC:matrix.rinx.chat' \
  --host-binary /opt/src/OctoSense/target/release/octosense \
  --display :99 --xauthority /root/oncue-runtime/state/xauthority \
  --mode routes --allow-import --allow-real-turn --trial '那我们中午出发、当天回来，先确认预算可以吗？'
```

行为要点：

- 导入前后逐文件核对副本与发布包一致，Review 核对应用名、版本、服务清单与房间；重开复用同一路径。
- 状态机按生产状态文案区分等待/自动重试/成功/失败，未知文案立即失败，不把「正在自动重试」当终态。
- 点击要求目标唯一、双轴完整在视口内；Rinx 常驻的空 `CalloutTooltip` 不拦截点击（实证），有内容的悬浮层会拒绝并先移鼠标题栏清除后重试。
- 尺寸默认严格一致，显式 `--size-tolerance` 才放宽，报告始终记录实测 geometry。
- 草稿文本带每轮唯一标记并核对保存字节，防止旧文件掩盖写入失败。
- 所有检查用显式异常，`python -O` 下同样生效；证据输出禁止落在包目录或账号数据目录内。
- 输入绑定原生窗口 ID，多窗口或窗口变化时拒绝。

## 4. 低层 helper

`native_bridge.py`（快照/点击/输入/滚动/窗口绑定）、`rinx_session.py`（窗口尺寸实测，默认拒绝 Review/Run）、`collect_native_reading.py`（逐页采集阅读内容）是低层驱动，不替代完整验收工具的包/账号核对。
