"""Application layers. A feature is split across them:

    routes/       APIRouter + endpoint signatures (HTTP only)
    controllers/  request -> service call -> response mapping; deps.py holds FastAPI dependencies
    services/     business rules, transactions
    repositories/ SQL (psycopg 3, dict rows)
    models/       internal data classes (rows from the DB)
    requests/     Pydantic input schemas
    responses/    Pydantic output schemas

See README.md, "Adding a feature".
"""
