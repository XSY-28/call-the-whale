# 开发与验证

仓库中的可安装技能位于 `skills/dsh-dev`。品牌可以出现在界面和文档中，技术标识、目录名和调用名必须保持 dsh-dev / `$dsh-dev`。

Python 辅助脚本只依赖标准库，面向 Python 3.9+ 的 POSIX 环境；Node 用于隔离开发样例。测试需可用的 Git；可以用 `DSH_DEV_TEST_GIT` 指定路径，不在源码中写入个人运行时位置。

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
python3 tools/check_package.py
node tests/acceptance.mjs tests/e2e-fixture
node --test tests/e2e-fixture/clamp.test.mjs
```

`tools/check_package.py` 校验品牌/技能元数据、相对引用、目录结构和常见敏感信息模式；它不是完整秘密扫描器。发布前还须人工审查全部待推送文件、Git 历史和提交元数据。不要复制本地历史报告、真实配置或原始终端日志来充当验证材料。

可使用 Codex 自带 skill-creator 的 quick_validate 补充格式检查；该工具可能需要其自身依赖，不属于此 skill 的运行时依赖。不要为了验证触发真实限流/余额不足或安装不必要的 dsh 插件。

模拟错误、真实临时文件/进程检查和真实 dsh 网页端到端运行必须分别报告。PR 应写清具体行为变化、验证命令及未验证范围；新增平台支持需要真实证据，不能仅因单测通过就宣称支持完整桌面流程。

更新与卸载只作用于安装目录，用户配置与交接不能被覆盖。请优先维护简明 SKILL.md，把必要细节放在按需 references 中。
