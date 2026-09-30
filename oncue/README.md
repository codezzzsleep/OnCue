# OnCue · 群聊试映室 v0.2

队伍：OnCue。成员：YCOROY。赛道：OctoSense 即时消息 · Rinx。

给群聊加一个私人排练舞台：试一句尚未发出的台词，展开“顺着这句 / 换个问法 /
换个玩法”三种假想的下一幕。选择、编辑、保存存档，比较改台词前后，再导出自己想用的草稿。

## 现在可以运行什么

`server/` 是无界面 Linux 可运行的浏览器体验版，Python 3.9+ 标准库即可运行（协作容器实测 3.9.9），不需要桌面、
Rust、Node.js 或 Docker。它提供三组虚构现场，也允许手动输入自己的聊天片段。
本地模式明确使用规则和预设；模型模式会真正调用配置的 MiniMax API，不会静默降级成演示。

`bundle/` 保留 Rinx OctoScript 小程序 v0.1 源码，仍待原生运行、宿主接口和 Hub 准入联调。
服务器体验版不会自动读取 Rinx 或 Matrix 群聊，不能代表 Rinx 集成已经完成。

## 立即启动本地演示

解压，在本文件所在目录执行：

```bash
python3 server/app.py
```

浏览器打开 `http://127.0.0.1:8787`。点击“试映下一幕”，切换路线，修改并保留草稿；
保存两次存档后可以“对照最近两版”。存档与草稿仅在点击保存后写入当前浏览器，最多保留12个存档。
可以从存档恢复现场、导出带原消息和假设标签的剧本，或删除存档。

## 使用自己的 MiniMax API Key

API 调用不需要网页登录。Key 只配置在服务器，不放到前端或源码中。

把 Key 放在交付目录外的一个只允许自己读取的文本文件中，启动时指定文件的绝对路径：

```bash
chmod 600 /absolute/path/minimax.key
MINIMAX_API_KEY_FILE=/absolute/path/minimax.key python3 server/app.py
```

也可用 `MINIMAX_API_KEY` 环境变量。默认接口为 `https://api.minimax.cn/v1`，
默认模型为 `MiniMax-M2.7`。使用旧国内接口或国际账号时，可以配置 `MINIMAX_BASE_URL` 为
`https://api.minimaxi.com/v1` 或 `https://api.minimax.io/v1`，模型由 `MINIMAX_MODEL` 指定。
接口只接受这些官方 HTTPS 主机，不允许把 Key 转发到任意地址。

在页面选择“MiniMax 模型试映”，确认本次使用所选消息与台词，再点击试映。
每次点击最多发起一次模型请求，不自动重试，不自动发送群消息。
切换场景或修改台词后旧结果失效；停止等待不会保证已提交的模型请求取消或免于计费。

## 在没有 GUI 的服务器上运行

服务器启动命令与上面相同。使用已有 SSH 客户端做端口转发：

```bash
ssh -N -L 8787:127.0.0.1:8787 USER@SERVER
```

你的电脑浏览器打开 `http://127.0.0.1:8787` 即可操作服务器上的应用。
开发和模型调用在服务器完成，电脑无需安装 OctoSense / Rinx，也不用安装桌面环境。

需要通过已有 HTTPS 反向代理访问时，配置 `ONCUE_ACCESS_TOKEN`（至少24字符）和
`ONCUE_ALLOWED_HOSTS`（浏览器访问的域名或IP，不含协议、端口），并设置
`ONCUE_SECURE_COOKIE=1`。服务默认只监听本机，也可使用 `--host 0.0.0.0 --port 8787`。
对外监听必须有访问口令；页面先通过口令登录，口令和模型 Key 分开。
这是单用户体验版，未实现多租户隔离、持久会话或生产级登录限流。

## 可选 Docker

已附 Dockerfile，当前环境没有 Docker，尚未构建实测。普通 Python 启动已实测。
填写自己的 `.env`（示例见 `.env.example`）后可以在已有 Docker 的服务器尝试：

```bash
docker build -t oncue:0.2 .
docker run --rm --name oncue --env-file .env -p 127.0.0.1:8787:8787 oncue:0.2
```

容器仅复制服务器源码，使用非 root 用户；`.env`、Key、测试和原生代码不进入镜像构建上下文。

## 检查

```bash
python3 -m unittest discover -s tests -v
```

17项检查覆盖输入限制、来源摘录、待确认条件、模型协议、错误反馈、访问口令、来源隔离与注销。
真实 MiniMax 调用及浏览器基线已经实测；新增播放功能和原生功能的验证范围见 `VERIFICATION.md`。
Key 不在交付包中，运行时需配置自己的凭证。

## Rinx 小程序开发包

在支持 OctoScript 小程序开发导入的 Rinx 版本里登录 Matrix，打开 Mini apps，
选择 Import an app 或 App Hub → Developer。输入 `bundle/` 的绝对路径，Review bundle 后 Run。
真实群聊必须由用户在宿主中附加和授权；模型由宿主的 Octos 服务提供。
原生代码没有申请消息发送能力，保存草稿后由用户自行使用。

原生源码未改变，版本和摘要仍为 v0.1；修改后应使用 Rinx 官方封装工具或本包工具重新计算摘要：

```bash
python3 -m pip install blake3
python3 tools/stamp_bundle.py bundle
```

摘要正确不能替代原生启动、App Hub 准入、签名或比赛提交。

## 下一步

开发可继续在当前环境完成。比赛作品仍需补上实际 Rinx 宿主运行与消息读取、
Agent 回合、原生截图、Hub 检查，以及按主办方要求提供的演示与固定版本源码。
本包没有执行外部发布或比赛提交。

## 如何看待试映结果

来源摘录会逐字检查，但摘录存在不代表整段台词或推测都有事实依据。
模型对白始终标为假设。原消息中的当天返回与住宿提议、已知出游样例的早出发，以及部分新增费用数字，
会显示“待确认”提示；这是有限的词语检查，无法覆盖所有场景或全部语义冲突。
费用没有查询外部数据，所有路线都应由使用者对照原消息判断。

## 官方依据

- [MiniMax OpenAI兼容接口](https://platform.minimaxi.com/docs/api-reference/text-openai-api)
- [Rinx 小程序示例](https://github.com/upstreamlabs/Rinx/tree/main/examples/miniapps)
- [Matrix 与 Octos 服务](https://github.com/upstreamlabs/Rinx/blob/main/docs/adr/0005-octoscript-miniapps-matrix-octos.md)
- [共享 App Hub](https://github.com/upstreamlabs/Rinx/blob/main/docs/adr/0006-shared-app-hub-miniapps.md)
- [OctoScript API](https://github.com/OctoSense-org/OctoScript-App-Design-Flow/blob/main/docs/SCRIPT-API.md)

采用 Apache License 2.0，见 LICENSE。
