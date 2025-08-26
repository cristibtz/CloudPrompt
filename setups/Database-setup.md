# Start database
```bash
docker run -d --name cloudprompt-db -e POSTGRES_USER="cloudprompt" -e POSTGRES_PASSWORD="cloudprompt" -e POSTGRES_DB="cloudprompt" -p 5432:5432 postgres:latest
```

# Migrations
```bash
cd backend/
alembic revision --autogenerate -m "Init Migration"
alembic upgrade head 
python3 seed_dummy_data.py 
```