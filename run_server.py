from waitress import serve

from skyswallow_tools import create_app


def main():
    app = create_app()

    host = app.config.get(
        "SERVER_HOST",
        "127.0.0.1",
    )
    port = app.config.get(
        "SERVER_PORT",
        5001,
    )

    print(f"SkySwallow Tools running on http://{host}:{port}")

    serve(
        app,
        host=host,
        port=port,
        threads=4,
    )


if __name__ == "__main__":
    main()
