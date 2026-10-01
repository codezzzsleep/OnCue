# 新容器恢复：16核 / 32GB

2026-10-02：旧8核16GB容器异常后，用户新开空容器。以下是恢复计划，**不是新容器已恢复的报告**。
新AI2已确认WebChat client身份ai2、GitHub SSH与git身份、`/root/hackthon/OnCue`（main `093bcfb`）和本地代理`127.0.0.1:17888`。
用户当前先要求停手对齐；收到用户开始恢复的指令后再执行安装、构建和启动。

## 1. 接管已有代码与聊天室

- 不重配GitHub账号，不重复克隆已经存在的OnCue。先检查工作区再正常pull；有未提交修改先报告、保留，不reset丢文件、不强推。
- WebChat只用client模式连接`http://193.112.97.187:8088/`，不运行init/serve、不重生成或覆盖ai2.token。该服务是独立通信端点，不因本容器为空而重建。
- 身份仍是用户授权的AI2；接管声明须注明新容器，不把旧AI2消息中的运行现场当作自己做过。
- 从服务读最新消息，按next_cursor分页并保存游标，不只停在旧223。token只向同一站点发送，禁止跨站重定向，保存在私有文件，不入Git/日志。

```bash
cd /root/hackthon/OnCue
git status --short
git switch main
git pull --ff-only
git rev-parse HEAD
python3 oncue/tools/recovery_preflight.py
```

最后一项脚本加入main后可执行。它只读取资源信息，不安装软件、不读取凭据。字段为null表示未读到，不能据此认定资源无限；用容器平台限额、free与现有监控补充核对。
核对实际OS、CPU架构、cgroup有效内存上限/当前占用、CPU quota和磁盘空间。容器标称32GB不代表cgroup一定允许32GB。
复用已有system-monitor观察构建峰值；先只运行一个构建，`CARGO_BUILD_JOBS=2`，不要按16核开16个rustc、也不要同时编译多个宿主。

## 2. 恢复工具链与固定源码

先读官方[Flow](https://github.com/OctoSense-org/OctoScript-App-Design-Flow/blob/main/README.zh-CN.md)、OctoSense的AGENTS/README和Linux依赖说明，根据现场发行版选择apt或dnf；不要假设新容器仍是HCE/aarch64。
安装系统编译依赖、Rust工具链、Python3、Xvfb、X11认证/诊断工具、Mesa软件渲染、x11vnc、noVNC/websockify及实际截屏工具。优先系统发行版软件包，不重复源编译能直接安装的工具。
旧环境曾成功用Rust1.98.0；固定OctoSense提交未提供rust-toolchain.toml，先核对源码MSRV和现场工具链，再记录实际版本，不虚称由该文件锁定。

| 源码 | 基线 |
| --- | --- |
| OctoSense | `https://github.com/OctoSense-org/OctoSense.git`，`6c4746f0854b74446f854fdcd32eeb87b5192a81` |
| Rinx | 由OctoSense的Cargo.lock拉取，`0879548ba826c786eb6ad3f60dfba7bd342bd750` |
| octos | `https://github.com/octos-org/octos.git`，`fe08d8e6b3b32e672b0f956a2b692c3c8205b167` |
| App Hub | `https://github.com/OctoSense-org/OctoSense-App-Hub`，`0f332112f0b5a379c5bb33790df74b21597190cf` |

OnCue始终main；外部依赖按基线检出。OctoSense运行官方`python3 tools/setup.py`准备其`.sources/`与官方补丁，然后`python3 tools/setup.py --check --cargo`。
不删除Cargo.lock、擅换Makepad分支、使用另一版Rinx来掩盖旧问题。已有17888代理需先验证实际协议/可用性再配置Git/Cargo，不把代理端口本身当HTTP/SOCKS协议的证明。

## 3. 串行构建与真实运行

OctoSense目录先执行`CARGO_BUILD_JOBS=2 cargo build --release --locked -p octosense`；完成后再构建所需octos CLI、固定Hub/card-host，包名以实际Cargo manifest为准。
Rinx是OctoSense托管模块，不另起一个独立Rinx内核。
记录每次命令、实际退出码、Rust/源码版本、产物路径/摘要；成功日志不可从旧报告搬过来。

重建无密钥start/stop/env脚本，服务链：Xvfb `:99` → llvmpipe → OctoSense带Rinx模块 → x11vnc → noVNC。
已有启动参数线索：`--module rinx --test-action launch-rinx`；正式OnCue Hub入口`--test-action launch-hub:oncue-screening-room`仅在安装包后使用，不凭空启动未安装应用。
启动必须等待依赖真实健康；停止用官方`/quit`和记录的PID，不用宽泛`pkill -f`。
先验证X认证与GL、桥`/help`、实际Rinx首帧和输入，再恢复远程访问。

| 地址 | 用途 |
| --- | --- |
| `127.0.0.1:18141` | Makepad控制桥，保持回环 |
| `127.0.0.1:5901` | x11vnc，保持回环、私有新密码 |
| `127.0.0.1:6080` | noVNC HTTP/WebSocket统一入口 |

旧deploy脚本只在旧容器独立本地仓库，目前没有进入OnCue的公开main；不能假称clone项目就能获得旧start.sh。按官方机制和`evidence/ENDPOINTS.md`的历史线索重建后，将无密钥脚本提交到main的`deploy/`并做stop→start实测。
GL后端官方/g曾超时，若本机仍复现，记录限制并用真实X像素capture；不可用重绘控件树代替截图。

## 4. 私有状态、账号与浏览器入口

代码、截图与已提交证据可从Git恢复；未push的044分页代码、临时宿主补丁、编译缓存和私有state不能从Git凭空恢复。
先检查是否有真实旧卷/备份；没有就按重建执行，不重置旧账号密码或伪造历史草稿。

- Matrix账号在新Rinx重新登录，并选本人私有测试房间。旧Matrix会话、加密设备密钥不在Git；重新登录不等于恢复旧设备的加密历史。只按实际可读内容声明结果。
- MiniMax由宿主私有配置恢复，不能写入小程序。`/srv/oncue-core`与`/srv/oncue-apps`是旧环境最后使用的运行目录线索，现场重新建立权限与配置，不假设已存在。
- AI1已获授权提供模型/Matrix凭据；如需私密重配，使用新AI2环境生成的公钥封套或用户私有渠道。旧封套若没有旧私钥无法解密，不打印密钥、不把凭据粘贴在讨论正文/Git。
- VNC密码重新生成并保存600文件；旧密码文件已经丢失时不能承诺继续有效。
- 新容器的cloudflared连接配置需要恢复。先确认connector实际能到达新容器6080，再在原隧道或新隧道正确配置原主机名`vnc.ycyc.kdns.fr`。不能只恢复CNAME就认为新connector在线；同名域名不证明流量到新容器。
- 既有cloudflared管理端口`20241`不等于noVNC服务入口。cloudflared是否为目标隧道必须现场核对，token保存在私有配置。

## 5. 恢复应用与继续开发

正式当前包仍是0.4.3开发候选，未整体验收；资源digest `ec7773d51f2078e618d1711bb9b2840629e272858b040abf0af19c1c492e9619`。保留signed原件，Rinx Developer使用仓库外仅去signature的同资源开发副本，真实Review/Run和房间授权。
不把旧localmirror seq9当新环境已存在/官方收录；旧演练私钥若无备份，只能另建并明确是新演练信任根，不能冒充旧publisher续签。正式publisher身份与Submit由最终可审材料处理。

恢复基本样例/草稿操作后，继续两项真实缺口：

1. 长文本分页：源消息、对白/建议、多行A/B各至少200字，所有页拼接逐字等于输入，无routes时A/B也可翻页；412×892、990×613真实图，不用snap完整值代替像素可读。旧043只能证明短fixture。
2. 房间绑定：固定Rinx导入表单与library有重复room id线索；先真实Review无效room应Invalid、有效room应显示准确ID，再真实读本人房间最近12条→共享Octos七块回合→停止/90秒超时/旧回调隔离。必要诊断在固定基准仓库外仅做全限定lookup补丁，存base+diff，结果标明localpatch，不能冒称原版已通过；不预写consent/伪造lease。

任务20/22是旧执行体的工作标签，不是新机器已有进程。按main实际内容继续目标，不等待不存在的worker，不照搬旧PASS。
比赛硬要求是OctoSense／Rinx中运行的OctoScript应用与正式AppHub发布；先基本功能→系统Agent→整体完善，不恢复Python网页主线。

## 6. 本次恢复的交付与防再次丢失

每个阶段给AI1实际结果、第一条阻断和下一可交付证据，不只说“进行中”；活跃执行约2分钟读新消息，普通实现自主继续。
在main提交无密钥部署脚本、固定版本/系统依赖清单、恢复文档和真实stop→start报告。每个可复现实质改动及时push，不把几十分钟代码只留/tmp。
私有state（含账号、provider、VNC、演练密钥和草稿）另作加密备份到用户控制的持久存储；它不进入Git，也不上传公开讨论组。恢复脚本本身不是state备份。明确备份位置和实际恢复验证，不能仅声称“已备份”。
