"""Entry point for the Prom generator application."""
from __future__ import annotations

from database import init_db
from ui.app import App


def main() -> None:
    init_db()
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
