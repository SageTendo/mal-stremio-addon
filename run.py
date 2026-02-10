import logging

from app.factory import create_app

logging.basicConfig(format="%(asctime)s %(message)s")

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
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5000)
