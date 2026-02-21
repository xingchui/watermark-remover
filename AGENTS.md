# AGENTS.md - AI Coding Assistant Guidelines for watermark_remover

本文件用于约束和引导在本代码库中执行的“代理人”式编码任务，确保构建、测试、风格规范和协作流程的一致性。

若仓库中存在 Cursor 规则 (.cursor/rules/) 或 Copilot 指令 (.github/copilot-instructions.md)，请务必将要点融入本文件的对应部分，以便未来代理在执行时可直接遵循。

以下内容覆盖本仓库在代理执行时的默认最佳实践、验收标准以及版本控制下的协作要点。

进度状态（当前阶段）：
- 9 已完成：跨引用检查的修正已将测试引用更新到现有的测试路径
- 10–12 正在执行中：等待实际执行并汇总证据（需在具备依赖的环境中运行 lsp_diagnostics、mypy、pytest）

- Build, lint, test 常用命令（含单测示例）
- 代码风格与导入规范（命名、类型、错误处理、日志等）
- 模块结构与命名约定
- Cursor 规则与 Copilot 指令的整合与管理
- 验证与证据要求
- 会话与任务分解（Todo）和分派机制
- 版本控制与提交建议

- 1) Build、lint、test 命令
- 环境准备（Windows/PowerShell 兼容，亦可在 Unix-like 环境使用）：
-   - python -m venv venv
-   - Windows: .\\venv\\Scripts\\activate
-   - Unix: source venv/bin/activate
-   - pip install -r requirements.txt
- 运行应用（入口假设 main.py）
-   - python main.py
- 运行所有测试
-   - pytest -q
- 运行单个测试（示例）
-   - pytest tests/test_batch_executor.py::test_run_batch_basic -q
- 运行另一个示例单测（集成测试路径示例）
-   - pytest tests/test_integration_batch.py::test_image_batch_integration -q
- 运行子集测试（示例路径，请替换成实际要执行的子集）
-   - pytest tests/path/to/subset -q
- 静态分析/风格检查
-   - flake8 watermark_remover tests
- 类型检查
-   - mypy watermark_remover
- 代码格式化/导入排序
-   - black watermark_remover
-   - isort watermark_remover
- 打包（如 PyInstaller）
-   - pyinstaller build.spec
- Pre-commit 钩子（若配置）
-   - pre-commit run -a

- 2) 代码风格指南
- 语言与约定：
  - Python 3.8+，公有 API 使用类型注解
  - 使用 4 空格缩进，禁止尾部空格，统一 LF 行结
  - 导入分组：标准库、第三方、本地模块，使用 isort
- 命名规范：
  - 类：PascalCase
  - 函数/方法：snake_case
  - 变量：snake_case；常量：UPPER_SNAKE_CASE
  - 私有成员：前导下划线
- 类型注解：对公有 API 进行精准类型标注，尽量避免 Any
- 文档：公有 API 必须具备 docstring，使用 Google 风格
-  错误处理：避免裸露的 except；自定义领域错误如 WatermarkRemoverError
-  日志：使用项目级 logger，避免使用 print
-  测试：避免不确定性，确保测试可重复
-  安全性：避免在代码中硬编码密钥，使用环境变量
-  CI/质量门槛：确保合并前格式化、静态检查通过

### 代码示例
- 典型函数签名和注解示例（简化版）:
  - def remove_watermark(image: np.ndarray, roi: Tuple[int,int,int,int]) -> np.ndarray:
      pass

- docstring 示例（Google 风格）:
  - def remove_watermark(...):
        """去除水印
        参数: image, roi
        返回: 处理后的图片
        """


- 3) 模块结构与约定
- 建议的包结构：
  - watermark_remover.core：核心算法
  - watermark_remover.services：业务逻辑与编排
  - watermark_remover.utils：工具函数
  - watermark_remover.gui：界面相关
- 每个模块暴露清晰的公共 API，避免循环依赖

- 公开 API 暴露原则：
  - core/ 只暴露核心算法接口
  - services/ 提供业务编排和对外服务入口
  - utils/ 提供基础工具、配置、日志等基础能力
  - gui/ 仅通过 services 暴露的能力驱动界面

- 4) Cursor 规则与 Copilot 指引（实际存在性时的整合指引）
- 备注：当前仓库未发现明确的 Cursor/Copilot 规则文件时，保持与 Copilot 的协作偏好一致，后续如有规则再合并要点。
- Cursor 规则（Cursor Rules）
  - 位置：.cursor/rules/
  - 作用：作为持久化的 AI 行为指南，注入到代理上下文作为头部 guardrails
  - 文件格式：Markdown 文件，通常在顶部包含 YAML frontmatter，描述作用域、激活模式等
  - 类型与用法：Always、Auto-attached、Agent-decided、Manual；按需使用
  - 版本化与审阅：纳入 CI/PR，随代码版本控制
  - 示例要点：编码规范、架构约束、测试策略等
- Copilot 指令（GitHub Copilot Instructions）
  - 文件类型：仓库自定义指令，常见路径如 .github/copilot-instructions.md 或 .github/copilot-instructions/xxx.md；组织/仓库/个人三类作用域
  - 作用：为 Copilot 提供持久化的项目上下文与偏好
  - 内容要点：编码规范、首选框架/库、命名约束、错误处理风格、注释/文档风格
  - 取效与维护：纳入版本控制、CI 验证、PR 审核流程
  - 参考资源：GitHub Copilot 官方文档、实践指南等

5) 检索结果与后续工作（外部资料整合）
- 记录外部资料要点，留作后续填充到本节的具体要点
- 当仓库内实际存在规则文件时，提取要点并合并到本节，确保风格一致

6) 验证与证据
- 变更应包含诊断结果、构建状态、测试结果等证据
- 新规则应有触发/应对案例的验证

- 证据模板示例：
-  - lsp_diagnostics: 变更前后诊断输出对比
-  - mypy: 类型检查结果摘要
-  - pytest: 关键用例的执行结果、覆盖率信息
-
- 9) 确保不引用不存在的测试/模块：跨引用检查，移除/修正无效引用
- lsp_diagnostics: 变更前后诊断输出对比
- mypy: 类型检查结果摘要
- pytest: 关键用例的执行结果、覆盖率信息

- 7) 会话与任务管理
- 详细流程：
-   - 每个任务分解为独立的 Todo 条目，明确 atomicity
-   - 与 Atlas/Plan 交互时记录 session_id，用于后续续接
-   - Boulder（计划 Boulder）更新：在开始执行前更新状态，执行中阶段性进度更新，完成后标记完成
-   - 任务完成后立即在 todolist 中标记为 completed，避免批量完成
-   - 任务中断时，保留未完成的 Todo 并在恢复时从中断点继续
- 非平凡任务应创建 Todo，逐项推进；单任务逐步推进，避免一次性完成所有
- 使用 explore/librarian/Oracle 等代理进行并行探索，结果需记录
- 验证通过后再提交最终结果

8) 补充与版本控制
- 示例/模板：提供 3-5 条典型 Patch/模板，便于代理快速落地
-  示例模版1：
-  ```diff
-  *** Begin Patch
-  *** Update File: some_module.py
-  - old_line
-  + new_line
-  *** End Patch
-  ```
-  示例模版2：
-  ```python
-  # 示例代码片段
-  def example():
-      pass
-  ```
- 如有新规则文件，请附上变更说明与影响范围
- 提交前运行 lsp_diagnostics，确保更改不引入类型错误

此 AGENTS.md 将用于指导 watermark_remover 项目的代理式编码任务，确保可追溯、可重复、可审阅。

9) 跨引用检查
- 目标：提交前确认 AGENTS.md 中引用的测试路径或模块路径均存在，避免指向不存在的资源
- 做法：在提交变更前执行引用检查，若发现不存在的引用，则修正或删除相关条目
- 示例：若引用了 tests/test_integration_batch.py::test_image_batch_integration，但实际路径存在，应替换为现有的测试路径

10) 验证清单执行摘要
- 目标：修改后输出一个简短的验证摘要，用于验收
- 步骤：对修改的文件执行 lsp_diagnostics、mypy、pytest 的子集或全量运行，记录关键结果
- 输出格式：简短文本块列出诊断错误/警告数量、测试通过情况

11) 与现有 AGENTS.md 对齐
- 目标：确保新条目风格、用词和结构与仓库现有文档一致
- 动作：统一术语、引导语气、段落结构，必要时合并要点

12) 最终交付与验收
- 目标：整理变更日志、输出验收证据、输出最终 patch
- 步骤：输出 patch diff，附上验收证据截图或文本摘要
- 交付物：更新后的 AGENTS.md、版本说明、验收证据列表
