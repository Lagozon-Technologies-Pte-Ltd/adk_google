

from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools.mcp_tool import MCPToolset, StreamableHTTPConnectionParams
from google.adk.a2a.utils.agent_to_a2a import to_a2a
import uvicorn
from pathlib import Path
from config.settings import settings

BASE_DIR = Path(__file__).parent

with open(BASE_DIR / "agent_instructions.txt", "r", encoding="utf-8") as f:
    system_instruction = f.read()
with open(BASE_DIR / "domain.yaml", "r", encoding="utf-8") as f:
    domain_context = f.read()

root_agent = LlmAgent(
    name="Fashion_agent",
    model="gemini-2.5-flash",
    description="Fashion assistant that can query bigquery datasets",
    instruction=f"""
    {system_instruction}

    DOMAIN CONTEXT:
    {domain_context}
    """,

    tools=[
        # 📧 Bigquery MCP
        MCPToolset(
            connection_params=StreamableHTTPConnectionParams(
                url="http://localhost:5000/mcp"   # Bigquery MCP
            )
        ),

    ],
)
#Convert to A2A agent for inter-agent communication
a2a_app = to_a2a(root_agent, port=8004)
if __name__ == "__main__":
    uvicorn.run(a2a_app, host="0.0.0.0", port=8004)
    print("🚀 Bigquery A2A agent starting on port 8004")