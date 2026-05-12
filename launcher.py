import uvicorn
from app.core.config import get_settings, print_banner


def main():
    print_banner()
    config = get_settings()

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


if __name__ == "__main__":
    main()
