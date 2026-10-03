# 来源与署名

呼叫蓝色大肥鱼（call-the-whale）是一个社区维护的 Codex skill。技术标识为 dsh-dev。

本仓库的规则、Python 辅助脚本、测试和示例为本项目开发内容，按根目录 MIT 许可证发布。隔离 clamp 样例是本项目开发验证的简单示例，不是第三方组件。

DeepSeek Harness 与 Codex 是各自权利人的产品。文档中的产品名、包名、命令和错误码用于说明互操作行为，不表示官方背书。官方资料以链接引用并自行概括；未复制或打包第三方实现、SDK、运行时、模型、图标、完整手册或安装器。使用它们时遵守各自许可证和服务条款。

首次安装使用 Codex 随附的 skill-installer，该安装器不包含在本仓库中。完整资料入口见 [兼容性参考](skills/dsh-dev/references/compatibility.md#官方来源)。

本次行为改进参考以下项目的机制并自行实现：

- [chatgpt-delegate](https://github.com/adamallcock/codex-chatgpt-control/blob/main/plugins/codex-chatgpt-control/skills/chatgpt-delegate/SKILL.md)：对话与长任务分流、一次提交后核对实际状态。
- [orchestrate](https://github.com/danielrahman/claude-orchestrate-skill/blob/main/.codex/skills/orchestrate/SKILL.md)：文件职责、阶段产物和逐项独立证据。
- [codex-in-claude](https://github.com/briandconnelly/codex-in-claude)：披露审查覆盖缺口与未知结论。

这些项目不是运行依赖；未复制实现或大段规则，也未引入自动委托、固定模型或强制多 Agent/worktree。参考项目当前已将 codex-in-claude 标为弃用；此处仅保留机制来源，不推荐安装。
