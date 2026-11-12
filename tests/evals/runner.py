"""Drive one eval step through the real Claude Code via the Agent SDK.

The repo is loaded as a local plugin, the target command is sent as the
prompt, and AskUserQuestion is answered from scripted rules. Tool access is
confined: reads inside the scratch project or the plugin, writes only inside
the scratch project, nothing else.
"""

import dataclasses
import json
from dataclasses import dataclass, field
from pathlib import Path

from answers import answer_questions
from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    SystemMessage,
    TextBlock,
    query,
)
from claude_agent_sdk.types import (
    HookMatcher,
    PermissionResultAllow,
    PermissionResultDeny,
)

READ_TOOLS = {"Read", "Glob", "Grep"}
WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
FREE_TOOLS = {"Skill", "TodoWrite"}
DISALLOWED = ["Bash", "WebFetch", "WebSearch", "Agent", "Task"]


@dataclass
class StepResult:
    texts: list = field(default_factory=list)
    questions: list = field(default_factory=list)
    unmatched: list = field(default_factory=list)
    transcript: list = field(default_factory=list)
    denied: list = field(default_factory=list)
    loaded: bool = False
    available: list = field(default_factory=list)
    subtype: str = ""
    cost: float = 0.0
    turns: int = 0
    duration_ms: int = 0
    error: str = ""


def _inside(path, base, roots):
    p = Path(path).expanduser()
    p = (p if p.is_absolute() else Path(base) / p).resolve()
    return any(p == r or r in p.parents for r in roots)


def _jsonable(message):
    try:
        data = dataclasses.asdict(message) if dataclasses.is_dataclass(message) else repr(message)
    except Exception:  # noqa: BLE001 - transcripts are best-effort
        data = repr(message)
    return {"type": type(message).__name__, "data": data}


async def _dummy_hook(input_data, tool_use_id, context):
    return {"continue_": True}


async def run_step(prompt, rules, cwd, plugin_root, model, budget, max_turns, cli_path=None):
    cwd = Path(cwd).resolve()
    read_roots = [cwd, Path(plugin_root).resolve()]
    write_roots = [cwd]
    result = StepResult()
    target = prompt.split()[0].lstrip("/")

    async def can_use_tool(tool_name, input_data, context):
        if tool_name == "AskUserQuestion":
            questions = input_data.get("questions", [])
            answers, unmatched = answer_questions(questions, rules)
            result.questions.extend(questions)
            result.unmatched.extend(unmatched)
            return PermissionResultAllow(
                updated_input={"questions": questions, "answers": answers}
            )
        if tool_name in FREE_TOOLS:
            return PermissionResultAllow(updated_input=input_data)
        if tool_name in READ_TOOLS:
            path = input_data.get("file_path") or input_data.get("path") or str(cwd)
            if _inside(path, cwd, read_roots):
                return PermissionResultAllow(updated_input=input_data)
        if tool_name in WRITE_TOOLS:
            path = input_data.get("file_path") or input_data.get("notebook_path") or ""
            if path and _inside(path, cwd, write_roots):
                return PermissionResultAllow(updated_input=input_data)
        result.denied.append(f"{tool_name} {json.dumps(input_data, default=repr)[:160]}")
        return PermissionResultDeny(message="Not permitted in this eval sandbox")

    async def prompt_stream():
        yield {"type": "user", "message": {"role": "user", "content": prompt}}

    options = ClaudeAgentOptions(
        model=model,
        cwd=str(cwd),
        plugins=[{"type": "local", "path": str(plugin_root)}],
        setting_sources=["project"],
        max_turns=max_turns,
        max_budget_usd=budget,
        can_use_tool=can_use_tool,
        disallowed_tools=DISALLOWED,
        hooks={"PreToolUse": [HookMatcher(matcher=None, hooks=[_dummy_hook])]},
        cli_path=cli_path,
    )

    try:
        async for message in query(prompt=prompt_stream(), options=options):
            result.transcript.append(_jsonable(message))
            if isinstance(message, SystemMessage) and message.subtype == "init":
                names = list(message.data.get("slash_commands", [])) + list(
                    message.data.get("skills", [])
                )
                result.available = sorted(set(names))
                result.loaded = target in names
                if not result.loaded:
                    result.error = f"{target!r} not loaded; available: {result.available}"
                    break
            elif isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        result.texts.append(block.text)
            elif isinstance(message, ResultMessage):
                result.subtype = message.subtype
                result.cost = message.total_cost_usd or 0.0
                result.turns = message.num_turns
                result.duration_ms = message.duration_ms
                if message.is_error:
                    result.error = f"run ended with {message.subtype}"
    except Exception as err:  # noqa: BLE001 - surface any SDK/CLI failure as a failed step
        result.error = f"{type(err).__name__}: {err}"
    return result
