# 项目选择与本机默认目录

目录选择是提交前置条件。先确定目标，再读项目约束和基线；不能从 Codex cwd、dsh 启动 cwd 或网页上次选中项推断用户默认项目。

## 选择规则

| 请求 | 应使用的项目 / 待补信息 |
|---|---|
| 新任务，当前请求明确指定项目目录 | 使用该目录；即使不可用也不回退默认值 |
| 新任务，指定具体文件 | 保留文件为任务对象，确认所属项目根；归属未确定前不使用默认项目 |
| 新任务，未指定目录或文件 | 读取独立本机配置；无默认值则询问本次项目，等待答复后才提交 |
| 继续已有任务 | 核实原会话项目并沿用；默认值不参与选择 |
| 继续任务，同时新指定不同目录 | 说明两者冲突并询问；不切换原会话、不直接继续、不自行另开任务 |
| 只打开 | 缺少默认目录不阻止打开；需要选择项目或提交时再补齐目录信息 |
| 设置 / 修改 / 清除默认项目 | 仅执行用户明确要求的配置变更，不因此启动 dsh 或提交任务 |

**文件归属：** 先读路径周围适用的项目指令、仓库根、包/构建入口和项目说明。Git 根是证据之一，不能在 monorepo、嵌套仓库或多项目目录中机械等同于任务 workspace；文件父目录也不等于项目根。证据唯一时自主确认并说明；仍有歧义时询问“这个文件属于哪个项目目录？”。只指定文件的请求不能被现有默认项目接管。脚本不会猜测根目录，`--file-project` 只能传已确认的归属。

路径先转为有上下文依据的绝对路径；相对路径无明确参照时询问。每次使用前检查存在、目录类型、可读取/进入；不要求所有任务预先具有写权限。不存在、外置卷未挂载或访问受限时，说明具体原因并询问，不创建替代目录、不切换默认、不扩大权限。辅助脚本只检查 Codex 当前进程的访问能力，dsh 的权限/实际访问仍需网页核验。

**网页核验：** 用当前受支持 UI 读取目标 workspace 的完整路径，必要时打开详情或目录选择器；同名文件夹不足为证。规范化绝对路径和符号链接后比较。新任务可选择已确认的目标项目后重查；继续任务必须同时核对会话身份与原项目。网页选错时不发送任务，记录或默认配置不能代替此检查。

询问目录后的答复只用于本次任务。只有答复另外明确“设为默认”等持久化意图，才调用 `set`。配置、目录或会话冲突未解决前，可以只读收集证据；不得提交、修正提交或重放开发任务。

## 独立配置

路径由脚本计算：`$CODEX_HOME/dsh-dev/config.json`；未设置 `CODEX_HOME` 时使用 `~/.codex/dsh-dev/config.json`。不硬编码用户项目，不把配置复制到 skill、项目仓库或交付包。它与 dsh 自己的 profile/workspace 配置分开，不保存密钥或认证数据。

schema 1 仅包含 `schema` 和 `default_project`。`set` 先验证目录，再原子替换配置，文件权限 0600、新建配置目录 0700；失败不覆盖原值。无默认时 `show/resolve` 不创建文件。未知版本、损坏配置和配置符号链接明确报错，不静默重置；用户明确清除时可以删除损坏的普通配置文件。`clear` 只删这个配置文件，保留项目、dsh workspace 和会话。

不应为了日常临时选择执行 `set`。`--user-requested` 是防误调用标志，不能替代用户明确的保存/修改/清除请求。文件系统审批按当前环境处理，配置脚本不能绕过审批。

## 脚本用法

以本 skill 所在目录为参照，使用当前可用 Python 3.9+；下例占位路径替换为真实确认的绝对路径，不把示例作为默认值。

```sh
python3 scripts/project_config.py show
python3 scripts/project_config.py set --project '/absolute/project' --user-requested
python3 scripts/project_config.py clear --user-requested

# 显式目录；不读、不改默认配置
python3 scripts/project_config.py resolve --mode new --project '/absolute/project'
# 无显式目录的新任务；仅读取默认配置
python3 scripts/project_config.py resolve --mode new
# 文件归属经确认后，保留具体任务文件
python3 scripts/project_config.py resolve --mode new --file '/absolute/project/src/file.py' --file-project '/absolute/project'
# 恢复：只用原会话核实的目录
python3 scripts/project_config.py resolve --mode resume --session-project '/absolute/project'
# 仅打开；不依赖默认配置
python3 scripts/project_config.py resolve --mode open
```

取得实际网页路径后，在同一次解析参数中追加 `--web-workspace '/observed/absolute/project'`。不得把目标路径原样抄入该参数冒充 UI 观察；脚本不会读取浏览器。

输出为 JSON：`project`、`source`（explicit/file_confirmed/default/session）、可选 `task_file` 和 `reason`。`candidate_project` 是待检或出错路径，不表示可用。`needs_input` 表示需按原因补齐/澄清；`needs_workspace_check` 表示需核验或纠正网页选择；两者退出码 2，`can_submit: false`。`ready` 仅说明目录检查通过，仍须通过会话身份、权限、推理等级、范围与去重等原有检查；`open_only` 允许打开而不允许提交。`may_open: true` 不是开发授权。读取/保存/清除成功退出 0，不表示 dsh 已启动。

测试一律将全局选项 `--config '/absolute/temp/config.json'` 放在子命令前，或把 `CODEX_HOME` 指向临时目录；绝不为测试设置、清除或迁移用户真实默认值。

## 调用示例

- “使用 $dsh-dev，将 `/项目完整路径` 设为默认项目。”
- “使用 $dsh-dev，修改默认项目为 `/另一个项目完整路径`。”
- “使用 $dsh-dev，清除默认项目。”
- “用 dsh 在 `/临时项目完整路径` 修复这个问题。”——仅本次生效。
- “继续 dsh 上次的任务。”——先找原会话及其项目，忽略当前默认值。
