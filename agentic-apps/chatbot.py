from google.adk.runners import Runner
from google.genai.types import Content, Part

from google.adk.sessions import InMemorySessionService
from manager_agent.jira_agent.jira_agent.agent import root_agent   # your manager agent
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file
APP_NAME = "manager_app"
USER_ID = "default_user"

# ADK session manager
session_service = InMemorySessionService()

# ADK runner
runner = Runner(
    agent=root_agent,
    app_name=APP_NAME,
    session_service=session_service,
)


def _extract_agent_name(event) -> str | None:
    """Best-effort extraction of event author (often manager/orchestrator)."""
    for attr in ("author", "agent_name", "agent", "source"):
        value = getattr(event, attr, None)
        if isinstance(value, str) and value.strip():
            name = value.strip()
            if name.lower() not in {"user", "system"}:
                return name
    return None


def _normalize_routed_agent(raw_name: str | None) -> str | None:
    if not raw_name:
        return None

    name = raw_name.strip().lower()
    aliases = {
        "jira_agent": ("jira_agent", "jira", "atlassian", "confluence"),
        "workspace_agent": ("workspace_agent", "workspace", "gmail", "calendar", "drive", "docs", "sheets", "google_workspace"),
        "fashion_sales_agent": ("fashion_sales_agent", "fashion", "bigquery", "bq", "sales"),
    }

    for canonical, keys in aliases.items():
        if any(key in name for key in keys):
            return canonical

    return raw_name.strip()


def _extract_agent_from_function_part(part) -> str | None:
    """Extract delegated specialist name from function call/response metadata."""
    for attr in ("function_call", "function_response"):
        obj = getattr(part, attr, None)
        if not obj:
            continue

        fn_name = getattr(obj, "name", None)
        mapped = _normalize_routed_agent(fn_name)
        if mapped:
            return mapped

        if isinstance(obj, dict):
            mapped = _normalize_routed_agent(obj.get("name"))
            if mapped:
                return mapped

    return None


# Streaming chat
async def chat_stream(user_input: str, session_id: str):
    # Ensure session exists
    session = await session_service.get_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=session_id,
    )

    if not session:
        await session_service.create_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=session_id,
        )

    user_message = Content(
        role="user",
        parts=[Part(text=user_input)]
    )

    last_agent = None
    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=session_id,
        new_message=user_message,
    ):
        # Event author is usually the orchestrator (manager_agent).
        # Keep it as fallback, but prefer delegated agent names from function calls.
        fallback_agent = _extract_agent_name(event)

        if event.content and event.content.parts:
            for part in event.content.parts:
                delegated_agent = _extract_agent_from_function_part(part)
                if delegated_agent and delegated_agent != last_agent:
                    last_agent = delegated_agent
                    yield {"type": "agent", "agent": delegated_agent}

                # Normal assistant text
                if hasattr(part, "text") and part.text:
                    if not last_agent and fallback_agent:
                        routed = _normalize_routed_agent(fallback_agent)
                        if routed and routed != last_agent:
                            last_agent = routed
                            yield {"type": "agent", "agent": routed}
                    yield {"type": "text", "text": part.text}

                # Tool call from agent
                elif hasattr(part, "function_call"):
                    continue

                # Tool result
                elif hasattr(part, "function_response"):
                    continue
