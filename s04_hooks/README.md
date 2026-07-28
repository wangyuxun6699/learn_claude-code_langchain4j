# s04: Hooks — 在生命周期的每个节点插入逻辑

> LangChain 教学改编版。章节结构与“深入 CC 源码”部分主要参考 [shareAI-lab/learn-claude-code](https://github.com/shareAI-lab/learn-claude-code)。
>
> **Harness 层**：生命周期 — 用户输入、工具前后与结束事件。

[s03](../s03_permission/) → **s04** → [s05](../s05_todo_write/)

---

## 问题

日志、权限、审计与收尾逻辑如果散落在每个工具里，很快会重复并难以组合。

---

## 解决方案

![s04: Hooks — 在生命周期的每个节点插入逻辑](images/hooks-overview.svg)

用 LangChain middleware 装饰器接入 Agent 生命周期，再通过本地 `HOOKS` 注册表支持多个业务回调。

---

## 工作原理：LangChain 版本

```python
@before_agent
def user_prompt_submit(state: AgentState, runtime: Runtime):
    trigger_hooks("UserPromptSubmit", state["messages"][-1].content)

@wrap_tool_call
def tool_hook(request: ToolCallRequest, handler):
    blocked = trigger_hooks(
        "PreToolUse", request.tool_call["name"], request.tool_call.get("args", {})
    )
    if blocked:
        return ToolMessage(content=str(blocked),
                           tool_call_id=request.tool_call["id"], status="error")
    result = handler(request)
    trigger_hooks("PostToolUse", request.tool_call["name"],
                  request.tool_call.get("args", {}), result)
    return result

@after_agent
def stop_hook(state: AgentState, runtime: Runtime):
    trigger_hooks("Stop", state.get("messages", []))
```

这些函数直接放进 `create_agent(..., middleware=MIDDLEWARE)`，不需要改动工具本身。

---

## 本章文件

`code.py` 为当前主版本，并保留详细注释版与精简版。

---

## 试一下

先在仓库根目录准备环境，然后从根目录按模块运行：

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python -m s04_hooks.code
```

> 这些教学 Agent 可以执行命令和修改文件。建议先在测试目录中试用，并认真阅读每次权限提示。

---

## 接下来

s05 使用官方 `TodoListMiddleware` 给复杂任务加入显式进度状态。

<details>
<summary>深入 CC 源码</summary>

> 以下基于 CC 源码 `toolHooks.ts`（650 行）、`hooks.ts`、`stopHooks.ts`、`coreTypes.ts` 的完整分析。

### 一、Hook 事件：不止这 4 个，而是 27 个

教学版只讲了 PreToolUse 和 PostToolUse。CC 实际有 27 个 hook 事件（`coreTypes.ts:25-53`）：

| 类别 | 事件 |
|------|------|
| 工具相关 | `PreToolUse`, `PostToolUse`, `PostToolUseFailure` |
| 会话相关 | `SessionStart`, `SessionEnd`, `Stop`, `StopFailure`, `Setup` |
| 用户交互 | `UserPromptSubmit`, `Notification`, `PermissionRequest`, `PermissionDenied` |
| 子 Agent | `SubagentStart`, `SubagentStop` |
| 压缩相关 | `PreCompact`, `PostCompact` |
| 团队相关 | `TeammateIdle`, `TaskCreated`, `TaskCompleted` |
| 其他 | `Elicitation`, `ElicitationResult`, `ConfigChange`, `WorktreeCreate`, `WorktreeRemove`, `InstructionsLoaded`, `CwdChanged`, `FileChanged` |

教学版只讲 4 个核心事件（UserPromptSubmit、PreToolUse、PostToolUse、Stop），因为它们覆盖了一个完整 agent cycle 的关键节点。其他 23 个都是同样的模式。

### 二、HookResult 常用字段摘录

CC 的 `HookResult`（`types/hooks.ts:260-275`）有 14 个字段，以下是常用字段：

| 字段 | 类型 | 用途 |
|------|------|------|
| `message` | Message | 可选 UI 消息 |
| `blockingError` | HookBlockingError | 阻塞错误 → 注入对话让模型自纠 |
| `outcome` | success/blocking/non_blocking_error/cancelled | 执行结果 |
| `preventContinuation` | boolean | 阻止后续执行 |
| `stopReason` | string | 停止原因描述 |
| `permissionBehavior` | allow/deny/ask/passthrough | hook 返回权限决策 |
| `updatedInput` | Record | 修改工具输入 |
| `additionalContext` | string | 附加上下文 |
| `updatedMCPToolOutput` | unknown | MCP 工具输出修改 |

### 三、关键不变式：Hook 'allow' 不能绕过 deny/ask 规则

这是 CC 权限系统最重要的安全设计（`toolHooks.ts:325-331`）：**hook 返回 allow 时，仍然要检查 settings.json 的 deny/ask 规则**。即使用户的 hook 脚本说"允许"，如果在 settings.json 中禁用了这个工具，操作仍然会被阻止。

教学版没有这个层次，只把 PreToolUse 的非 None 返回值解释为阻止本次工具执行。这在教学场景中够了，但在生产环境中会形成安全漏洞。

### 四、stopHookActive 机制

CC 的 Stop hooks 有一个防无限循环机制（`query.ts:212,1300`）：`stopHookActive` 状态字段。当 stop hooks 产生 blockingError 时，循环带 `stopHookActive: true` 重入下一轮。后续迭代中 stop hooks 看到这个标志就不会再次触发。这防止了一个永不停机的 bug：模型自纠后 stop hook 再次报错 → 模型再自纠 → stop hook 再报错...

### 五、hook_stopped_continuation

PostToolUse hooks 返回 `preventContinuation: true` 时，会产生一个 `hook_stopped_continuation` 附件（`toolHooks.ts:117-130`）。query.ts（L1388-1393）检测到后设置 `shouldPreventContinuation = true`，循环退出。这是 "hook 优雅地让 Agent 停机" 的机制，不是崩溃，是完成。

### 教学版的简化是刻意的

- 27 个事件 → 4 个（UserPromptSubmit/PreToolUse/PostToolUse/Stop）：覆盖 agent cycle 关键节点
- 14 个字段 → 简单的返回值（None = 继续，非 None = 阻止/续跑）：心智负担降到最低
- Hook allow vs deny/ask 不变式 → 省略：教学版没有 settings.json 层
- stopHookActive → 省略：教学版 Stop hook 只做简单续跑，不涉及防无限循环机制

</details>

<!-- translation-sync: zh@v1, en@v0, ja@v0 -->
