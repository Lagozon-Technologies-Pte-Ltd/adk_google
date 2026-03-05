from google.adk.agents import LlmAgent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.tools.agent_tool import AgentTool
from pathlib import Path
base_path = Path(__file__).parent
with open(base_path / "manager_instructions.txt", "r", encoding="utf-8") as f:
    MANAGER_SYSTEM_INSTRUCTION = f.read()

# Bigquery agent (REMOTE A2A)
fashion_agent_tool_remote = RemoteA2aAgent(
    name="fashion_sales_agent",
    description="Handles BigQuery operations.",
    agent_card="http://localhost:8004/.well-known/agent.json"
)
fashion_agent_tool = AgentTool(agent=fashion_agent_tool_remote)
jira_remote = RemoteA2aAgent(
    name="jira_agent", 
    description="Handles Jira operations.",
    agent_card="http://localhost:8003/.well-known/agent.json"
)
jira_agent_tool = AgentTool(agent=jira_remote)
# 📧 Gmail agent (REMOTE A2A)
workspace_remote = RemoteA2aAgent(
    name="workspace_agent", 
    description="Handles Google Workspace operations.",
    agent_card="http://localhost:8006/.well-known/agent.json"
)
workspace_agent_tool = AgentTool(agent=workspace_remote)

# 🧠 Manager Agent - Direct constructor (no .builder())
root_agent = LlmAgent(
    name="manager_agent",
    model="gemini-2.5-flash",
    instruction=MANAGER_SYSTEM_INSTRUCTION,
    tools=[jira_agent_tool, workspace_agent_tool, fashion_agent_tool]
)

