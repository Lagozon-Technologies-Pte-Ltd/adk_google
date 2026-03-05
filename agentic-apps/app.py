from pathlib import Path
import json
import sqlite3
import uuid
import warnings

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from chatbot import chat_stream

warnings.filterwarnings(
    "ignore",
    message=".*EXPERIMENTAL.*",
)

app = FastAPI(title="Agentic Assistant")
DB_PATH = Path("chat_history.db")

app.mount("/static", StaticFiles(directory="static"), name="static")


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _init_db() -> None:
    with _get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                agent TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(session_id) REFERENCES sessions(session_id)
            )
            """
        )
        conn.commit()


def _session_exists(session_id: str) -> bool:
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM sessions WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        return row is not None


def _create_session(session_id: str) -> None:
    with _get_conn() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO sessions (session_id, title)
            VALUES (?, ?)
            """,
            (session_id, "New Chat"),
        )
        conn.commit()


def _update_session_timestamp(session_id: str) -> None:
    with _get_conn() as conn:
        conn.execute(
            """
            UPDATE sessions
            SET updated_at = CURRENT_TIMESTAMP
            WHERE session_id = ?
            """,
            (session_id,),
        )
        conn.commit()


def _update_session_title_if_new(session_id: str, user_input: str) -> None:
    title = user_input.strip().replace("\n", " ")[:80] or "New Chat"
    with _get_conn() as conn:
        conn.execute(
            """
            UPDATE sessions
            SET title = ?, updated_at = CURRENT_TIMESTAMP
            WHERE session_id = ? AND title = 'New Chat'
            """,
            (title, session_id),
        )
        conn.commit()


def _insert_message(session_id: str, role: str, content: str, agent: str | None = None) -> None:
    with _get_conn() as conn:
        conn.execute(
            """
            INSERT INTO messages (session_id, role, content, agent)
            VALUES (?, ?, ?, ?)
            """,
            (session_id, role, content, agent),
        )
        conn.execute(
            """
            UPDATE sessions
            SET updated_at = CURRENT_TIMESTAMP
            WHERE session_id = ?
            """,
            (session_id,),
        )
        conn.commit()


_init_db()


@app.get("/", response_class=HTMLResponse)
async def home():
    with open("templates/index.html", encoding="utf-8") as f:
        return f.read()


@app.post("/new_chat")
async def new_chat():
    session_id = str(uuid.uuid4())
    _create_session(session_id)
    return {"session_id": session_id}


@app.get("/sessions")
async def list_sessions():
    with _get_conn() as conn:
        rows = conn.execute(
            """
            SELECT session_id, title, created_at, updated_at
            FROM sessions
            ORDER BY datetime(updated_at) DESC
            """
        ).fetchall()

    return {
        "sessions": [
            {
                "session_id": row["session_id"],
                "title": row["title"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
            for row in rows
        ]
    }


@app.get("/sessions/{session_id}/messages")
async def get_session_messages(session_id: str):
    if not _session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")

    with _get_conn() as conn:
        rows = conn.execute(
            """
            SELECT role, content, agent, created_at
            FROM messages
            WHERE session_id = ?
            ORDER BY id ASC
            """,
            (session_id,),
        ).fetchall()

    return {
        "session_id": session_id,
        "messages": [
            {
                "role": row["role"],
                "content": row["content"],
                "agent": row["agent"],
                "created_at": row["created_at"],
            }
            for row in rows
        ],
    }


@app.get("/chat/stream")
async def chat_stream_endpoint(user_input: str, session_id: str):
    if not _session_exists(session_id):
        _create_session(session_id)

    _insert_message(session_id=session_id, role="user", content=user_input)
    _update_session_title_if_new(session_id=session_id, user_input=user_input)
    _update_session_timestamp(session_id=session_id)

    async def generator():
        assistant_chunks: list[str] = []
        routed_agents: list[str] = []

        try:
            async for chunk in chat_stream(user_input, session_id):
                if isinstance(chunk, dict):
                    chunk_type = chunk.get("type")
                    if chunk_type == "text":
                        text = chunk.get("text", "")
                        if text:
                            assistant_chunks.append(text)
                    elif chunk_type == "agent":
                        agent_name = chunk.get("agent")
                        if isinstance(agent_name, str) and agent_name and agent_name not in routed_agents:
                            routed_agents.append(agent_name)
                elif isinstance(chunk, str):
                    assistant_chunks.append(chunk)

                yield f"data: {json.dumps(chunk)}\n\n"
        finally:
            assistant_text = "".join(assistant_chunks).strip()
            if assistant_text:
                _insert_message(
                    session_id=session_id,
                    role="assistant",
                    content=assistant_text,
                    agent=", ".join(routed_agents) if routed_agents else None,
                )

    return StreamingResponse(generator(), media_type="text/event-stream")
