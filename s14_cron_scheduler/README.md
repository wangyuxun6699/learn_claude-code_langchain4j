# s14: Cron Scheduler — 按时间表生产工作

[s13](../s13_background_tasks/) → **s14** → [s15](../s15_agent_teams/)

> 按时间表生产工作，让调度与执行解耦。

本章参考 [`shareAI-lab/learn-claude-code/s14_cron_scheduler`](https://github.com/shareAI-lab/learn-claude-code/tree/main/s14_cron_scheduler)，使用 **LangChain 1.x + LangGraph** 重新实现同一组 Cron Scheduler 概念。参考仓库直接维护 Anthropic 消息和工具循环；本项目复用 s13 的 `create_agent`、后台任务 middleware 与工具集合，把重点放在定时调度、队列交付和持久化边界上。

## 问题

s13 已经能把慢命令送到后台，但所有工作仍需用户主动触发。类似下面的任务不应该要求人反复发送同一个 prompt：

- 每天 09:00 运行测试；
- 每 10 分钟检查一次 CI；
- 下一个整点提醒检查部署状态。

定时任务还带来新的并发问题：Agent 可能正在回答用户，调度器不能打断当前回合；模型执行较慢时，时间检查也不能停下来等待。

## 解决方案

本章把定时工作拆成四层：

```text
Scheduler（每秒检查时间）
    ↓ append
cron_queue（保存已到期任务）
    ↓ Agent 空闲时取出
Queue Processor（自动拉起 Agent 回合）
    ↓ HumanMessage
Consumer / LangGraph Agent（执行 prompt）
```

Scheduler 只负责“什么时候到期”，不直接调用模型；Queue Processor 只负责“Agent 是否空闲”；真正的工具选择和执行仍由 LangGraph Agent 完成。

## 核心数据结构

每个定时任务由 `CronJob` 表示：

```python
@dataclass
class CronJob:
    id: str
    cron: str
    prompt: str
    recurring: bool
    durable: bool
```

- `cron`：5 段式表达式；
- `prompt`：触发后注入 Agent 的消息；
- `recurring=True`：周期任务，触发后继续保留；
- `recurring=False`：一次性任务，首次触发前从注册表删除；
- `durable=True`：写入 `.scheduled_tasks.json`，重启后恢复定义；
- `durable=False`：仅在当前 Python 进程中存在。

进程内还维护三份共享状态：

```python
scheduled_jobs: dict[str, CronJob]   # 任务定义
cron_queue: deque[CronJob]           # 已到期、待交付任务
last_fired: dict[str, str]           # 同一分钟去重标记
```

它们统一由 `cron_lock` 保护。用户回合和自动定时回合则通过 `agent_lock` 串行执行，避免同时修改 LangGraph 会话状态。

## Cron 表达式

格式为：

```text
分钟 小时 日 月 星期
```

本教学版支持 `*`、`*/N`、单个数字、`N-M` 和逗号列表：

| 表达式 | 含义 |
|---|---|
| `* * * * *` | 每分钟 |
| `*/5 * * * *` | 每 5 分钟 |
| `0 9 * * *` | 每天 09:00 |
| `0 9 * * 1-5` | 周一至周五 09:00 |
| `0 9 1,15 * *` | 每月 1 日和 15 日 09:00 |

星期使用 `0=周日`、`1=周一`、……、`6=周六`。当“日”和“星期”同时被具体值约束时，采用标准 cron 的 **OR** 语义：任一字段匹配即可。

时间按运行 Python 进程的本机时区解释。

## 调度与交付

### 1. Scheduler

`cron_scheduler_loop()` 每秒轮询一次。匹配后用包含日期的 `YYYY-MM-DD HH:MM` 标记去重，所以一个任务在同一分钟最多触发一次，第二天相同时间仍能再次触发。

单个任务的异常在循环内部捕获，不会杀掉整个调度线程。一次性 durable 任务会先从内存和持久化文件删除，成功后才进入队列，降低重启后重复执行的风险。

### 2. Queue Processor

`queue_processor_loop()` 每 0.2 秒观察队列，并非阻塞地尝试获取 `agent_lock`：

- Agent 忙：保留队列，稍后再试；
- Agent 空闲：消费当前队列并启动一个 LangGraph 回合；
- 没有到期任务：不调用模型。

### 3. Consumer

到期任务被转成新的 `HumanMessage`：

```xml
<scheduled_task>
  <id>cron_ab12cd34</id>
  <cron>*/5 * * * *</cron>
  <prompt>check CI status</prompt>
</scheduled_task>
```

动态 system prompt 会告诉模型三个新工具及其边界：

- `schedule_cron`：创建任务；
- `list_crons`：列出任务；
- `cancel_cron`：按 ID 取消任务。

## 持久化

durable 任务原子写入仓库启动目录下的 `.scheduled_tasks.json`：先写 `.scheduled_tasks.json.tmp`，再替换正式文件，避免留下半截 JSON。

启动时会逐条校验记录。单条记录损坏、cron 无效或 ID 重复时只跳过该条，不影响其他任务恢复。任务总数最多为 50。

需要特别区分：

- **跨重启保留定义**：是；
- **进程关闭后继续计时和执行**：否。

两个调度线程都是 daemon。若要求应用关闭后仍然准时执行，应使用系统 crontab、systemd timer、Windows Task Scheduler 或外部工作流平台。

## 相对 s13 的变化

| 组件 | s13 | s14 |
|---|---|---|
| 触发来源 | 用户输入 | 用户输入 + Cron Scheduler |
| 新类型 | — | `CronJob` |
| 新队列 | 后台命令完成通知 | `cron_queue` 到期任务队列 |
| 新线程 | 后台命令线程 | Scheduler + Queue Processor |
| 新存储 | 后台状态仅在内存 | `.scheduled_tasks.json` |
| 工具数量 | 8 | 11（新增 3 个 cron 工具） |

## 本章文件

- `code.py`：默认可运行版本；
- `code_uncommented.py`：无教学行注释的完整版本，适合快速通读；
- `code_commented.py`：带详细中文注释的完整版本，解释锁、队列、持久化和 LangGraph 边界。

三个文件的可执行逻辑一致，默认版与无注释版内容相同。

## 运行

先在仓库根目录准备环境：

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
# 编辑 .env，至少填写 MODEL_ID 和 OPENAI_API_KEY
```

运行任一版本：

```powershell
python -m s14_cron_scheduler.code
python -m s14_cron_scheduler.code_uncommented
python -m s14_cron_scheduler.code_commented
```

可以依次尝试：

1. `Schedule a task to print the current date every 2 minutes.`
2. `List all cron jobs.`
3. `Create a session-only one-shot reminder for the next matching minute.`
4. `Cancel the recurring job and list jobs again.`

观察以下现象：

- 不输入新 prompt 时，到期任务是否仍出现 `[queue processor]`；
- durable 任务是否写入 `.scheduled_tasks.json`；
- 重启程序后 durable 任务是否恢复；
- 一次性任务触发后是否从任务列表消失；
- Agent 正忙时，到期任务是否保留在队列等待交付。

## 教学版边界

为了聚焦核心机制，本章没有实现参考仓库/真实 Claude Code 中更复杂的能力：

- 多进程文件锁与文件变更监听；
- 任务抖动、自动过期和 QoS；
- 错过触发时间后的补偿执行；
- `N-M/S`、`L`、`W`、`?` 等扩展 cron 语法；
- 完整的 UI 阻塞状态、优先级队列和跨会话协调。

## 接下来

s14 让一个 Agent 能自动按时间工作。但重构大型系统时，一个 Agent 的注意力和上下文仍然有限。

[s15: Agent Teams](../s15_agent_teams/) 将进入多 Agent 协作：持久队友、异步收件箱和团队生命周期。
