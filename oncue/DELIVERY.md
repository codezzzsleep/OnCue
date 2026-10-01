# 可复现交付

开发与交付使用仓库 `main`。验证结果须对应实际运行的代码；修改运行逻辑后重验受影响的流程，文档修订不需要重复消耗模型额度。

## 浏览器版

在仓库根启动 `python3 oncue/server/app.py`，模型配置使用仓库外的私有 Key 文件。后端检查和真实浏览器检查分别执行：

```bash
python3 -m unittest discover -s oncue/tests -v
python3 evidence/playback_check.py --url http://127.0.0.1:8787/ --out evidence/playback
```

已有 Chromium/Chrome 时，可在第二条命令中加入 `--executable /absolute/path/to/chromium`，直接复用现有浏览器。
报告会记录实际浏览器版本；安装依赖或通过语法检查仍不代表 18 项浏览器检查通过。

检查报告、浅色/深色/320px 截图提交到 `evidence/`。视觉截图在有限动画结束状态下取证，避免把对白刚出现时的透明首帧误当成空白；动画与暂停行为仍由交互检查验证。

## 原生包

先在固定版本 OctoSense/Rinx 中完成样例和本人私有测试房间的闭环，捕获真实 OnCue 画面。
原生版本使用 `oncue/bundle/`；包内不放源码工具、测试目录或模型/Matrix 凭据。

图标唯一源文件为 `branding/icon.svg`。修改后统一导出，避免网页和原生各画一份：

```bash
python3 oncue/tools/sync_brand_assets.py --bundle
```

在最终包中添加完整 `listing.json`，引用 `assets/icon.svg` 和包内真实原生截图；平台只声明实测平台。
发布者为 OnCue / YCOROY，支持地址为仓库 Issues，数据说明地址为仓库 `oncue/PRIVACY.md` 的 HTTPS 页面。
不能用网页截图代替 Rinx 原生画面。

包的源码、图标、截图或 listing 改动后，重新计算摘要并检查。使用实际宿主锁定的 App Hub 工具：

```bash
hub stamp oncue/bundle
hub check oncue/bundle --allow-unsigned
hub scan oncue/bundle --packet evidence/hub-review.json
```

原始输出和审阅答案保存在包外。Developer 导入、包检查通过、签名和上架是不同结果，逐项如实记录。
按最终摘要重新 Review/Run；宿主运行的是冻结副本，编辑原目录不会更新正在运行的副本。

规则依据为 Rinx 0879548b 引用的 [App Hub 发布契约](https://github.com/OctoSense-org/OctoSense-App-Hub/blob/e8601b80ce104db2e48208094714bdcffdce6b5a/docs/PUBLISHING.md)。
实际协作容器若有外层依赖锁覆盖，以运行时锁定版本的工具结果为准。
