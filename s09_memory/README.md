# s09: Memory — 跨会话记住重要的事

> LangChain 教学改编版。章节结构与“深入 CC 源码”部分主要参考 [shareAI-lab/learn-claude-code](https://github.com/shareAI-lab/learn-claude-code)。
>
> **Harness 层**：长期记忆 — 检索、注入、抽取与 Markdown 持久化。

[s08](../s08_context_compact/) → **s09** → [s10](../s10_system_prompt/)

---

## 问题

上下文压缩只服务于当前会话；程序重启后，稳定偏好、项目事实和用户反馈仍会消失。

---

## 解决方案

![s09: Memory — 跨会话记住重要的事](images/memory-overview.svg)

本章复用 s08 的 Agent 基础设施，用 `MarkdownMemoryStore` 管理 `.memory/`，并通过 middleware 在模型调用前检索注入、在回合后抽取新记忆。

---

## 工作原理：LangChain 版本

```python
from s08_context_compact import code as s08

class LongTermMemoryMiddleware(AgentMiddleware):
    state_schema = MemoryAgentState

    def before_model(self, state, runtime):
        # 根据当前请求检索最多 MAX_RELEVANT_MEMORIES 条 Markdown 记忆
        # 并追加到本次模型请求的 system context。
        ...

    def after_agent(self, state, runtime):
        # 从本轮对话中抽取值得跨会话保留的信息并更新索引。
        ...

agent = create_agent(
    model=s08.MODEL,
    tools=s08.PARENT_TOOLS,
    system_prompt=s08.PARENT_SYSTEM,
    middleware=[MEMORY_MIDDLEWARE, *s08.PARENT_MIDDLEWARE],
)
```

记忆正文是带 YAML frontmatter 的独立 Markdown 文件，`MEMORY.md` 只保存轻量索引，便于人工检查与版本管理。

---

## 本章文件

- `code.py`：当前主版本。
- `code_commented.py`：详细注释版，解释 Markdown 存储、检索、临时注入、提取和事务式合并。
- `code_uncommented.py`：无教学注释的精简版。

请从仓库根目录用模块方式运行，以便正确导入 s08。

---

## 试一下

先在仓库根目录准备环境，然后从根目录按模块运行：

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python -m s09_memory.code
```

> 这些教学 Agent 可以执行命令和修改文件。建议先在测试目录中试用，并认真阅读每次权限提示。

---

## 接下来

s10 根据真实运行状态动态组装 system prompt。

<details>
<summary>深入 CC 源码</summary>

> 以下基于 CC 源码 `src/` 下 `memdir/`、`services/`、`utils/`、`query/` 的分析，行号已对照核实。

### 源码路径

| 文件 | 行数 | 职责 |
|------|------|------|
| `memdir/memdir.ts` | 507 | 核心：MEMORY.md 定义（`34-38`）、记忆行为指令区分 memory/plan/tasks（`199-266`）、`loadMemoryPrompt()` 三条路径（`419-490`） |
| `memdir/findRelevantMemories.ts` | 141 | Sonnet side-query 选记忆（`18-24` 系统提示、`97-122` 调用逻辑） |
| `memdir/memoryTypes.ts` | 271 | 类型定义，frontmatter 字段 |
| `memdir/memoryScan.ts` | — | 扫描 .md 文件，排除 MEMORY.md，读 frontmatter，最多 200 个，按 mtime 降序（`35-94`） |
| `services/extractMemories/extractMemories.ts` | 615 | forked agent 提取记忆，受限权限，`skipTranscript: true`，`maxTurns: 5`（`371-427`） |
| `services/autoDream/autoDream.ts` | 324 | Dream 整理，四层门控（`63-66` 默认值、`130-190` 门控、`224-233` forked agent） |
| `services/SessionMemory/sessionMemory.ts` | 495 | 会话级记忆管理 |
| `services/compact/sessionMemoryCompact.ts` | — | session memory 轻量摘要，阈值 10K/5/40K（`56-61`） |
| `utils/attachments.ts` | — | 注入预算：200 行 / 4096 字节每文件，60KB 每 session（`269-288`）；按 query 找相关 memory（`2196-2241`） |
| `query.ts` | — | memory prefetch 每轮启动（`301-304`），非阻塞收集（`1592-1614`） |
| `query/stopHooks.ts` | — | stop hook fire-and-forget 触发提取和 Dream（`141-155`） |

### 记忆选择：LLM 选，不是 embedding

CC 用 **Sonnet 本身来选**（`findRelevantMemories.ts`），不是 embedding 向量相似度：

1. `memoryScan.ts` 扫描 `.memory/` 下所有 `.md` 文件（排除 MEMORY.md），最多 200 个，按 mtime 降序
2. 把 `name` + `description` 列成清单
3. 发给 Sonnet side-query："根据名称和描述选出真正有用的记忆（最多 5 个）。不确定就不要选。"
4. Sonnet 返回 `{ selected_memories: ["file1.md", ...] }`
5. 选中文件读取完整内容（每文件 ≤ 200 行 / 4096 字节），注入上下文。单 session 总预算 60KB

每轮用户 turn 开始时，`query.ts:301-304` 启动 memory prefetch（异步）；工具执行后 `1592-1614` 非阻塞收集结果，不卡主流程。

### 提取时机：stop hook，不是 autoCompact 后

触发位置（`stopHooks.ts:141-155`）：在 `handleStopHooks()` 中，fire-and-forget 触发提取和 Dream。教学版把提取放在 `stop_reason != "tool_use"` 分支里，方向一致。

CC 的提取通过 forked agent 执行（`extractMemories.ts:371-427`）：受限权限、`skipTranscript: true`、`maxTurns: 5`。还有重叠保护：如果主 Agent 已经写入了记忆文件，跳过提取。

### 记忆文件格式

CC 用 Markdown + YAML frontmatter，和教学版一致。四种类型：`user`、`feedback`、`project`、`reference`。

`memdir.ts:34-38` 定义索引约束：`MEMORY.md` 最多 200 行 / 25KB。`memdir.ts:199-266` 构建记忆行为指令，明确区分 memory、plan、tasks。存储位置：`~/.claude/projects/<sanitized-git-root>/memory/`。

### Dream：四层门控

不是"空闲时触发"或"数量够了就合并"，而是四层门控（`autoDream.ts`，默认值 `63-66`，门控逻辑 `130-190`）：

1. **时间门控**：距上次合并 ≥ 24 小时
2. **扫描节流**：避免频繁扫描文件系统
3. **会话门控**：自上次合并以来修改了 ≥ 5 个会话 transcript
4. **锁门控**：没有其他进程正在合并（`.consolidate-lock` 文件）

合并本身通过 forked agent 执行（`224-233`）：定位 → 收集近期信号 → 合并写文件 → 剪枝更新索引。锁文件 mtime 就是 lastConsolidatedAt。崩溃恢复：1 小时后锁自动过期。

### User Memory vs Session Memory

| | User Memory | Session Memory |
|---|---|---|
| 持久性 | 跨会话 | 单会话 |
| 存储 | `memory/` 下多个 .md 文件 | `session-memory/<id>/memory.md` |
| 加载到 | system prompt | compact 摘要 |
| 用途 | 跨会话的知识积累 | 跨 compact 的上下文连续性 |

sessionMemoryCompact（s08 中提到的机制）正是使用了 Session Memory：autoCompact 前先读 session memory 文件，如果内容足够（≥ 10K token、≥ 5 条文本消息、≤ 40K token，`sessionMemoryCompact.ts:56-61`），就用它做摘要，不调 LLM。

### 真实实现比教学版复杂的地方

- **Feature flags**：记忆相关功能有多层 feature gate 控制
- **Team memory**：团队共享记忆，`loadMemoryPrompt()` 有专门路径（教学版未涉及）
- **KAIROS**：时机感知的记忆提取策略，`loadMemoryPrompt()` 中 daily-log 模式
- **Prompt cache**：记忆注入需要考虑 prompt cache 的 TTL，避免每次都重写 system prompt 的大段内容
- **文件锁**：多进程并发时的锁机制
- **Memory prefetch**：异步预取，不阻塞主流程

### 教学版的简化是刻意的

- LLM side-query → LLM side-query + 关键词降级：教学版保留了 LLM 选择，加了降级路径
- 记忆 JSON → Markdown + frontmatter：教学版与 CC 一致
- stop hook 触发 → `stop_reason != "tool_use"` 分支：方向一致
- 四层门控 → 文件数阈值：教学版没有 transcript 系统和多会话概念
- forked agent + 受限权限 → 直接调用：教学版没有子进程隔离

</details>

<!-- translation-sync: zh@v1, en@v1, ja@v1 -->
