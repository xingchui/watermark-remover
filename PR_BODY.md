## Summary
- Enhanced AGENTS.md with CI-based verification workflow for AGENTS.md. Introduced automated validation script and GitHub Action to verify changes.

## Changes
- AGENTS.md: augment sections 9-12 (cross-reference checks, verification digest, alignment, final acceptance).
- .sisyphus/todos/improve-agents-md-todos.md:新增执行状态跟踪条目（9 in_progress，10-12 待办）
- tools/verify_agents.sh: 新增 CI/local 验证脚本，执行 pytest 子集、mypy、flake8 的快速检查
- .github/workflows/verify-agents.yml: CI 工作流，cite verify_agents.sh 的执行

## Verification
- CI 将在 PR/Push 时执行 verify-agents 流程，输出：pytest 子集、mypy、flake8 的结果以及跨引用修正摘要。
- 本地复现：在具备依赖的环境下执行 bash tools/verify_agents.sh

## Patch/Verification Artifacts
- AGENTS.md 的最终版本文本
- .sisyphus/todos/improve-agents-md-todos.md 的状态更新
- tools/verify_agents.sh 验证脚本
- .github/workflows/verify-agents.yml CI 配置

## Reproduce
- 本地复现：执行 bash tools/verify_agents.sh（需预安装 pytest/mypy/flake8）

**Note**: 如需修改 PR Body，请在后续提交中更新 PR_BODY.md
