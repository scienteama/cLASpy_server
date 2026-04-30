# README for CLASPY Server

## Installation

1. Clone the repository:

2. Create a virtual environment:
   ``` bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```
3. Install the required packages:
   ``` bash
   pip install -r requirements.txt
   ```

4. Launch and install Database:
   ``` bash
   cd db

   docker network create claspy-net

   docker compose -f docker-compose.db.yml up -d

   ```
5. Apply migrations and seed db:
   ``` bash
      alembic upgrade head

      python -m db.seed  

   ```

## Configuration

Before running the application, ensure that the database configuration in `app/database.py` is set correctly. Update the `DATABASE_URL` with your PostgreSQL credentials.

## Running the Application

To start the application, run:
``` bash
poetry run python -m app.main
```

To format code, run:
``` bash
poetry run black .
```

To lint and auto-fix issues
``` bash
poetry run ruff check .

poetry run ruff check . --fix
```

## Database Migrations

Database migrations are managed using Alembic. To create a new migration, run:
``` bash
poetry run alembic -c db/alembic.ini revision --autogenerate -m "Migration message"
```

To apply migrations, run:
``` bash
poetry run alembic -c db/alembic.ini upgrade head
```

## TaskRunner 

Launch taskrunner infra with .env integration: 
``` bash
python -m taskrunner.cli start-infra --env-file .env
```

Start worker with .env integration and "ml" queue : 

``` bash
python -m taskrunner.cli start-worker --queue ml --env-file .env
```