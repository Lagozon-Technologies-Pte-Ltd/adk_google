$root = "C:\Users\dell\Documents\GitHub\adk_google\agentic-apps"

Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd $root\mcps\gmail_mcp; python server.py"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd $root; uvicorn agents.jira_agent.jira_agent.agent:a2a_app --port 8003"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd $root; uvicorn agents.gmail_agent.gmail_agent.agent:a2a_app --port 8002"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd $root; adk web manager_agent/jira-agent"