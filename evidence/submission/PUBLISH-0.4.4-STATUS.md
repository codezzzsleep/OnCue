# 0.4.4 官方发布流程进度（2026-10-02）

依据 `OctoScript-App-Design-Flow` README.zh-CN「发布」六步。

| # | 步骤 | 状态 | 证据 |
| --- | --- | --- | --- |
| 1 | 定稿 manifest.json（新版本、最少权限、列全主机）与 listing.json（无占位文本） | **已有** | `oncue/bundle/manifest.json` v0.4.4；`hosts: {}`；6 项能力逐项有可见用途 |
| 2 | `tools/octo shot` 真实截图并逐张查看 | **部分**（用等价方式） | 本环境用真实 `card-host` + 真实 Rinx 截图；`tools/octo` 未在本机获取 |
| 3 | `tools/octo check <bundle>` 直到 `— PASSED` 且只剩未签名警告 | **已过**（等价：`hub check`） | `hub check oncue/bundle --allow-unsigned` → PASSED |
| 4 | `hub scan <bundle> --packet …` 并书面回答七问 | **已完成** | `evidence/hub-review-answers-044.md` |
| 5 | **由人**：`hub keygen` → `hub sign-manifest` → `hub check --publisher-key` | **已完成** | 复用既有发布者密钥（id `oncue.dev`，公钥与 catalog 登记一致）；签名后 digest 不变；`hub check --publisher-key oncue.dev=50578fd7…` → **PASSED** |
| 6 | **由人**：打 tag + 在 `OctoSense-App-Hub/issues` 开 `Submit <app id> <version>` | **tag 已完成；issue 未开** | tag `v0.4.4` → commit `03bb88d30554979bb59f8877d6e84fc6b4fd7bea`（已 push、`git ls-remote` 可见；仓库 https 200 公开可达） |

## 第 6 步未完成的**具体原因**（不是没做，是做不了）

- 本机**没有 `gh` CLI**，`~/.config/gh/hosts.yml`、`~/.netrc`、`~/.git-credentials` **均不存在**，
  环境里**没有 GITHUB_TOKEN**；
- 只有 **SSH 到 github 的身份 `codezzzsleep`** —— 该身份**不能**用来在 `OctoSense-org/OctoSense-App-Hub`
  开 issue（开 issue 需要具备 `issues:write` 的 API token）；
- 另外本机到 `https://github.com/OctoSense-org/OctoSense-App-Hub` 的 HTTPS 探测连续返回 **000**（代理侧不稳），
  即便有 token 也需先确认网络可达。

## 已备好的 issue 正文（可直接粘贴）

完整正文见 `evidence/submission/SUBMIT-ISSUE-0.4.4.md`，含官方要求的全部字段：
仓库 URL、tag、完整 commit SHA、bundle 路径、app id/version、bundle digest、
publisher id 与公钥、**该提交上完整的 `hub check` 输出**、以及**七问答案全文**。

标题应为：`Submit oncue-screening-room 0.4.4`
