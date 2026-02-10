---
name: Docker Mandatory Execution
description: Enforce execution of backend and DB commands inside Docker containers.
---

# Docker Mandatory Execution Rule

## 🚨 CRITICAL INSTRUCTION 🚨

The **SISTEMA-GESTION-CESAR** project architecture relies strictly on Docker.
You must **NEVER** attempt to run backend Python scripts (`manage.py`, `alembic`, `uvicorn`) directly on the host machine's shell (Powershell/Bash), except for specific Orchestration scripts that explicitly require it (like `start-e2e.ts` launching a local process *only if configured to do so*, but even then, prefer Docker).

## 1. Database Management
ALWAYS use `manage.py` WITHOUT the `--local` flag to ensure commands run inside the `backend_FastOps` container.

- **Bad**: `python manage.py db --local upgrade` (Runs on host, fails due to missing env/deps)
- **Good**: `python manage.py db upgrade` (Executes `docker exec backend_FastOps ...`)

## 2. Testing Constraints
- E2E tests orchestrate services. If the test environment uses `docker-compose.test.yml`, ensure verify if a backend service is available to run commands.
- If no backend service is running in test mode:
  1. Use `docker-compose run backend ...`
  2. OR rely on the main `docker-compose.yml` stack being active.

## 3. Dependency Management
- Never try to install pip packages locally.
- If a package is missing, it must be added to `requirements.txt` and the container rebuilt.

## 4. Execution Protocol
Before running any python command:
1. Check if it targets the backend.
2. If yes, wrap it or trigger it via `manage.py` (which handles docker exec).
3. If you must run it manually, use: `docker exec -it backend_FastOps python <script>`

## 5. Gold Master Database (E2E Test Baseline)

The project maintains a **Gold Master SQL dump** that represents the exact database state after a manual Genesis flow. This is the baseline for all E2E tests.

**File location:** `tests-e2e/fixtures/gold_master.sql`

### 5.1 Restore Gold Master (Reset DB to test baseline)
```powershell
# PowerShell syntax (use Get-Content + pipe)
Get-Content tests-e2e/fixtures/gold_master.sql | docker exec -i container_DB_FastOps psql -U admin -d bdfastops
```

### 5.2 Export Gold Master (After manual configuration changes)
```powershell
docker exec container_DB_FastOps pg_dump -U admin -d bdfastops --clean --if-exists --no-owner --no-privileges > tests-e2e/fixtures/gold_master.sql
```

### 5.3 Verify DB State
```powershell
docker exec container_DB_FastOps psql -U admin -d bdfastops -c "SELECT 'companies' as tbl, count(*) FROM companies UNION ALL SELECT 'users', count(*) FROM users UNION ALL SELECT 'roles', count(*) FROM roles UNION ALL SELECT 'permissions', count(*) FROM permissions UNION ALL SELECT 'products', count(*) FROM products UNION ALL SELECT 'orders', count(*) FROM orders ORDER BY tbl;"
```

### 5.4 Gold Master Contents (as of 2026-02-09)
| Table | Count | Notes |
|---|---|---|
| permissions | 33 | System config (never changes) |
| companies | 1 | Manually created via Genesis |
| branches | 1 | Sede Principal |
| users | 4 | Admin + staff |
| roles | 6 | Configured roles |
| role_permissions | 68 | Permission assignments |
| subscriptions | 1 | Active plan |
| categories | 1 | Product category |
| products | 2 | Test products |
| tables | 10 | Restaurant tables |
| orders | 0 | Clean (no orders) |

### 5.5 Rules
- **NEVER seed data manually** for E2E tests. Always restore from gold_master.sql.
- **Tests run against live DB** (port 8000 backend, port 5173 frontend). No separate test containers.
- If the gold master needs updating, the user will manually configure the system and request a new export.
