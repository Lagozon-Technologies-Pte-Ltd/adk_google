from google.adk.agents import LlmAgent

SYSTEM_INSTRUCTION = """
You are a weather-based lifestyle advisor.

You will receive structured weather data in JSON format.
Based on this data:
- Suggest what the user should wear
- Give practical tips (hydration, umbrella, sunscreen, etc.)
- Keep advice short, friendly, and practical
- Do NOT fetch weather yourself
"""

advice_agent = LlmAgent(
    name="advice_agent",
    model="gemini-2.5-flash",
    description="Gives clothing and lifestyle advice based on weather data",
    instruction=SYSTEM_INSTRUCTION,
)
