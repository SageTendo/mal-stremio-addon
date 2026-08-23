from typing import cast

from quart import Quart, current_app

from app.services.cinemeta_service import CinemetaService
from app.services.kitsu_service import KitsuService
from app.services.mal_service import MalService


class App(Quart):
    mal: MalService
    kitsu: KitsuService
    cinemeta: CinemetaService


def get_app() -> App:
    return cast(App, current_app)
