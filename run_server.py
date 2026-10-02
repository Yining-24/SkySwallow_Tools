import argparse
import subprocess

from waitress import serve

from skyswallow_tools import create_app
from skyswallow_tools.configuration import configure_instance, set_shared_pin


def main(argv=None):
    parser = argparse.ArgumentParser(description="SkySwallow Tools server")
    management = parser.add_mutually_exclusive_group()
    management.add_argument(
        "--configure",
        action="store_true",
        help="Create the private first-time configuration",
    )
    management.add_argument(
        "--set-shared-pin", action="store_true",
        help="Set one shared six-digit PIN for all roles, preserving other settings",
    )
    arguments = parser.parse_args(argv)

    if arguments.configure or arguments.set_shared_pin:
        try:
            if arguments.set_shared_pin:
                set_shared_pin()
            else:
                configure_instance()
        except (EOFError, KeyboardInterrupt, OSError, subprocess.SubprocessError) as error:
            print(f"Configuration was not completed: {error}")
            if arguments.set_shared_pin:
                _pause_reset_window()
            return 1

        if arguments.set_shared_pin:
            _pause_reset_window()
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


def _pause_reset_window():
    try:
        input("Press Enter to close this window.")
    except (EOFError, KeyboardInterrupt):
        pass


if __name__ == "__main__":
    raise SystemExit(main())
