from anyio import Path
from dotenv import load_dotenv
import httpx
# Resolve project root



http_client = httpx.AsyncClient(
    timeout=httpx.Timeout(30.0),
)