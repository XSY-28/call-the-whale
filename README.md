# 🐋 呼叫蓝色大肥鱼

**通过 Codex 调度 DeepSeek Harness，完成开发、审查与迭代。**

大肥鱼负责开工，Codex 负责验收。

> **完全访问权限说明**
>
> 本 skill 的预期使用模式会给予 dsh 完全访问权限。dsh 执行任务时可能读写本机文件、运行终端命令并访问网络；实际范围取决于 dsh 的权限配置、运行账户及操作系统限制。请仅在你信任并愿意授权的环境中使用。

安装不会修改 dsh 的全局权限设置。首次需要启用完全访问时，Codex 应先说明影响并核对授权；安装本身不是授权。它不是严格限制在项目目录内的安全沙箱，也不能绕过操作系统权限。完全访问不扩大任务范围：仍须保护已有修改，不删除无关文件、不发布其他项目、不操作其他账户。

这是社区项目，**并非 DeepSeek 或 OpenAI 官方产品**。不附带模型额度，不保证所有任务成功或完全无人值守；用户自行承担 dsh 模型接口费用，Codex 的使用限制也独立适用。

| 名称 | 用途 |
|---|---|
| 呼叫蓝色大肥鱼 | 项目品牌和 Codex 中的显示名称 |
| `call-the-whale` | GitHub 仓库名称 |
| `dsh-dev` | Skill 目录名与 SKILL.md 技术标识 |
| `$dsh-dev` | **实际调用方式**，不会因品牌改名而改变 |

**English:** A community skill for the Codex desktop app. Codex delegates development to an already configured DeepSeek Harness through its embedded browser, then checks the actual changes and tests independently. Invocation remains `$dsh-dev`. The intended mode grants dsh full access; model API charges are the user's responsibility. This is not an official DeepSeek or OpenAI product.

## 适用环境与前置条件

**使用本 skill 前，请先自行运行并使用至少一次 DeepSeek Harness（dsh），完成 API key 配置，并确认能够正常发送请求、获得模型回复。**

按照 [dsh 官方说明](https://github.com/deepseek-ai/deepseek-harness)完成首次使用。本 skill 使用已经配置好的 dsh，不负责申请 API key、充值或提取其他应用的凭据。**不要把 key 粘贴到 Codex 对话、仓库文件、Issue 或截图中。**

需要：

- Codex 桌面应用，以及该环境实际提供的**内置浏览器展示与网页交互工具**。仅能加载 skills 或打开链接不够；不能宣称所有 skills 客户端可直接使用。
- 可读取目标项目、执行终端命令和跟进进程的工具权限。
- dsh 当前版本所要求的 Node.js 和 npm/npx；本项目不固定某个作者的运行时或安装路径。
- Python 3.9+，用于标准库辅助脚本；Git 和其他构建/测试工具按目标项目需要提供。

Codex 会先检查工具、实际服务及非敏感模型状态。缺配置或认证失败时，请回到 dsh 完成配置，再继续任务；不会为检查而输出密钥，也不会因界面列出了模型名就宣称接口可用。仅打开页面时不发送模型测试请求。

## 安装

推荐使用 Codex 自带的 [skill-installer](https://github.com/openai/skills/tree/main/skills/.system/skill-installer)。在 Codex 中发送：

```text
请使用 $skill-installer，从 https://github.com/XSY-28/call-the-whale/tree/main/skills/dsh-dev 安装此 skill，保留目录名 dsh-dev。
```

安装器通常将它放到 `$CODEX_HOME/skills/dsh-dev`；未设置 CODEX_HOME 时为 `~/.codex/skills/dsh-dev`。下一轮对话可使用 `$dsh-dev`。以你的安装器报告的实际位置为准，避免在多个技能搜索目录重复安装。

需要固定版本时，将上面链接的 `main` 换成已发布标签，例如 `v0.1.0`。安装包只取 `skills/dsh-dev`，不是整个仓库，也不是名为 `call-the-whale` 的 skill。安装器遇到同名目录会停止，不覆盖旧安装；已有安装请按下面的更新方法处理。

本次实测使用官方安装器已支持的 Git 方法。若下载遇到本机 Python 证书错误，可让 Codex 检查该运行时的证书配置，或使用安装器的 `--method git`；不要关闭 HTTPS 证书验证。

## 第一次使用与快速开始

1. **使用本 skill 前，请先自行运行并使用至少一次 DeepSeek Harness（dsh），完成 API key 配置，并确认能够正常发送请求、获得模型回复。**
2. 安装后，先让 Codex 只打开页面，确认你的桌面环境有需要的浏览器能力：

   ```text
   使用 $dsh-dev，只打开 dsh，不提交开发任务。
   ```

3. 首次委托前阅读并授权预期权限：**本 skill 的预期使用模式会给予 dsh 完全访问权限。dsh 执行任务时可能读写本机文件、运行终端命令并访问网络；实际范围取决于 dsh 的权限配置、运行账户及操作系统限制。请仅在你信任并愿意授权的环境中使用。** 已有覆盖当前范围的有效授权不重复询问，但 dsh 网页和执行工具要求的当次确认仍须遵守。
4. 指定你的项目及验收目标。以下路径都是占位值，替换为自己的绝对路径：

   ```text
   使用 $dsh-dev，在 /absolute/path/to/project 修复登录表单的重复提交问题，保留现有接口，补充并运行相关测试。我理解并授权本次任务使用 dsh 完全访问权限。
   ```

继续已有任务：

```text
使用 $dsh-dev，继续刚才修复登录表单的任务，沿用原会话的项目和验收标准。
```

只打开时，缺少默认项目不会阻止打开，也不会自行提交任务；尚未配置模型时可展示页面供你自行配置，但不宣称模型已可用。继续任务先找原会话，不因当前默认值变化而换项目。任务不唯一或新目录与旧会话冲突时才澄清。

## 项目目录与个人配置

```text
使用 $dsh-dev，将 /absolute/path/to/project 设为默认项目。
使用 $dsh-dev，修改默认项目为 /absolute/path/to/another-project。
使用 $dsh-dev，清除默认项目。
```

当前请求明确指定的目录优先，只对当前任务生效。新任务未指定目录时，读取该用户自己的默认项目；没有默认值先询问，得到答复后再提交。不会把 Codex 当前目录、dsh 启动目录或网页上次 workspace 当默认值。

指定具体文件时保留该文件为任务对象，再从项目资料确认所属根目录；归属不明确时询问，不直接把父目录当项目根。目录不存在或不可访问时说明原因，不静默换项目。提交前必须确认网页实际选中的完整 workspace 路径。

四类目录互相独立：

| 目录 | 内容与生命周期 |
|---|---|
| Skill 安装目录 | `SKILL.md`、references、脚本；可更新/卸载 |
| 目标项目目录 | 用户明确选择或已保存的默认项目；由任务范围约束 |
| 本机配置目录 | `$CODEX_HOME/dsh-dev/config.json`，否则 `~/.codex/dsh-dev/config.json`；只在明确要求设置/修改/清除默认项目时改变 |
| 临时/交接目录 | 临时目录由系统 API 创建；长期交接放获准的项目外私有位置，不依赖会被清理的临时目录 |

[配置示例](examples/project-config.example.json)仅说明格式，不应复制进安装目录或 Git 跟踪文件保存个人配置。设置默认值请使用上述请求或已安装的 `project_config.py`。更新和卸载都保留本机配置及任务交接。

## Codex 与 dsh 如何分工

Codex 读取需求和项目约束、保护已有修改、选择方式并整理提示词；dsh 默认修改代码。Codex 读取实际文件、diff 和运行证据，独立测试/构建/界面验收。dsh 说“完成”只是验收开始；不通过时反馈具体位置、复现步骤、预期与实际结果，继续定点修正。

- **服务与会话：** 先读当前终端输出，再按需查进程、监听和标签页；只有确认 dsh 已就绪才复用。无可用服务时在已确认项目启动当前版本支持的 `npx @deepseek-ai/dsh web --no-open`；只打开且没有项目时可在系统创建的私有临时目录启动，不将它保存为默认项目。采用实际认证网址，在 Codex 内置浏览器打开，不猜端口、重复启动或额外打开系统浏览器。
- **插件：** 先判断是否有具体收益，查实际安装与可信来源，评估兼容性、维护、权限和用法；最少安装，区分候选、已安装、运行可用和任务实测。不为简单任务机械搜索，搜索不到也不阻塞。
- **GitHub 调研：** 成熟功能、陌生集成或复杂设计值得调研时，安排少量高相关候选，核对链接、代码证据、兼容性、维护和许可证；足够后进入实现。stars 不是质量结论，不擅自换技术栈。
- **执行方式：** 根据任务选择单 Agent、普通子 Agent、workflow、Agent Teams，并独立考虑多 Agent 审评。方式可组合，但先核对当前能力；角色、文件职责、并发与汇总明确后才委托。
- **权限与推理：** 每次新会话重新检查完全访问权限。推理默认 High，用户指定其他等级则沿用；模型不支持时报告缺口，不擅自换模型。安装和更新不修改 dsh 全局设置。
- **文件协作：** dsh 写入时 Codex 默认只读验收；要直接修改同批文件先确认停写并交接。多个 Agent 明确文件职责，必要时使用独立 worktree。

## Token 异常、预算与恢复

“token 用完”不代表同一种错误：

| 证据支持的类型 | 行为 |
|---|---|
| 上下文达到上限 | 优先已核实的压缩功能；原会话不能继续才保存精简交接，在同一原项目新建一个后继会话 |
| 单次输出达到上限 | 查回复、工具结果和实际文件；从明确断点只续剩余部分，不重做整个任务 |
| 接口限流 | 依据服务端等待信息与任务预算退避；已有内部重试时不叠加提交，超预算/无进展时停止 |
| 账户额度或余额不足 | 停止无效重试并保存进度；由用户补充额度或决定已授权的备用配置，不充值、不换 key/账户 |
| 证据不足或冲突 | 明确未知，补取最小脱敏证据，不猜测 |

交接记录包含目标、约束、项目/分支、已有修改、完成与未完成项、决策、验证、错误和下一步，不复制全聊天或凭据。恢复前重新核对文件、diff、提交状态和后台任务，避免双写及重复执行；恢复成功不等于任务完成，原验收标准继续适用。

用户预算优先，内部重试、压缩和多 Agent 都可能增加接口费用。没有真实后续执行机制时，不承诺关掉当前 Codex 任务后会自动继续。详细规则见 [恢复参考](skills/dsh-dev/references/recovery.md)。

## 更新与卸载

官方 skill-installer 不覆盖已有目录。为了保留旧副本并明确限定更新范围，本仓库提供一个仅操作技能文件的[本地维护脚本](tools/manage_skill.py)；它不联网、不启动 dsh、不改个人配置或权限设置。

先结束当前 dsh 开发与 Codex 技能维护，再取最新源码：

```sh
git clone https://github.com/XSY-28/call-the-whale.git
cd call-the-whale
# 已有此独立克隆时，在其中执行 git pull --ff-only
python3 tools/manage_skill.py update
```

默认目标与随附安装器一致：`$CODEX_HOME/skills/dsh-dev`，否则 `~/.codex/skills/dsh-dev`。如果实际安装在别处，传 `--skills-dir '/absolute/path/to/skills'`；不要更新另一个未被 Codex 使用的副本。更新前将整个旧 skill 保存到 `$CODEX_HOME/backups/dsh-dev`（默认 `~/.codex/backups/dsh-dev`）中的唯一子目录，保留其中的本地修改；新版本不会自动合并自定义技能代码，需对照备份自行处理。失败时恢复旧副本。

卸载（从技能搜索目录移走并保留备份）：

```sh
python3 tools/manage_skill.py uninstall
```

两种操作均打印实际目标与备份路径，下一轮对话核对是否生效。不会清除默认项目、dsh 会话、用户 profile 或已设置的会话权限；若需要撤回 dsh 权限，请自行在 dsh 中调整。恢复旧版时先停相关任务，再让 Codex 用打印的备份替换同一个 `dsh-dev` 安装目录，保留个人配置。

## 验证范围与平台

完整浏览器工作流仅有 **macOS 上的隔离小任务历史实测**；公开版主要做可移植脚本、安装维护和模拟决策验证，不能外推所有高级模式均已实测。Linux CI 只验证脚本和结构；Windows 未验证，POSIX 权限相关脚本不保证可用。仅 CLI、其他 skills 客户端或缺少内置浏览器工具的环境不能直接运行完整流程。

dsh 已核对版本为 `0.1.5-rc.2`，版本和 UI 变化时必须重新发现能力。workflow/Teams、插件安装回滚、真实 token 故障和多提供方切换未作完整端到端验证。详见 [验证记录](docs/validation.md)与[兼容性参考](skills/dsh-dev/references/compatibility.md)。

开发者可运行：

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
python3 tools/check_package.py
node tests/acceptance.mjs tests/e2e-fixture
node --test tests/e2e-fixture/clamp.test.mjs
```

Git 必须可用；若 PATH 中的 Git 不能执行，可显式设置 `DSH_DEV_TEST_GIT` 指向已验证的 Git 可执行文件。测试只使用临时配置与临时项目，不访问真实 key 或默认项目。测试依赖和贡献方法见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 常见问题

**安装后找不到“呼叫蓝色大肥鱼”？** 检查目录是否仍为 `dsh-dev` 且内部直接有 SKILL.md；用下一轮对话调用 `$dsh-dev`，确认没有重复安装位置。品牌不是调用名。

**能只安装 skill，然后让它帮我配置 key 吗？** 不可以。先自行使用 dsh 成功获得一次模型回复，再交给 skill。认证问题回到 dsh 处理，不在 Codex 或 Issue 中提供密钥。

**为什么权限不是项目内沙箱？** 本 skill 的预期模式就是 Full access。已核对的 dsh 将它映射为 `danger-full-access` 与 `never` 审批策略；系统和运行账户仍限制其实际能力。首次启用需要授权，详情见[官方权限说明](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/interaction/permission-presets/README.md)。

**为什么不直接开始？** 可能缺少项目目录、网页工具、首次配置、权限授权或明确验收信息。Codex 应说明实际缺项；普通开发请求不会自动被转交 dsh。

**运行时断线或限流怎么办？** 继续同一个任务，让 Codex 先查旧会话和后台执行。不要反复点击发送或另开会话；无证据不能判定任务停止。

**如何反馈？** 提供操作系统、Codex/dsh 版本、缺少的工具名称、最小复现、预期/实际行为、脱敏错误 code 和测试结果。路径换成占位值。不要附 API key、认证网址、cookies、完整聊天日志、私人代码或未脱敏截图。敏感问题先按 [SECURITY.md](SECURITY.md)处理。

## 许可证与来源

项目代码、原创规则和文档采用 [MIT](LICENSE)。本项目通过链接参考 dsh 与 Codex 官方接口文档，不打包其源码、运行时、凭据或模型；相应产品仍适用各自许可证与服务条款。来源说明见 [NOTICE.md](NOTICE.md)。
