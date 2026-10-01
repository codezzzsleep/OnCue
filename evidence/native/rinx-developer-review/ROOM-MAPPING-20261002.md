# 同批房间映射（脱敏）：API 事件元数据 × OnCue 有序正文指纹

**限定**：本文件全部结论在 **fixed Rinx 0879548 + local lookup patch** 下取得；**官方原版未通过**。
**未向房间发送任何消息。**

## 0. 一句话结论

OnCue 自身经真实 UI 授权读到 **12** 条；与 API 侧「现有 13 条中最新 12 条」**按顺序逐条正文指纹一致 = 12/12**。
**`event_id` / `origin_server_ts` 只存在于 API 侧**——app 响应不暴露它们，因此本表只能做**有序正文指纹对照**，
**不能声称 app 看到了事件元数据**。

- 脱敏输出： [`ROOM-MAPPING-OUTPUT.txt`](ROOM-MAPPING-OUTPUT.txt)
  整体 sha256 `bbb83698f343191498dad8feb2175fea5aa20278f2d1c71a86a59b69b485af04`
- 探针源码： [`probe-src/roommap-probe.splash`](probe-src/roommap-probe.splash)
  整体 sha256 `ffa5838be264e5b308dde75bc61231a6fae3d61e36377db63ddfe812c52f1efd`

## 1. 探针怎么工作（可复现）

**为什么需要探针**：Splash 侧**没有 SHA256 原语**，应用算不出哈希。所以让探针把 OnCue 读到的
**每条正文原样落盘到本机应用存储**，由我在宿主侧计算 UTF-8 SHA256，**只公开哈希、不公开正文**。

探针（只读，追加在 `/root/oncue-runtime/dev/probe-044/RoomMap/main.splash` 末尾）：

```javascript
{
    start_timeout(3.0, fn(){ cue_import_room() })
    start_timeout(16.0, fn(){
        let n = cue_sources.len()
        let out = "count=" + n + "\n"
        for i in n {
            let s = cue_sources[i]
            fs.write("body-" + (i + 1) + ".txt", s.body)
            out = out + "M" + (i + 1) + " sender=" + s.sender + " chars=" + s.body.to_chars().len() + " bytes=" + s.body.len() + "\n"
        }
        fs.write("bodies-index.txt", out)
    })
}
```

**产物的字节精确性**（避免哈希算错）：`fs.write` 不额外追加换行——`bodies-index.txt` 里声明的
`bytes=` 与落盘文件长度逐个相等（例：`M1` 声明 60 B，`body-1.txt` 实测 60 B）。

**执行路径**（与 §3 的真实回合同一形态）：Rinx → `Mini apps` → `Import an app` →
填**仓库外 unsigned 探针包** + **精确 room id** → `Review bundle`（Allowed room = 精确值）→ `Run`。

## 2. 对照表

见 [`ROOM-MAPPING-OUTPUT.txt`](ROOM-MAPPING-OUTPUT.txt)。每行：
`event_id(SHA256 前 16)` / `origin_server_ts` / `sender`(只保留 localpart) / `API 正文 SHA256(前16)` /
`OnCue 正文 SHA256(前16)` / 一致。

- **12/12 逐条一致**
- 未被读到的是**最早那条**（32 字符）
- `sender` 在两侧都是 `@codezzzsleep`（去 homeserver 后一致）

## 3. 口径与失效声明

- **`sum` / `head` 不再作为最终证据**。早先 `oncue-self-read-room.txt` 里的 `sum=`（码点和）与 `head=`（码点十进制串）
  只能做**快速交叉核对**，本文件起改用 **UTF-8 SHA256** 作为正文强指纹。
  旧文件保留不改写，但**以本文件为准**。
- **不伪造字段**：app 侧的 `matrix.read_messages` 响应只被产品用到 `sender` 与 `body`；
  **没有任何观测表明 app 收到了 `event_id` / `origin_server_ts`**。故表中那两列标注为「仅 API 侧」。
- **未发送消息**：整个过程只有读取。

## 4. 复现命令（骨架）

```bash
# 1) 生成/更新探针包（仓库外），并重新 stamp 以计算摘要
deploy/tools/make_probe_bundle.py <fixture> <out_dir> <app_id>   # 若复用现成包可跳过
hub stamp /root/oncue-runtime/dev/probe-044/RoomMap

# 2) 在 Rinx 里 Review + Run 该包（真实 UI 授权，room = 精确值）

# 3) 读回落盘，宿主侧算哈希并出对照表
#    （脚本见本仓库提交信息；输出即 ROOM-MAPPING-OUTPUT.txt）
```
