# 早期网页原型（历史资料）

此网页用于原生环境就绪前的玩法探索，已退出当前开发、验收与参赛交付主流程。
保留代码、运行说明与历史证据以便溯源。当前作品请从 [仓库首页](../../README.md) 的 OctoScript 应用入口开始。
网页模型调用和浏览器测试不能证明原生 Rinx／共享 Octos 链路通过。
以下命令均从仓库根目录执行，仅供复查历史原型。

## 历史网页启动方式

在仓库根目录运行，无需图形桌面或额外 Python 依赖：

```bash
python3 oncue/server/app.py
```

打开 `http://127.0.0.1:8787/`。默认是明确标记的本地规则演示。
若服务器已有仓库外的模型凭据文件：

```bash
MINIMAX_API_KEY_FILE=/absolute/path/minimax.key python3 oncue/server/app.py
```

模型模式需在页面选择并确认取材。网页支持保存和恢复完整排练场景，区别于原生的草稿A/B。
部署说明见 [服务器运行说明](WEB-PREVIEW-SERVER-LEGACY.md)。

![辅助网页的实际播放画面](../../evidence/playback/01-playback-light.png)

```bash
python3 -m unittest discover -s oncue/tests -v
# 需要已有 Playwright + Chromium，对运行中的辅助服务器执行：
python3 evidence/playback_check.py --url http://127.0.0.1:8787/
```

