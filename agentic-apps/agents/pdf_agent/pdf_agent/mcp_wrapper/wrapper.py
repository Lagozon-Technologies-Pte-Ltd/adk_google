# wrapper.py - updated version
"""
Minimal MCP wrapper that just fixes the Accept header issue.
"""

import json
from fastapi import FastAPI, Request, Response
import httpx
import uvicorn

app = FastAPI()
TARGET_URL = "http://localhost:9010/mcp"
client = httpx.AsyncClient()


@app.post("/mcp")
async def mcp_proxy(request: Request):
    """Proxy MCP requests with fixed Accept headers."""
    # Get original body
    body = await request.body()
    
    # Forward with proper Accept header
    headers = dict(request.headers)
    headers["accept"] = "application/json, text/event-stream"
    
    # Remove problematic headers
    headers.pop("host", None)
    headers.pop("content-length", None)
    
    try:
        response = await client.post(
            TARGET_URL,
            content=body,
            headers=headers,
            timeout=30.0  # Add timeout
        )
        
        # Return the response
        content_type = response.headers.get("content-type", "application/json")
        
        if "text/event-stream" in content_type:
            # Stream SSE response
            from fastapi.responses import StreamingResponse
            return StreamingResponse(
                response.aiter_bytes(),
                media_type=content_type,
                headers=dict(response.headers)
            )
        else:
            # Try to parse as JSON, but handle non-JSON responses
            try:
                if response.content:
                    result = response.json()
                    
                    # Fix schemas if tools are present
                    if "result" in result and "tools" in result["result"]:
                        for tool in result["result"]["tools"]:
                            # Fix the items list issue
                            if "inputSchema" in tool:
                                fix_items_in_schema(tool["inputSchema"])
                    
                    return result
                else:
                    # Empty response
                    return {"result": {}}
                    
            except json.JSONDecodeError:
                # If not valid JSON, return as plain text
                return Response(
                    content=response.content,
                    media_type=content_type,
                    status_code=response.status_code,
                    headers=dict(response.headers)
                )
                
    except httpx.RequestError as e:
        # Handle connection errors
        return {
            "error": f"Connection failed to {TARGET_URL}",
            "detail": str(e)
        }


def fix_items_in_schema(schema):
    """Fix the items: [list] issue in schema."""
    if isinstance(schema, dict):
        for key, value in schema.items():
            if key == "items" and isinstance(value, list):
                # Convert list to proper schema
                schema[key] = {"anyOf": value}
            elif isinstance(value, (dict, list)):
                fix_items_in_schema(value)
    elif isinstance(schema, list):
        for item in schema:
            fix_items_in_schema(item)


@app.get("/health")
async def health():
    return {"status": "ok", "target": TARGET_URL}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9020)