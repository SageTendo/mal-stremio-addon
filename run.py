import logging

import uvicorn

from app.factory import create_app
from app.services.anime_mapping import load_mapping_db

logging.basicConfig(format="%(asctime)s %(message)s")

load_mapping_db()
app = create_app()


@app.before_serving
async def startup():
    await app.mal.start()
    await app.kitsu.start()


@app.after_serving
async def shutdown():
    await app.mal.stop()
    await app.kitsu.stop()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
