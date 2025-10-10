"""Main entry point for the Headshot Generator application."""

from headshot_curator import HeadshotApp


def main():
    """Run the Headshot Generator application."""
    app = HeadshotApp()
    app.run()


if __name__ == "__main__":
    main()