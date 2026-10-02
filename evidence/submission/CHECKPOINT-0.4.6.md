# OnCue 0.4.6 开发检查点（2026-10-02）

**性质：按用户要求先保存并推送的开发检查点，不是最终初赛验收版，不提交新的App Hub申请。**

## 版本

- 应用：`oncue-screening-room`，版本 `0.4.6`
- 包路径：`oncue/bundle/`
- 资源BLAKE3：`129c543c1a8fd4093da3eb7e698fa8ca87f6bdec98f5cedc9126b605f5f86fef`
- 签名标识：`oncue.dev`
- 发布者公钥：`50578fd7e0d8ac51a1e9e590835427ce8e71f46dba491860c75ae4e7c8c78042`
- 生产入口SHA-256：`5a658e2dbbbfe8a51eba28bcef998321bff055997692b7c6798a14d8fd103228`
- 此文档所在提交即检查点源码提交；完整SHA在Git历史与本次交付回复中提供，避免自引用提交哈希。

## 已保存的修复

1. 宽窗两列，窄窗上下分区滚动；固定状态提示、多行输入。只用应用内部布局，不改宿主尺寸API。
2. 七块解析不删除内部空块，不按任意位置切`@@@`；标准分隔与纯行末分隔分开处理，拒绝混合歧义结构。
3. 输出要求七个固定顺序标记，拒绝空块、缺块、多块和错序；最多一次格式重试。
4. 原始90秒总预算包含session与重试；回调验证revision、busy、attempt和截止时间。
5. 分页保全CRLF及指定组合字符/emoji簇，避免新增空页。
6. 收紧模型提示，区分来源事实和假设；**此项仍不充分，见已知缺陷**。

## 已验证（不扩大结论）

### 真实OctoScript受控探针：49项通过

[测试源码及重跑说明](<../../oncue/tests/README.md>)；[精确探针、provenance和结果](<../checkpoint-0.4.6/native/>)。

| Suite | 断言数 | 范围 |
| --- | --- | --- |
| parser | 21 | 标准、包装、CRLF、行末分隔、空块、6/8块、正文分隔符、歧义、顺序标记与实际结果映射 |
| pagination | 14 | 字符重拼、CRLF、组合音标、ZWJ/肤色/旗帜/Hangul、阅读器上下限 |
| retry | 8 | 首次失败二次成功、两次失败、停止/编辑/新请求后的旧回复、服务错误边界 |
| deadline | 6 | 完整90秒原期限、80秒首次异常后重试、92秒迟回调不覆盖 |

计时探针观察到停止等待为 **90.0479秒**，总观察约92.997秒。全部保持生产函数原文，fake host只注入受控回调、不外发请求；**不是自然模型超时，也不证明宿主关闭租约机制或视觉可读性**。
Python基础设施6项自检另行通过，不计入49项。

### 真实Rinx部分流程

复用原OctoSense二进制及原账号/模型配置；仅重启主实例加原生测试桥，没有构建/升级。Rinx历史构建基线 `c515e5fc9b6dc22e67f7d551b09fdd793ec685a1`。
二进制SHA-256：`87ed4dccd14bac51222f40c38d4db086911790786b688a68a503002ada64ba25`。
平台：Linux aarch64、X11/Xvfb、软件渲染。其他平台未测，不据此判断比赛违规。

- 在 `matrix.rinx.chat` 已登录宿主里完成Review/Run；OnCue读取授权房间12条原消息。
- 真实session.open/turn.start返回七块，界面逐页读取三路线、建议与摘要。
- 串行测量Rinx外窗 **990×613 → 应用嵌入954×448**，**412×892 → 应用嵌入376×727**。
- 两种尺寸的完整结果文字已通过原生点击逐页读取。**完整视觉、全部控件、播放时序和持久化验收尚未结束**。
- 上述交互对应此检查点相同生产入口；提交时只修正文案listing并更新签名，未重新声称整个包最终视觉通过。

## 已知缺陷与待办

- **模型事实边界仍有问题**：一次真实回合编造“青旅人均80”，建议中继续引用该价格；摘要把用户输入的“杭州”混入原消息事实。当前只提示词防护不充分，不能声称事实核验通过。
- 长文本/空格/复杂emoji全量视觉检查、播放暂停续播/切路线隔离、新版A/B长草稿与关闭重开、两账号关键路径还未完成。
- **当前listing截图及旧演示视频仍是历史版**；保留溯源，不作为0.4.6验收证据。本检查点不替换这些图，不包装成商店最终材料。
- 历史审核packet/七问与依赖说明尚未全部更新；仅作为旧版本材料。最终验收后需要同版scan、截图视频与固定提交材料。
- App Hub #57仍是0.4.4申请；初赛Issue #13仅已登记仓库，不表示本检查点已审核收录。

## 本地开发复现

需要现有Hub/card-host工具、已登录且配置好助手的Rinx宿主；凭据只在宿主中。以下从本仓库根目录执行（工具路径由调用者设置）：

```sh
# 新建副本并移除signature；源码发布包保持签名。
DEV="$(mktemp -d /tmp/oncue-dev.XXXXXX)"
python3 oncue/tools/prepare_dev_bundle.py "$DEV/bundle" --hub "$OCTO_HUB"
```

Rinx：Discover → Mini apps → Import an app → 填上述副本和自己获授权的测试房间 → Review → Run。
OnCue：载入群聊 → 试映下一幕 → 查看三路线/摘要、上下滚动与逐页阅读。副本导入不等于签名目录安装，不发送任何消息。
原生驱动工具在[tools目录](<../../oncue/tools/>)；它们只是测试输入客户端，不是网页作品入口。

## 检查点包检查

最终listing定稿后实际执行 `stamp → sign-manifest → check --publisher-key`，退出码均0：

```text
129c543c1a8fd4093da3eb7e698fa8ca87f6bdec98f5cedc9126b605f5f86fef
signed oncue-screening-room 0.4.6 with oncue.dev
oncue-screening-room 0.4.6 — PASSED
  grants: capabilities {"matrix.read_messages", "matrix.room_info", "octos.session.open", "octos.turn.interrupt", "octos.turn.start", "storage"}, hosts {}, storage 4194304 bytes, agent none
```

**包检查PASS只说明签名/资源准入，不说明以上已知问题已解决。** 不打最终发布tag、不发新的外部Issue/评论，不替用户提交比赛。
