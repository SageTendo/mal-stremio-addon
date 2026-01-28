from typing import cast

from quart import Quart, current_app

from app.services.mal_service import MalService


class App(Quart):
    mal: MalService


def get_app() -> App:
    return cast(App, current_app)
