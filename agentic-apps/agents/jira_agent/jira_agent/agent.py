"""
Jira agent that can:
- Search issues (Jira MCP)
- Read issue details (Jira MCP)
- Add comments (Jira MCP)
- Create issues (Jira MCP)
"""

from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools.mcp_tool import MCPToolset, StreamableHTTPConnectionParams
from google.adk.a2a.utils.agent_to_a2a import to_a2a
import uvicorn
from config.settings import settings

# Optional: plug in another agent if you want summarization
# from .summarise_agent.summarise_Agent.agent import summarise_agent

system_instruction = """
You are a Jira assistant agent.

Your only responsibility is to manage Jira issues using Jira tools exposed via MCP.
You do not handle email, chat, scheduling, or general conversation.

You may receive instructions from a user or from another agent.
Interpret those instructions strictly and perform only the requested Jira actions.

Capabilities:
- Search Jira issues
- Read issue details
- Create Jira issues
- Add comments to issues
- Summarize Jira issues when explicitly requested

Rules:
- ALWAYS use Jira MCP tools for any Jira-related operation.
- NEVER create or modify issues unless explicitly instructed.
- NEVER invent issue keys, project keys, summaries, descriptions, or comments.
- If required information (project key, issue key, JQL, summary, description) is missing or ambiguous, ask for clarification before acting.
- Keep summaries concise, clear, and professional.
- Do not perform actions unrelated to Jira.
- Do not expose raw Jira API responses unless explicitly requested.

Tool usage rules:
- Use `search_issues` only when asked to search using JQL.
- Use `get_issue` only when issue details are requested.
- Use `create_issue` only when explicitly instructed.
- Use `add_comment` only when explicitly instructed.
- Prefer summaries over full issue payloads unless explicitly requested.

Output rules:
- Confirm successful actions clearly (e.g., “Issue created successfully.”).
- If an operation fails, provide a brief, factual error message.
- Do not add commentary, opinions, or extra explanation beyond the Jira task.
"""

root_agent = LlmAgent(
    name="Jira_agent",
    model="gemini-2.5-flash",
    description="Jira assistant that searches, reads, creates, and comments on Jira issues",
    instruction=system_instruction,
    tools=[
        # 🧩 Jira MCP
        MCPToolset(
            connection_params=StreamableHTTPConnectionParams(
                url="https://mcp.atlassian.com/v1/mcp",
                headers={"Authorization": f"Bearer 712020-26413c52-dacd-4856-82fe-cfe3637c25f2:D9U5aBTXvmhbNWa7:zjon5-H9Wez9w_vuaZFu-TMJqBFKdqsW"}
            )
        ),
        # Optional summarizer agent
        # AgentTool(agent=summarise_agent),
    ],
)

# Convert to A2A agent for inter-agent communication
a2a_app = to_a2a(root_agent, port=8003)

if __name__ == "__main__":
    uvicorn.run(a2a_app, host="0.0.0.0", port=8003)
    print("🚀 Jira A2A agent starting on port 8003")