import asyncio
import logging
import os
import requests
from fastmcp import FastMCP
from dotenv import load_dotenv
load_dotenv("self-experiments\weather-agent\.env")
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("Weather MCP Server ☀️")

API_KEY = "817503c3b9afa2609e36a6b8239520bd"
BASE_URL = "http://api.openweathermap.org/data/2.5/weather"


@mcp.tool()
def get_weather(location: str = "New Delhi"):
    """Get current weather information for a location."""
    logger.info(f"🛠️ get_weather called for '{location}'")

    try:
        response = requests.get(
            BASE_URL,
            params={
                "q": location,
                "appid": API_KEY,
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        return {
            "location": data.get("name"),
            "temperature_celsius": round(data["main"]["temp"] - 273.15, 2),
            "feels_like_celsius": round(data["main"]["feels_like"] - 273.15, 2),
            "weather": data["weather"][0]["description"],
            "humidity": data["main"]["humidity"],
            "wind_speed": data["wind"]["speed"],
        }

    except Exception as e:
        logger.error(f"❌ Weather fetch failed: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    port = int(os.getenv("PORT", "1000"))
    logger.info(f"🚀 MCP server running on port {port}")

    asyncio.run(
        mcp.run_async(
            transport="http",
            host="0.0.0.0",
            port=port,
        )
    )
