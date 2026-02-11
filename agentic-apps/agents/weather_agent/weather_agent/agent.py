"""
Weather agent that can:
- Fetch weather (Weather MCP)
- Give clothing advice (Advice Agent)
- Send weather updates via email (Gmail MCP)
"""

from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools.mcp_tool import McpToolset, StreamableHTTPConnectionParams
from google.adk.a2a.utils.agent_to_a2a import to_a2a

from .advise_agent.agent import advice_agent
import uvicorn
from shared.validate_agent_cards import validate_all_agent_cards

cards = validate_all_agent_cards()
card = cards["weather_agent"]
system_instruction = """
You are a smart weather assistant.

MANDATORY FLOW (do not skip steps):
1. Call get_weather to fetch weather data.
2. Immediately pass the FULL weather response to the advice_agent.
3. Use the advice_agent output as the ONLY source of clothing/lifestyle advice.
4. If the user asks to email or notify, include BOTH:
   - weather data
   - advice_agent output


Rules:
- You MUST call advice_agent after every weather fetch.
- Do NOT generate advice yourself.


Do not include extra text outside the structure.


"""



root_agent = LlmAgent(
    name="weather_agent",
    model="gemini-2.5-flash",
    description="Weather assistant with advice and email notification support",
    instruction=system_instruction,
    tools=[
        # 🌦 Weather MCP
        McpToolset(
            connection_params=StreamableHTTPConnectionParams(
                url="http://localhost:1000/mcp"   # Weather MCP
            )
        ),


        # 🧠 Advice agent
        AgentTool(advice_agent),
    ],
)

# Convert to A2A agent for inter-agent communication
a2a_app = to_a2a(root_agent, port=8001)
if __name__ == "__main__":
    uvicorn.run(a2a_app, host="0.0.0.0", port=8001)
    print("🚀 Weather A2A agent starting on port 8001")
