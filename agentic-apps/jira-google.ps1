$root = "C:\Users\dell\Documents\GitHub\adk_google\agentic-apps"

Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd $root; uvicorn agents.jira_agent.jira_agent.agent:a2a_app --port 8003"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd $root; uvicorn app:app --port 8000"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd $root; uvicorn agents.workspace_agent.workspace_agent.agent:a2a_app --port 8006"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd $root\mcps\workspace_mcp; python main.py --transport streamable-http --single-user  "
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd $root; uvicorn agents.bigquery_agent.bigquery_fashion_agent.agent:a2a_app --port 8004"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd $root\mcps\bigquery_toolbox; ./toolbox --tools-file='fashion_tools.yaml' "

