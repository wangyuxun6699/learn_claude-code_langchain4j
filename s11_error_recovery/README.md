# s11: Error Recovery — 出错了，自己恢复

> LangChain 教学改编版。章节结构与“深入 CC 源码”部分主要参考 [shareAI-lab/learn-claude-code](https://github.com/shareAI-lab/learn-claude-code)。
>
> **Harness 层**：韧性 — 分类错误、退避重试、降级模型与上下文恢复。

[s10](../s10_system_prompt/) → **s11** → [s12](../s12_task_system/)

---

## 问题

真实模型 API 会限流、过载、超时、截断输出或拒绝过长上下文。直接异常退出会丢掉整个 Agent 回合。

---

## 解决方案

![s11: Error Recovery — 出错了，自己恢复](images/error-recovery-overview.svg)

当前 LangChain 实现已完成三条恢复路径及 `AgentMiddleware` 接线：输出截断时执行 8K→64K 升级与最多 3 次续写，上下文超限时响应式裁剪并重试一次，遇到 429/529 时按 `Retry-After` 或指数退避重试，并在连续 3 次 529 后切换备用模型。`create_agent` 继续负责标准工具循环。

---

## 工作原理：LangChain 版本

```python
PRIMARY_MODEL = ChatOpenAI(
    model=MODEL_ID, api_key=API_KEY, base_url=BASE_URL,
    max_retries=0, timeout=120,
)
FALLBACK_MODEL = (
    build_model(FALLBACK_MODEL_ID) if FALLBACK_MODEL_ID else None
)

def retry_delay(attempt: int, retry_after: float | None = None) -> float:
    if retry_after is not None:
        return retry_after
    base = min(BASE_DELAY_SECONDS * (2 ** attempt), MAX_DELAY_SECONDS)
    return base + random.uniform(0, base * 0.25)

class RecoveryAgentState(AgentState):
    recovery: NotRequired[dict[str, Any]]
```

这里关闭 SDK 自带重试，避免它与教学恢复层重复重试。恢复状态会在一次用户请求的模型/工具循环中持续保留，并在下一条用户请求开始前自动重置。未配置 `FALLBACK_MODEL_ID` 时不会创建备用客户端，连续 529 将继续使用主模型退避重试。

---

## 本章文件

- `code.py`：默认可运行版本，与无注释版逻辑一致。
- `code_uncommented.py`：便于直接阅读完整控制流的精简版本。
- `code_commented.py`：逐段解释状态、错误分类、重试和消息回写的详细注释版。

---

## 试一下

先在仓库根目录准备环境，然后从根目录按模块运行：

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python -m s11_error_recovery.code
```

也可以分别运行两个学习版本：

```powershell
python -m s11_error_recovery.code_uncommented
python -m s11_error_recovery.code_commented
```

> 这些教学 Agent 可以执行命令和修改文件。建议先在测试目录中试用，并认真阅读每次权限提示。

---

## 接下来

s12 及以后尚未实现，目录中仅放置空 `code.py` 占位。

<details>
<summary>深入 CC 源码</summary>

> 以下基于 CC 源码 `query.ts`（1729 行）、`services/api/withRetry.ts`（822 行）、`query/tokenBudget.ts`（93 行）、`utils/tokenBudget.ts`（73 行）的分析。

### 一、十几种 reason/transition（不只是 3 条）

教学版讲了 3 种最常见的恢复模式。CC 实际有十几种 reason/transition，每轮 LLM 调用后都会判断：

| reason/transition | 教学版对应 | CC 行为 |
|---|---|---|
| `completed` | 正常完成 | 返回结果 |
| `next_turn` | 正常工具调用 | 继续下一轮工具执行 |
| `max_output_tokens_escalate` | 路径 1 | 8K→64K 升级 |
| `max_output_tokens_recovery` | 路径 1 续写 | 续写提示（最多 3 次） |
| `reactive_compact_retry` | 路径 2 | reactive compact → 重试 |
| `prompt_too_long` | 路径 2 | 同上 |
| `collapse_drain_retry` | 未展开 | context collapse 先提交暂存 |
| `model_error` | 未展开 | 重试 |
| `image_error` | 未展开 | `ImageSizeError` / `ImageResizeError` 专门处理 |
| `aborted_streaming` | 未展开 | 流式中止恢复 |
| `aborted_tools` | 未展开 | 工具中止 |
| `stop_hook_blocking` | 未展开 | 注入 blocking error → 模型自纠 |
| `stop_hook_prevented` | 未展开 | hooks 阻止 |
| `hook_stopped` | 未展开 | hook 停止执行 |
| `token_budget_continuation` | 未展开 | token 用量 < 90% 时继续 |
| `blocking_limit` | 未展开 | 阻塞限制 |
| `max_turns` | 未展开 | 达到最大轮次 |

教学版只展开了前 5 种（最常见的），其余各有专门处理逻辑。

### 二、指数退避的精确公式

CC 的退避延迟（`withRetry.ts:530-548`）：

```
delay = min(500 × 2^(attempt-1), 32000) + random(0~25%)
```

| 尝试 | 基础延迟 | + 抖动 |
|------|---------|--------|
| 1 | 500ms | 0-125ms |
| 2 | 1000ms | 0-250ms |
| 4 | 4000ms | 0-1000ms |
| 7+ | 32000ms（上限） | 0-8000ms |

如果服务器返回 `Retry-After` header，优先用那个值。

### 三、CONTINUATION 提示原文

CC 的续写提示（`query.ts:1225-1227`）：

```
Output token limit hit. Resume directly — no apology, no recap of what
you were doing. Pick up mid-thought if that is where the cut happened.
Break remaining work into smaller pieces.
```

Token budget 的 nudge 提示（`tokenBudget.ts:72`）：

```
Stopped at {pct}% of token target. Keep working — do not summarize.
```

### 四、流式错误处理

CC 的流式路径中，可恢复的错误（413、max_tokens、media error）在 streaming 期间**被暂扣不展示**（`query.ts:788-822`）——SDK 消费者看不到，只有恢复逻辑能看到。等 streaming 结束后才判断是否需要恢复。

### 五、529 → Fallback Model 切换

连续 3 次 529 过载错误后（`MAX_529_RETRIES = 3`），CC 自动切换到 fallback model（如 Opus → Sonnet）。切换时清除所有 pending 消息和 tool 结果，给用户展示 "Switched to {model} due to high demand"。

### 六、Diminishing Returns 检测

Token budget 的"继续"不是无限的。当连续 3 次 continuation 且 token 增量 < 500 时，系统判断"继续也没有实质性产出"，停止 continuation（`tokenBudget.ts:60-62`）。

</details>

<!-- translation-sync: zh@v1, en@v1, ja@v1 -->
