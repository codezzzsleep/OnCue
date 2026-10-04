# OnCue 0.4.7：原生运行指南

在 Rinx 小程序宿主（OctoSense `6c4746f` + Rinx `c515e5f`，构建组合见[依赖说明](DEPENDENCIES.md)）中装载与验收。

## 1. 生成未签名开发副本

Rinx Developer 导入按设计拒绝发布签名，所以用副本；发布包本身不动。

```sh
. /root/hackthon/refs/octo-env.sh
DEV_ROOT="$(mktemp -d /tmp/oncue-dev.XXXXXX)"
python3 oncue/tools/prepare_dev_bundle.py "${DEV_ROOT}/bundle" --hub "$OCTO_HUB"
```

destination 本身就是包目录（直接含 `manifest.json`），stamp 和 unsigned check 已由工具完成。

## 2. 在 Rinx 中导入与授权

1. **Discover → Mini apps → Import an app**（Developer 入口）。
2. 包路径填打印出的目录；房间填授权的 Matrix 房间 ID。
3. **Review**：核对名称、版本、Local unsigned 标识、当前账号、Allowed room 与六项服务。
4. **Run**：为当前账号与实例授权。每次打开都重新授权，关闭即撤销。

打开默认进入样例舞台（虚构数据，明确标注）；点 **载入群聊** 才读取真实房间。

## 3. 验收路径

- **载入群聊**：读取最近文本消息（上限 12 条），逐条翻看，长消息分页。
- **试映下一幕**：输入台词，真实助手回合按七节协议生成三路线；等待上限 90 秒。
- **摘要**：原文摘录逐字核对（助手只选编号，应用取回原文）。
- **播放**：播放/暂停/下一句/重播；切路线后旧计时器不推进新路线。
- **草稿**：用这句 → 修改 → 存 A/存 B → 取回对照；写入后回读比对字节。
- **重开**：Back 关闭 → 重新导入 → 草稿自动恢复到编辑框。
- **失败态**：无房间绑定、空房间、助手不可用、协议不合规、等待超时均有明确状态提示。

全程不向 Matrix 房间发送消息。

## 4. 记录

每项验收用新目录保存：源 hash、实际窗口尺寸、步骤与结果、截图。自动化工具与许可开关见[工具指南](TEST-TOOLS.md)；受控 VM 测试见[测试指南](../tests/README.md)。
