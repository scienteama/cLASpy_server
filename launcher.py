import uvicorn
from app.core.config import get_settings, print_banner


# This is the main entry point of the application. It initializes the database and starts the FastAPI server.
def main():
    config = get_settings()
    print_banner(config)

    # use_https = config.ENV != "production"

    uvicorn.run(
        "app.main:socket_app",
        host=config.HOST,
        port=config.PORT,
        reload=(config.ENV == "development"),
        log_config=config.get_log_config(),
        log_level="debug" if config.ENV == "development" else "info",
        # ssl_keyfile=(config.PROJECT_ROOT / "certificats/claspy_key.pem" if use_https else None),
        # ssl_certfile=(config.PROJECT_ROOT / "certificats/claspy_cert.pem" if use_https else None),
    )


# This function initializes the database by running the init_sqlite function from the db/init_sqlite.py script.
def init_db():
    from db.init_sqlite import init_sqlite
    import asyncio

    asyncio.run(init_sqlite())


if __name__ == "__main__":
    init_db()
    main()
