from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import McpToolset, StreamableHTTPConnectionParams
import uvicorn

PDF_SYSTEM_INSTRUCTION = """
You are a Currency agent.
"""

root_agent = LlmAgent(
    name="currency_agent",
    model="gemini-2.5-flash",
    instruction=PDF_SYSTEM_INSTRUCTION,
    tools=[
        McpToolset(
            connection_params=StreamableHTTPConnectionParams(
                url="https://currency-mcp.wesbos.com/mcp"
            )
        )
    ],
)

# # Expose as A2A service
# a2a_app = to_a2a(root_agent)
# if __name__ == "__main__":
#     uvicorn.run(a2a_app, host="0.0.0.0", port=8003)
#     print("🚀 PDF A2A agent starting on port 8003")