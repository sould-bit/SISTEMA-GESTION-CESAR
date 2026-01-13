# Bolt's Journal ⚡

## Performance Bottlenecks & Learnings

### 1. SQLAlchemy + AsyncIO Overhead
- **Observation**: `InventoryService.update_stock` takes ~18ms per operation in a SQLite environment.
- **Context**: This includes creating an `InventoryTransaction`, updating `Inventory`, and `Product` stock check.
- **Optimization Potential**: While 18ms is acceptable for low load, under high concurrency (thousands of ops/sec), this might be a bottleneck. Bulk updates or optimizing the transaction scope could improve this.

### 2. Test Environment Configuration
- **Issue**: `socketio.ASGIApp` wraps the FastAPI app, causing `AttributeError: 'ASGIApp' object has no attribute 'dependency_overrides'` in tests.
- **Fix**: Modified `conftest.py` to unwrap the app using `app.other_asgi_app` when necessary.
- **Lesson**: Always check if the ASGI app is wrapped by middleware/adapters when writing `httpx` or `TestClient` tests.

### 3. Missing Data Constraints in Tests
- **Issue**: `sqlite3.IntegrityError` due to missing `code` in `Branch` and `hashed_password` in `User`.
- **Fix**: Updated test fixtures and factories to include these required fields.
- **Lesson**: Database constraints in `SQLModel` might be stricter or interpreted differently in SQLite vs PostgreSQL, especially with `NOT NULL`. Tests must populate all required fields.

### 4. RBAC Integration Complexity
- **Observation**: Integration tests for `ProductRouter` are failing with 403 Forbidden despite permission assignment attempts.
- **Hypothesis**: The RBAC system might rely on complex relationships (User -> Role -> RolePermission -> Permission) that are not fully set up or committed in the test transaction, or there is a cache/session visibility issue.
- **Action**: Added performance tests that bypass the HTTP layer to validate service logic efficiency directly, decoupling performance metrics from auth complexity.

### 5. Product Search Scalability
- **Observation**: Search latency for 1000 items is extremely low (~6ms) using SQLite + SQLModel optimization (loading specific columns).
- **Metric**: < 15ms for single item search, < 10ms for list retrieval.
- **Learning**: The use of `ProductListRead` schema which avoids loading heavy relationships (lazy loading avoided by explicit query or lightweight schema) works very well for performance. Future optimization should ensure this pattern is kept as complexity grows.
