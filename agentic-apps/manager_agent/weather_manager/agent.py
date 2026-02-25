from google.adk.agents import LlmAgent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.tools.agent_tool import AgentTool
from pathlib import Path
base_path = Path(__file__).parent
with open(base_path / "manager_agent" / "system_instruction.txt", "r") as f:
    MANAGER_SYSTEM_INSTRUCTION = f.read()

# 🌦 Weather agent (REMOTE A2A)
weather_remote = RemoteA2aAgent(
    name="weather_agent",
    description="Handles weather queries and forecasts.",
    agent_card="http://localhost:8001/.well-known/agent.json"
)
weather_agent_tool = AgentTool(agent=weather_remote)
#  PDF agent (REMOTE A2A)
pdf_remote = RemoteA2aAgent(
    name="pdf_agent",
    description="Handles PDF generation and manipulation.",
    agent_card="http://localhost:8003/.well-known/agent.json"
)
pdf_agent_tool = AgentTool(agent=pdf_remote)

# 📧 Gmail agent (REMOTE A2A)
gmail_remote = RemoteA2aAgent(
    name="gmail_agent", 
    description="Handles Gmail operations.",
    agent_card="http://localhost:8002/.well-known/agent.json"
)
gmail_agent_tool = AgentTool(agent=gmail_remote)

# 🧠 Manager Agent - Direct constructor (no .builder())
root_agent = LlmAgent(
    name="manager_agent",
    model="gemini-2.5-flash",
    instruction=MANAGER_SYSTEM_INSTRUCTION,
    tools=[weather_agent_tool, gmail_agent_tool, pdf_agent_tool]
)

