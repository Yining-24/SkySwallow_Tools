import argparse
import subprocess

from waitress import serve

from skyswallow_tools import create_app
from skyswallow_tools.configuration import configure_instance


def main(argv=None):
    parser = argparse.ArgumentParser(description="SkySwallow Tools server")
    parser.add_argument(
        "--configure",
        action="store_true",
        help="Create the private first-time configuration",
    )
    arguments = parser.parse_args(argv)

    if arguments.configure:
        try:
            configure_instance()
        except (EOFError, KeyboardInterrupt, OSError, subprocess.SubprocessError) as error:
            print(f"Configuration was not completed: {error}")
            return 1

        return 0

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

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
