from dotenv import load_dotenv
load_dotenv(override=True)
from langchain.agents.middleware import AgentMiddleware
from langchain_core.tools import tool
import os, subprocess
from pathlib import Path
from langchain_core.messages import AIMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
WORKDIR = Path.cwd()
path = os.getcwd()
MODEL_ID = os.getenv('MODEL_ID')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
SYSTEM = f'you are a coding agent at {path}. Use tools to solve tasks. Act dont explain'
OPENAI_BASE_URL = os.getenv('BASE_URL')
dangerous = ['rm -rf /', 'sudo', 'shutdown', 'reboot', 'mkfs', 'dd if=', '> /dev/sda']

def check_deny_list(command: str) -> str | None:
    for pattern in dangerous:
        if pattern in command:
            return f'blocked:{pattern} is on the deny list'
    return None

def check_rules(tool_name: str, args: dict) -> str | None:
    if tool_name == 'run_bash':
        command = args.get('command', '')
        if any((kw in command for kw in ['rm ', '> /etc/', 'chmod 777', 'del'])):
            return 'potentially destructive command'
    if tool_name in ('run_write', 'run_edit', 'run_read'):
        path = args.get('path', '')
        if not (WORKDIR / path).resolve().is_relative_to(WORKDIR):
            return 'Working outside workspace'
    return None

def ask_user(tool_name: str, args: dict, reason: str) -> bool:
    print(f'\nWarning: {reason}')
    print(f'Tool: {tool_name}({args})')
    choice = input('Allow? [y/N] ').strip().lower()
    return choice in ('y', 'yes')

def check_permission(tool_name: str, args: dict) -> bool:
    if tool_name == 'run_bash':
        reason = check_deny_list(args.get('command', ''))
        if reason:
            print(f'\nBlocked: {reason}')
            return False
    reason = check_rules(tool_name, args)
    if reason:
        return ask_user(tool_name, args, reason)
    return True

class permission_check(AgentMiddleware):

    def wrap_tool_call(self, request, handler):
        tool_name = request.tool.name if request.tool else request.tool_call['name']
        args = request.tool_call.get('args', {})
        tool_call_id = request.tool_call['id']
        if not check_permission(tool_name, args):
            return ToolMessage(content='Permission denied', tool_call_id=tool_call_id, name=tool_name, status='error')
        return handler(request)

@tool
def run_bash(command: str) -> str:
    """执行 shell 命令，并返回命令输出。"""
    try:
        r = subprocess.run(command, shell=True, cwd=path, capture_output=True, text=True, timeout=120)
        out = (r.stdout + r.stderr).strip()
        return out[:50000] if out else '(no output)'
    except subprocess.TimeoutExpired:
        return 'Error: Timeout(120s)'
    except (FileExistsError, OSError) as e:
        return f'Error: {e}'

@tool
def run_read(path: str, limit: int | None=None) -> str:
    """对文件的内容进行阅读，传入路径和限制长度"""
    try:
        lines = Path(path).read_text().splitlines()
        if limit and limit < len(lines):
            lines = lines[:limit] + [f'...({len(lines) - limit} more lines)']
        return '\n'.join(lines)
    except Exception as e:
        return f'Error: {e}'

@tool
def run_write(path: str, content: str) -> str:
    """对文件内容进行改写，传入路径和内容"""
    try:
        file_path = Path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
        return f'write {len(content)} bytes to {path}'
    except Exception as e:
        return f'Error: {e}'

@tool
def run_edit(path: str, old_text: str, new_text: str) -> str:
    """替换旧文本为新文本，传入路径，旧文本，新文本"""
    try:
        file_path = Path(path)
        text = file_path.read_text()
        if old_text not in text:
            return f'Error: text not found in {path}'
        file_path.write_text(text.replace(old_text, new_text, 1))
        return f'edit {path}'
    except Exception as e:
        return f'Error: {e}'

@tool
def run_glob(pattern: str) -> str:
    """查找路径下对应文件类型的文件路径，输入文件类型"""
    import glob as g
    try:
        results = []
        for match in g.glob(pattern, root_dir=WORKDIR):
            if (WORKDIR / match).resolve().is_relative_to(WORKDIR):
                results.append(match)
        return '\n'.join(results) if results else '(no matches)'
    except Exception as e:
        return f'Error: {e}'

def print_assistant_message(message: AIMessage) -> None:
    content = message.content
    if isinstance(content, str):
        print(content)
        return
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict):
                if block.get('type') == 'text':
                    print(block.get('text', ''))
            elif hasattr(block, 'text'):
                print(block.text)
TOOLS = [run_bash, run_edit, run_glob, run_write, run_read]
MODEL = ChatOpenAI(model=MODEL_ID, max_tokens=8000, temperature=0, api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)
agent = create_agent(model=MODEL, tools=TOOLS, system_prompt=SYSTEM, middleware=[permission_check()])

def agent_loop(messages: list) -> None:
    result = agent.invoke({'messages': messages})
    new_messages = result['messages'][len(messages):]
    for message in new_messages:
        if hasattr(message, 'tool_calls') and message.tool_calls:
            print('模型调用工具:')
            for tool_call in message.tool_calls:
                print('工具名：', tool_call['name'])
                print('参数：', tool_call.get('args', {}))
        elif message.__class__.__name__ == 'ToolMessage':
            print('工具返回结果：')
            print('工具名', getattr(message, 'name', None))
            print('内容:', message.content)
        else:
            print('模型回复:')
            print(getattr(message, 'content', message))
        print()
    messages[:] = result['messages']
if __name__ == '__main__':
    print('s03.5: Permission before agent run tools')
    print('输入问题，回车发送。输入 q 退出。\n')
    history = []
    while True:
        try:
            query = input('\x1b[36ms03 >> \x1b[0m')
        except (EOFError, KeyboardInterrupt):
            break
        if query.strip().lower() in ('q', 'exit', ''):
            break
        history.append({'role': 'user', 'content': query})
        agent_loop(history)
