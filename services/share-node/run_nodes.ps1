# run_nodes.ps1 — ShardLock Share Nodes
# Run from services/share-node/

# Node 1 — port 8001
Start-Process powershell -ArgumentList "-NoExit", "-Command", `
    "cd '$PWD'; venv\Scripts\activate; `$env:NODE_ID='node-1'; `$env:PORT='8001'; `$env:DATABASE_URL='sqlite+aiosqlite:///./node1.db'; `$env:INTERNAL_SERVICE_TOKEN='shardlock-internal-dev-token-change-in-prod'; `$env:DEBUG='true'; uvicorn main:app --port 8001 --reload"

Start-Sleep -Seconds 2

# Node 2 — port 8002
Start-Process powershell -ArgumentList "-NoExit", "-Command", `
    "cd '$PWD'; venv\Scripts\activate; `$env:NODE_ID='node-2'; `$env:PORT='8002'; `$env:DATABASE_URL='sqlite+aiosqlite:///./node2.db'; `$env:INTERNAL_SERVICE_TOKEN='shardlock-internal-dev-token-change-in-prod'; `$env:DEBUG='true'; uvicorn main:app --port 8002 --reload"

Start-Sleep -Seconds 2

# Node 3 — port 8003
Start-Process powershell -ArgumentList "-NoExit", "-Command", `
    "cd '$PWD'; venv\Scripts\activate; `$env:NODE_ID='node-3'; `$env:PORT='8003'; `$env:DATABASE_URL='sqlite+aiosqlite:///./node3.db'; `$env:INTERNAL_SERVICE_TOKEN='shardlock-internal-dev-token-change-in-prod'; `$env:DEBUG='true'; uvicorn main:app --port 8003 --reload"

Start-Sleep -Seconds 2

# Node 4 — port 8004
Start-Process powershell -ArgumentList "-NoExit", "-Command", `
    "cd '$PWD'; venv\Scripts\activate; `$env:NODE_ID='node-4'; `$env:PORT='8004'; `$env:DATABASE_URL='sqlite+aiosqlite:///./node4.db'; `$env:INTERNAL_SERVICE_TOKEN='shardlock-internal-dev-token-change-in-prod'; `$env:DEBUG='true'; uvicorn main:app --port 8004 --reload"

Write-Host ""
Write-Host "All 4 share nodes starting..." -ForegroundColor Green
Write-Host "  Node 1: http://localhost:8001/health" -ForegroundColor Cyan
Write-Host "  Node 2: http://localhost:8002/health" -ForegroundColor Cyan
Write-Host "  Node 3: http://localhost:8003/health" -ForegroundColor Cyan
Write-Host "  Node 4: http://localhost:8004/health" -ForegroundColor Cyan