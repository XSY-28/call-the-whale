# 兼容性、前置能力与官方来源

这是面向 Codex 桌面应用的 skill，不是 dsh 插件或独立执行器。公开包不包含用户的 dsh 配置、模型、插件清单、服务地址、会话记录或默认项目。

## 运行前逐项检查

| 能力 | 如何确认 | 缺失时 |
|---|---|---|
| 项目读取与终端执行 | 当前工具可读取目标文件、执行命令并跟进运行会话 | 说明具体工具或权限缺项，不声称已启动/验收 |
| Codex 右侧浏览器展示 | 当前工具可创建或展示内置标签，并确认实际可见状态 | 不用系统浏览器代替成功；提示使用具备该能力的 Codex 桌面环境 |
| 网页交互 | 当前工具文档允许读取页面、操作真实控件、核对状态 | 仅能打开链接不够；提示启用/提供相应浏览器交互能力，不编造工具或插件安装命令 |
| Node.js、npm/npx 与 dsh | 从当前 PATH、包元数据、进程和当前版本帮助核实 | 使用官方安装说明；不依赖作者的缓存、运行时或源码目录 |
| dsh 首次配置 | 用户已自行运行成功；网页显示已选模型/提供方及非敏感配置状态 | 提示用户回到 dsh 配置并确认正常回复；不索取 key，不代购额度 |
| Python 3.9+ | 发现可用 Python 命令，辅助脚本只依赖标准库 | 说明辅助脚本缺少运行时；不要把某个私有虚拟环境当依赖 |
| 项目自身工具 | 从项目指令和配置核实 Git、构建、测试及依赖 | 按项目需要补齐或说明阻塞，不能伪造测试通过 |

工具名、schema 和界面可变。[连接参考](connection.md) 的名称只是已使用过的例子。查到包不等于运行可用；仅看进程、HTTP 状态或模型名不等于 dsh 就绪。只打开页面不发模型测试，开发请求才自然验证模型连接；出现未配置/认证失败就暂停，等待用户在 dsh 完成配置。

## 平台与版本范围

- macOS：已进行过 Codex 内置网页发现/复用、隔离小任务开发及验收；公开版的辅助脚本和安装维护另有隔离测试。历史小任务不证明所有版本、权限模式和高级模式都已实测。
- Linux：Python 辅助脚本可在具备相应 POSIX 能力的环境测试；CI 结果只证明脚本与包结构，不代表 Codex 桌面浏览器流程已可用或已验证。
- Windows：本项目尚未验证；Python 配置写入使用 POSIX 文件权限接口，不能宣称原样支持。没有添加未经验证的 PowerShell/进程发现分支。
- CLI-only、远端执行器、其他支持 skills 的客户端：如果缺少 Codex 内置浏览器展示和交互能力，不能直接运行完整流程；不要静默降级为另一个产品的自动化。

已核对的 dsh 包版本为 `0.1.5-rc.2`。这是一条版本证据，不是强制安装/锁定版本或“最新版”承诺。官方 master 可能领先已安装版本，workflow、Teams、权限及恢复接口须现场再查。

## 权限与模型选择

核对过的 Web UI 将 Full access 显示为“完全权限”，内置 preset 为 `danger-full-access`，组合 sandbox 模式 `danger-full-access` 与审批策略 `never`。它不是严格限制在项目目录内的安全沙箱，也不能绕过运行账户、操作系统或执行工具的限制。自定义 preset 的名字不保证含义相同，需检查实际配置与回显。

当前会话通过权限控件/`/permission` 选择；General 设置中的默认值只影响后续新会话，不会修改已有会话。完全权限的网页选择包含显式风险确认，以宿主状态回显为准。安装/更新本 skill 不改这些设置；首次使用说明影响并根据用户授权操作，保留当次工具确认要求。

推理等级由模型公开的选项决定。High 是 skill 的默认目标，用户指定等级优先；模型不支持时报告缺口，不擅自换模型。已核对版本中选择作用于下一请求，不能宣称已改变运行步骤。

## Token 恢复能力核对

- `dsh-command-compact` 提供无参数 `/compact`，要求空闲；命令输入不进入模型聊天，但摘要可产生辅助模型调用。运行中、无可压缩历史、保存失败均不能当作压缩成功。
- `dsh-compaction-basic` 支持按配置启用的自动压力压缩和上下文超限恢复；不是所有组成/preset 都启用。它不能缩小任意系统/工具定义或巨大单元；失败后也可能已有持久裁剪，须检查实际状态。
- `dsh-llm` 使用 `CONTEXT_WINDOW_EXCEEDED`、`QUOTA` 等归一化码；DeepSeek adapter 将输出 `length` 映射为 `max-tokens`。官方 DeepSeek 的 402/429 含义不能套用到未知代理。
- `dsh-llm-retry` 可在原 turn 的失败步骤重试。normal 有限，always 可能持续重试永久错误；日志的 retry 安排不证明已经成功。服务端等待、内部重试和任务总预算必须同时检查。
- 未核实可供本 skill 使用的余额查询或自动跨会话恢复接口，不编造命令。需要迁移时走网页会话操作、精简交接和独立文件核验。

## 官方来源

只引用接口与行为说明，不复制整份第三方文档。后续使用前核对当前版本：

- [dsh 官方项目及首次运行入口](https://github.com/deepseek-ai/deepseek-harness)
- [dsh 官方文档](https://deepseek-harness.github.io/deepseek-harness/)
- [CLI 参考](https://github.com/deepseek-ai/deepseek-harness/blob/master/apps/cli/reference/README.md)
- [Web app](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/bundle/web-app/README.md)
- [权限预设](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/interaction/permission-presets/README.md) / [Web 权限界面](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/client/ui-permission-presets/README.md)
- [模型选择](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/client/ui-model-selection/README.md)
- [Subagent](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/subagent/tool-subagent/README.md) / [Workflow](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/workflow/tool-workflow/README.md) / [Agent Teams](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/experimental/agent-team-profile/README.md)
- [目录选择器 auto](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/host/directory-picker-auto/README.md) / [browse](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/host/directory-picker-browse/README.md)
- [压缩命令](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/compaction/command-compact/README.md) / [压缩后端](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/compaction/compaction-basic/README.md)
- [请求重试](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/llm/llm-retry/README.md) / [DeepSeek API 错误码](https://api-docs.deepseek.com/zh-cn/quick_start/error_codes/)
- [OpenAI skill-installer](https://github.com/openai/skills/tree/main/skills/.system/skill-installer)
