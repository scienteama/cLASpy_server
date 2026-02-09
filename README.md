# README for CLASPY Server

## Installation

1. Clone the repository:

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```
3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Launch and install Database:
   ```
   cd db

   docker network create claspy-net

   docker compose -f docker-compose.db.yml up -d

   ```
5. Apply migrations and seed db:
   ```
   alembic upgrade head

   python -m db.seed  

   ```

## Configuration

Before running the application, ensure that the database configuration in `app/database.py` is set correctly. Update the `DATABASE_URL` with your PostgreSQL credentials.

## Running the Application

To start the application, run:
```
python -m app.main
```

## Database Migrations

Database migrations are managed using Alembic. To create a new migration, run:
```
alembic revision --autogenerate -m "Migration message"
```

To apply migrations, run:
```
alembic upgrade head
```
