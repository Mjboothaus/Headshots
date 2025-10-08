"""Main entry point for the Headshot Generator application."""

from headshot_generator import HeadshotApp


def main():
    """Run the Headshot Generator application."""
    app = HeadshotApp()
    app.run()


if __name__ == "__main__":
    main()