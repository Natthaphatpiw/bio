OpenAI Agents SDK 

The OpenAI Agents SDK enables you to build agentic AI apps in a lightweight, easy-to-use package with very few abstractions. It's a production-ready upgrade of our previous experimentation for agents, Swarm. 

The Agents SDK has a very small set of primitives: 

* **Agents**, which are LLMs equipped with instructions and tools 


* **Handoffs**, which allow agents to delegate to other agents for specific tasks 


* **Guardrails**, which enable validation of agent inputs and outputs 


* **Sessions**, which automatically maintains conversation history across agent runs 



In combination with Python, these primitives are powerful enough to express complex relationships between tools and agents, and allow you to build real-world applications without a steep learning curve. In addition, the SDK comes with built-in tracing that lets you visualize and debug your agentic flows, as well as evaluate them and even fine-tune models for your application. 

---

Why use the Agents SDK 

The SDK has two driving design principles: 

1. Enough features to be worth using, but few enough primitives to make it quick to learn. 


2. Works great out of the box, but you can customize exactly what happens. 



Here are the main features of the SDK: 

* **Agent loop**: Built-in agent loop that handles calling tools, sending results to the LLM, and looping until the LLM is done. 


* **Python-first**: Use built-in language features to orchestrate and chain agents, rather than needing to learn new abstractions. 


* **Handoffs**: A powerful feature to coordinate and delegate between multiple agents. 


* **Guardrails**: Run input validations and checks in parallel to your agents, breaking early if the checks fail. 


* **Sessions**: Automatic conversation history management across agent runs, eliminating manual state handling. 


* **Function tools**: Turn any Python function into a tool, with automatic schema generation and Pydantic-powered validation. 


* **Tracing**: Built-in tracing that lets you visualize, debug and monitor your workflows, as well as use the OpenAI suite of evaluation, fine-tuning and distillation tools. 



---

Installation 

```bash
pip install openai-agents

```

Hello world example 

```python
from agents import Agent, Runner

agent = Agent(name="Assistant", instructions="You are a helpful assistant")

result = Runner.run_sync(agent, "Write a haiku about recursion in programming.")
print(result.final_output)

# Code within the code,
# Functions calling themselves,
# Infinite loop's dance.

```

(If running this, ensure you set the OPENAI_API_KEY environment variable) 

```bash
export OPENAI_API_KEY=sk-... 

```

---

````markdown
# Quickstart – OpenAI Agents SDK

## Create a project and virtual environment
> You'll only need to do this once.

```bash
mkdir my_project
cd my_project
python -m venv .venv
````

## Activate the virtual environment

> Do this every time you start a new terminal session.

```bash
source .venv/bin/activate
```

## Install the Agents SDK

```bash
pip install openai-agents
# or
uv add openai-agents
```

## Set an OpenAI API key

If you don't have one, create an OpenAI API key first.

```bash
export OPENAI_API_KEY=sk-...
```

---

## Create your first agent

Agents are defined with:

* `name`
* `instructions`
* optional config (e.g. `model_config`)

```python
from agents import Agent

agent = Agent(
    name="Math Tutor",
    instructions="You provide help with math problems. Explain your reasoning."
)
```

---

## Add more agents

You can define multiple agents.
`handoff_description` helps determine routing.

```python
history_tutor_agent = Agent(
    name="History Tutor",
    handoff_description="Specialist agent for historical questions",
    instructions="You provide assistance with historical queries."
)

math_tutor_agent = Agent(
    name="Math Tutor",
    handoff_description="Specialist agent for math questions",
    instructions="You provide help with math problems."
)
```

---

## Define handoffs

Each agent can decide which agent to hand off to.

```python
triage_agent = Agent(
    name="Triage Agent",
    instructions="Determine which agent to use based on the user's question",
    handoffs=[history_tutor_agent, math_tutor_agent]
)
```

---

## Run the agent orchestration

```python
from agents import Runner
import asyncio

async def main():
    result = await Runner.run(
        triage_agent,
        "Who was the first president of the United States?"
    )
    print(result.final_output)

asyncio.run(main())
```

---

## Add a guardrail

You can validate input/output using guardrails.

```python
from agents import Agent, Runner, GuardrailFunctionOutput
from pydantic import BaseModel

class HomeworkOutput(BaseModel):
    is_homework: bool
    reasoning: str

guardrail_agent = Agent(
    name="Guardrail check",
    instructions="Check if the user is asking about homework.",
    output_type=HomeworkOutput
)

async def homework_guardrail(ctx, agent, input_data):
    result = await Runner.run(
        guardrail_agent,
        input_data,
        context=ctx.context
    )
    final_output = result.final_output_as(HomeworkOutput)
    return GuardrailFunctionOutput(
        output_info=final_output,
        tripwire_triggered=not final_output.is_homework
    )
```

---

## Full workflow with guardrails

```python
from agents import InputGuardrail
from agents.exceptions import InputGuardrailTripwireTriggered

triage_agent = Agent(
    name="Triage Agent",
    instructions="Route homework questions to the correct tutor",
    handoffs=[history_tutor_agent, math_tutor_agent],
    input_guardrails=[
        InputGuardrail(guardrail_function=homework_guardrail)
    ]
)

async def main():
    try:
        result = await Runner.run(
            triage_agent,
            "Who was the first president of the United States?"
        )
        print(result.final_output)
    except InputGuardrailTripwireTriggered as e:
        print("Guardrail blocked this input:", e)

if __name__ == "__main__":
    asyncio.run(main())
```

---

# Examples – OpenAI Agents SDK

This section contains a variety of sample implementations demonstrating different
patterns and capabilities of the OpenAI Agents SDK.

---

## Categories

### agent_patterns
Examples illustrating common agent design patterns, such as:
- Deterministic workflows
- Agents as tools
- Parallel agent execution
- Conditional tool usage
- Input / output guardrails
- LLM as a judge
- Routing
- Streaming guardrails

---

### basic
Foundational examples of the SDK, including:
- Hello World examples  
  - Default model  
  - GPT-5  
  - Open-weight models
- Agent lifecycle management
- Dynamic system prompts
- Streaming outputs  
  - Text  
  - Items  
  - Function call arguments
- Prompt templates
- File handling  
  - Local files  
  - Remote files  
  - Images and PDFs
- Usage tracking
- Non-strict output types
- Previous response ID usage

---

### customer_service
- Example customer service system for an airline

---

### financial_research_agent
- A financial research agent demonstrating structured research workflows
- Uses multiple agents and tools for financial data analysis

---

### handoffs
- Practical examples of agent handoffs
- Includes message filtering techniques

---

### hosted_mcp
Examples showing how to use hosted MCP (Model Context Protocol):
- Connectors
- Approval flows

---

### mcp
Examples for building agents with MCP (Model Context Protocol), including:
- Filesystem examples
- Git examples
- MCP prompt server examples
- SSE (Server-Sent Events)
- Streamable HTTP examples

---

### memory
Examples of different memory implementations for agents:
- SQLite session storage
- Advanced SQLite session storage
- Redis session storage
- SQLAlchemy session storage
- Encrypted session storage
- OpenAI session storage

---

### model_providers
Examples of using non-OpenAI models with the SDK:
- Custom model providers
- LiteLLM integration

---

### realtime
Examples for building real-time experiences, including:
- Web applications
- Command-line interfaces (CLI)
- Twilio integration

---

### reasoning_content
- Examples demonstrating reasoning content
- Structured output handling

---

### research_bot
- Simple deep research bot
- Demonstrates complex multi-agent research workflows

---

### tools
Examples of OpenAI-hosted tools, such as:
- Web search
- Web search with filters
- File search
- Code interpreter
- Computer use
- Image generation

---

### voice
Examples of voice agents using TTS and STT models:
- Voice agents
- Streamed voice examples



# Agents – OpenAI Agents SDK

Agents are the core building block in your apps. An agent is a large language model (LLM)
configured with instructions and tools.

---

## Basic Configuration

Common agent properties:
- **name**: Required string identifier
- **instructions**: Developer message / system prompt
- **model**: LLM to use (with optional `model_settings` such as `temperature`, `top_p`)
- **tools**: Tools the agent can use

---

## Context

Agents are generic over their context type. Context is a dependency-injection object passed
to `Runner.run()` and shared across agents, tools, and handoffs.

```python
from agents import Agent, ModelSettings, function_tool
from dataclasses import dataclass

@function_tool
def get_weather(city: str) -> str:
    """Returns weather info for the specified city."""
    return f"The weather in {city} is sunny"

agent = Agent(
    name="Haiku agent",
    instructions="Always respond in haiku form",
    model="gpt-5-nano",
    tools=[get_weather],
)

@dataclass
class UserContext:
    name: str
````

---

## Output Types

By default, agents return plain text (`str`).
To enforce structured outputs, specify `output_type` (supports Pydantic models, dataclasses,
lists, TypedDict, etc.).

```python
from pydantic import BaseModel
from agents import Agent

class CalendarEvent(BaseModel):
    name: str
    date: str
    participants: list[str]

agent = Agent(
    name="Calendar extractor",
    instructions="Extract calendar events from text",
    output_type=CalendarEvent,
)
```

---

## Multi-Agent System Design Patterns

### 1) Manager (Agents as Tools)

A central agent orchestrates and calls specialized sub-agents exposed as tools.

### 2) Handoffs

Peer agents delegate control to a specialized agent that takes over the conversation.

---

## Manager (Agents as Tools)

```python
from agents import Agent

booking_agent = Agent(...)
refund_agent = Agent(...)

customer_facing_agent = Agent(
    name="Customer-facing agent",
    instructions=(
        "Handle all direct user communication. "
        "Call the relevant tools when specialized expertise is needed."
    ),
    tools=[
        booking_agent.as_tool(
            tool_name="booking_expert",
            tool_description="Handles booking questions and requests.",
        ),
        refund_agent.as_tool(
            tool_name="refund_expert",
            tool_description="Handles refund questions and requests.",
        ),
    ],
)
```

---

## Handoffs

```python
from agents import Agent

booking_agent = Agent(...)
refund_agent = Agent(...)

triage_agent = Agent(
    name="Triage agent",
    instructions=(
        "Help the user with their questions. "
        "If they ask about booking, hand off to the booking agent. "
        "If they ask about refunds, hand off to the refund agent."
    ),
    handoffs=[booking_agent, refund_agent],
)
```

---

## Dynamic Instructions

Instructions can be provided via a function (sync or async), receiving agent and context.

```python
from agents import Agent
from agents.run_context import RunContextWrapper

def dynamic_instructions(
    context: RunContextWrapper[UserContext],
    agent: Agent[UserContext]
) -> str:
    return f"The user's name is {context.context.name}. Help them with their request."

agent = Agent(
    name="Triage agent",
    instructions=dynamic_instructions,
)
```

---

## Lifecycle Events (Hooks)

Use hooks to observe agent lifecycle events (e.g., logging, prefetching).
Subclass `AgentHooks` and override needed methods.

---

## Guardrails

Guardrails validate user input and/or agent output in parallel to agent execution
(e.g., relevance checks). See guardrails documentation for details.

---

## Cloning / Copying Agents

```python
from agents import Agent

pirate_agent = Agent(
    name="Pirate",
    instructions="Write like a pirate",
    model="gpt-5.2",
)

robot_agent = pirate_agent.clone(
    name="Robot",
    instructions="Write like a robot",
)
```

---

## Forcing Tool Use

Use `ModelSettings.tool_choice`:

* `auto`: LLM decides (default)
* `required`: Must use a tool
* `none`: Must not use tools
* Specific tool name (e.g., `"get_weather"`)

```python
from agents import Agent, function_tool, ModelSettings

@function_tool
def get_weather(city: str) -> str:
    return f"The weather in {city} is sunny"

agent = Agent(
    name="Weather Agent",
    instructions="Retrieve weather details.",
    tools=[get_weather],
    model_settings=ModelSettings(tool_choice="get_weather"),
)
```

---

## Tool Use Behavior

Controls how tool outputs are handled:

* `run_llm_again` (default)
* `stop_on_first_tool`
* `StopAtTools(stop_at_tool_names=[...])`
* Custom `ToolsToFinalOutputFunction`

### Stop on First Tool

```python
from agents import Agent, function_tool

@function_tool
def get_weather(city: str) -> str:
    return f"The weather in {city} is sunny"

agent = Agent(
    name="Weather Agent",
    instructions="Retrieve weather details.",
    tools=[get_weather],
    tool_use_behavior="stop_on_first_tool",
)
```

### Stop at Specific Tools

```python
from agents import Agent, function_tool
from agents.agent import StopAtTools

@function_tool
def get_weather(city: str) -> str:
    return f"The weather in {city} is sunny"

@function_tool
def sum_numbers(a: int, b: int) -> int:
    return a + b

agent = Agent(
    name="Stop At Tool Agent",
    instructions="Get weather or sum numbers.",
    tools=[get_weather, sum_numbers],
    tool_use_behavior=StopAtTools(stop_at_tool_names=["get_weather"]),
)
```

---

## Custom Tool Result Handling

```python
from agents import Agent, function_tool
from agents.agent import ToolsToFinalOutputResult
from agents.run_context import RunContextWrapper
from agents.types import FunctionToolResult
from typing import List, Any

@function_tool
def get_weather(city: str) -> str:
    return f"The weather in {city} is sunny"

def custom_tool_handler(
    context: RunContextWrapper[Any],
    tool_results: List[FunctionToolResult],
) -> ToolsToFinalOutputResult:
    for result in tool_results:
        if result.output and "sunny" in result.output:
            return ToolsToFinalOutputResult(
                is_final_output=True,
                final_output=f"Final weather: {result.output}",
            )
    return ToolsToFinalOutputResult(
        is_final_output=False,
        final_output=None,
    )

agent = Agent(
    name="Weather Agent",
    instructions="Retrieve weather details.",
    tools=[get_weather],
    tool_use_behavior=custom_tool_handler,
)
```

---

## Notes

* To prevent infinite loops, the framework resets `tool_choice` to `"auto"` after a tool call.
* This behavior is configurable via `agent.reset_tool_choice`.

# Running Agents – OpenAI Agents SDK

You can run agents via the `Runner` class. There are three main ways to run an agent:

1. **Runner.run()** – Asynchronous, returns a `RunResult`
2. **Runner.run_sync()** – Synchronous wrapper around `run()`
3. **Runner.run_streamed()** – Asynchronous streaming, returns `RunResultStreaming`

---

## The Agent Loop

When calling `Runner.run()`, you provide:
- A starting agent
- An input (string user message or a list of input items from the OpenAI Responses API)

### Execution Flow
1. Call the LLM for the current agent with the current input
2. The LLM produces output:
   - **Final output** → loop ends
   - **Handoff** → switch to another agent and continue
   - **Tool calls** → run tools, append results, continue
3. If `max_turns` is exceeded, a `MaxTurnsExceeded` exception is raised

```python
from agents import Agent, Runner

async def main():
    agent = Agent(
        name="Assistant",
        instructions="You are a helpful assistant"
    )
    result = await Runner.run(
        agent,
        "Write a haiku about recursion in programming"
    )
    print(result.final_output)

# Example output:
# Code within the code,
# Functions calling themselves,
# Infinite loop's dance
````

A response is considered **final** when:

* The desired output type is produced
* No tool calls are present

---

## Streaming

Streaming allows you to receive events while the LLM is running.

* Use `Runner.run_streamed()`
* Call `.stream_events()` to consume streaming events
* After completion, the result contains all outputs

---

## Run Configuration (`RunConfig`)

The `run_config` parameter allows global configuration for a run:

* **model** – Override all agent models
* **model_provider** – Model provider (default: OpenAI)
* **model_settings** – Global overrides (e.g. `temperature`, `top_p`)
* **input_guardrails / output_guardrails** – Guardrails applied to all runs
* **handoff_input_filter** – Global filter applied to handoffs
* **nest_handoff_history** –

  * `True` (default): Collapse prior transcript into a single assistant summary
  * `False`: Pass raw transcript
* **handoff_history_mapper** – Custom function to map conversation history
* **tracing_disabled** – Disable tracing
* **trace_include_sensitive_data** – Include sensitive data in traces
* **workflow_name / trace_id / group_id** – Tracing identifiers
* **trace_metadata** – Metadata attached to traces

> By default, prior turns are nested into a single `<CONVERSATION HISTORY>` block during handoffs.

---

## Conversations & Chat Threads

A single `Runner.run()` call may involve:

* Multiple agents
* Multiple tool calls
* Multiple LLM invocations

But it represents **one logical chat turn**.

After a run, you decide what to show the user:

* Final output only
* Or all intermediate outputs

---

## Manual Conversation Management

You can manually manage conversation history using:

```python
next_input = result.to_input_list()
```

This allows you to append new user messages and continue the conversation.

---

## Automatic Conversation Management with Sessions

Sessions automatically:

* Retrieve conversation history
* Store new messages
* Maintain separate conversations per session ID

### Example with SQLite Session

```python
from agents import Agent, Runner, SQLiteSession

async def main():
    agent = Agent(
        name="Assistant",
        instructions="Reply very concisely."
    )

    session = SQLiteSession("conversation_123")

    result = await Runner.run(
        agent,
        "What city is the Golden Gate Bridge in?",
        session=session
    )
    print(result.final_output)  # San Francisco

    result = await Runner.run(
        agent,
        "What state is it in?",
        session=session
    )
    print(result.final_output)  # California
```

---

## Server-Managed Conversations

You can let OpenAI manage conversation state on the server.

### Option 1: `conversation_id`

```python
from agents import Agent, Runner
from openai import AsyncOpenAI

client = AsyncOpenAI()

async def main():
    agent = Agent(
        name="Assistant",
        instructions="Reply very concisely."
    )

    conversation = await client.conversations.create()
    conv_id = conversation.id

    while True:
        user_input = input("You: ")
        result = await Runner.run(
            agent,
            user_input,
            conversation_id=conv_id
        )
        print("Assistant:", result.final_output)
```

### Option 2: `previous_response_id` (Response Chaining)

```python
previous_response_id = None

result = await Runner.run(
    agent,
    user_input,
    previous_response_id=previous_response_id,
    auto_previous_response_id=True,
)

previous_response_id = result.last_response_id
```

---

## Long-Running Agents & Human-in-the-Loop

The SDK integrates with **Temporal** to support:

* Durable workflows
* Long-running tasks
* Human-in-the-loop processes

---

## Exceptions

Common exceptions raised by the SDK:

* **AgentsException** – Base class for all SDK exceptions
* **MaxTurnsExceeded** – Exceeded `max_turns` limit
* **ModelBehaviorError**

  * Malformed JSON
  * Invalid tool usage
* **UserError** – Incorrect SDK usage
* **InputGuardrailTripwireTriggered**
* **OutputGuardrailTripwireTriggered**

Input guardrails validate incoming messages, while output guardrails validate the final response.

# Sessions – OpenAI Agents SDK

The Agents SDK provides built-in session memory to automatically maintain conversation
history across multiple agent runs, eliminating the need to manually handle
`.to_input_list()` between turns.

Sessions store conversation history for a specific session, allowing agents to maintain
context without explicit manual memory management. This is ideal for chat apps and
multi-turn conversations.

---

## Quick Start

```python
from agents import Agent, Runner, SQLiteSession

# Create agent
agent = Agent(
    name="Assistant",
    instructions="Reply very concisely.",
)

# Create a session instance with a session ID
session = SQLiteSession("conversation_123")

# First turn
result = await Runner.run(
    agent,
    "What city is the Golden Gate Bridge in?",
    session=session
)
print(result.final_output)  # "San Francisco"

# Second turn - agent automatically remembers previous context
result = await Runner.run(
    agent,
    "What state is it in?",
    session=session
)
print(result.final_output)  # "California"
````

Sessions also work with the synchronous runner:

```python
result = Runner.run_sync(agent, "Hello", session=session)
```

---

## How It Works

When session memory is enabled:

1. **Before each run**: Conversation history is automatically retrieved and prepended
2. **After each run**: All new items (user input, assistant output, tool calls) are stored
3. **Context preservation**: Subsequent runs include the full conversation history

This removes the need to manually call `.to_input_list()`.

---

## Memory Operations

### Basic Operations

```python
from agents import SQLiteSession

session = SQLiteSession("user_123", "conversations.db")

# Get all items
items = await session.get_items()

# Add items
await session.add_items([
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi there!"}
])

# Remove and return the most recent item
last_item = await session.pop_item()
print(last_item)
```

---

## Using `pop_item` for Corrections

Useful when undoing or correcting the last turn:

```python
from agents import Agent, Runner, SQLiteSession

agent = Agent(name="Assistant")
session = SQLiteSession("correction_example")

# Initial question
result = await Runner.run(agent, "What's 2 + 2?", session=session)
print(result.final_output)

# Remove last turn
await session.pop_item()  # assistant
await session.pop_item()  # user

# Ask corrected question
result = await Runner.run(agent, "What's 2 + 3?", session=session)
print(result.final_output)
```

---

## Session Types

### OpenAI Conversations API Sessions

```python
from agents import Agent, Runner, OpenAIConversationsSession

agent = Agent(
    name="Assistant",
    instructions="Reply very concisely.",
)

session = OpenAIConversationsSession()

result = await Runner.run(agent, "What city is the Golden Gate Bridge in?", session=session)
print(result.final_output)

result = await Runner.run(agent, "What state is it in?", session=session)
print(result.final_output)
```

---

### SQLite Sessions (Default)

```python
from agents import SQLiteSession

# In-memory (non-persistent)
session = SQLiteSession("user_123")

# Persistent
session = SQLiteSession("user_123", "conversations.db")
```

---

### SQLAlchemy Sessions (Production)

```python
from agents.extensions.memory import SQLAlchemySession
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/db")
session = SQLAlchemySession("user_123", engine=engine, create_tables=True)
```

---

### Advanced SQLite Sessions

Supports:

* Conversation branching
* Usage analytics
* Structured queries

```python
from agents.extensions.memory import AdvancedSQLiteSession

session = AdvancedSQLiteSession(
    session_id="user_123",
    db_path="conversations.db",
    create_tables=True
)

result = await Runner.run(agent, "Hello", session=session)
await session.store_run_usage(result)

await session.create_branch_from_turn(2)
```

---

### Encrypted Sessions

```python
from agents.extensions.memory import EncryptedSession, SQLAlchemySession

underlying = SQLAlchemySession.from_url(
    "user_123",
    url="sqlite+aiosqlite:///conversations.db",
    create_tables=True
)

session = EncryptedSession(
    session_id="user_123",
    underlying_session=underlying,
    encryption_key="your-secret-key",
    ttl=600  # seconds
)
```

---

## Session Management

### Session ID Naming

* User-based: `user_12345`
* Thread-based: `thread_abc123`
* Context-based: `support_ticket_456`

### Memory Persistence

* Temporary: in-memory SQLite
* Persistent: file-based SQLite
* Production: SQLAlchemy / Dapr / OpenAI-hosted

---

## Multiple Sessions & Sharing

```python
from agents import Agent, Runner, SQLiteSession

agent = Agent(name="Assistant")

session_1 = SQLiteSession("user_123")
session_2 = SQLiteSession("user_456")

await Runner.run(agent, "Help me with my account", session=session_1)
await Runner.run(agent, "What are my charges?", session=session_2)
```

Different agents can share the same session:

```python
support_agent = Agent(name="Support")
billing_agent = Agent(name="Billing")

session = SQLiteSession("user_123")

await Runner.run(support_agent, "Help me with my account", session=session)
await Runner.run(billing_agent, "What are my charges?", session=session)
```

---

## Complete Example

```python
import asyncio
from agents import Agent, Runner, SQLiteSession

async def main():
    agent = Agent(
        name="Assistant",
        instructions="Reply very concisely.",
    )

    session = SQLiteSession("conversation_123", "conversation_history.db")

    result = await Runner.run(agent, "What city is the Golden Gate Bridge in?", session=session)
    print(result.final_output)

    result = await Runner.run(agent, "What state is it in?", session=session)
    print(result.final_output)

    result = await Runner.run(agent, "What's the population of that state?", session=session)
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Custom Session Implementations

You can implement your own session by following the `Session` protocol:

```python
from agents.memory.session import SessionABC
from agents.items import TResponseInputItem
from typing import List

class MyCustomSession(SessionABC):
    def __init__(self, session_id: str):
        self.session_id = session_id

    async def get_items(self, limit: int | None = None) -> List[TResponseInputItem]:
        pass

    async def add_items(self, items: List[TResponseInputItem]) -> None:
        pass

    async def pop_item(self) -> TResponseInputItem | None:
        pass

    async def clear_session(self) -> None:
        pass
```

---

## Community Session Implementations

* **openai-django-sessions**
  Django ORM-based sessions supporting PostgreSQL, MySQL, SQLite, and more

---

## API Reference

* `Session` – Protocol interface
* `OpenAIConversationsSession`
* `SQLiteSession`
* `SQLAlchemySession`
* `DaprSession`
* `AdvancedSQLiteSession`
* `EncryptedSession`

# Results – OpenAI Agents SDK

When calling `Runner.run()` methods, you receive either:
- **RunResult** – from `run()` or `run_sync()`
- **RunResultStreaming** – from `run_streamed()`

Both inherit from **RunResultBase**, which contains most useful information.

---

## Final Output

The `final_output` property contains the final output of the **last agent** that ran:

- `str` – if the last agent has no `output_type`
- `last_agent.output_type` – if an output type is defined

> `final_output` is typed as `Any` because with handoffs, any agent may be the final agent.

---

## Inputs for the Next Turn

Use `result.to_input_list()` to convert the run result into an input list:

- Concatenates the original input
- Appends all items generated during the run

This is useful for:
- Chaining multiple agent runs
- Looping with follow-up user inputs
- Manual conversation management

---

## Last Agent

The `last_agent` property references the agent that produced the final
