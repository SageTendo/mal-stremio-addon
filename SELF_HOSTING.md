# Self-Hosting Guide

This guide covers running your own instance of the MAL-Stremio Addon using Docker.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/) (Alternatively, you can use [Podman](https://podman.io/))
- A MyAnimeList API application (see below)

---

## 1. Create a MyAnimeList API Application

1. Go to [myanimelist.net/apiconfig](https://myanimelist.net/apiconfig) and click **Create ID**.
2. Fill in the form:
   - **App Name**: anything you like
   - **App Type**: `web`
   - **App Redirect URL**: `https://your-domain.com/callback`
     - Use `http://localhost:5000/callback` for local testing
    - **Homepage URL**: `https://your-domain.com`
3. Submit — you'll receive a **Client ID** and **Client Secret**.

> The redirect URL must exactly match your hosted instance's callback endpoint. If you change your domain later, update it here.

---

## 2. Configure the Environment

Copy the example file and fill in your values:

```bash
cp .env.example .env
```

Edit `.env` with the required values:

```dotenv
# Flask
FLASK_RUN_HOST=your-domain.com   # or localhost for local testing
FLASK_PORT=5000                  # host port the service is exposed on
SECRET_KEY=change-me-to-something-random

# MyAnimeList API
MAL_ID=your_mal_client_id
MAL_SECRET=your_mal_client_secret

# Database backend: "sqlite" (default) or "mongo"
DB_BACKEND=sqlite
```

---

## 3. Choose a Database Backend

### SQLite (default — no extra setup)

SQLite is the default. No additional configuration is needed. The database is stored in a persistent Docker volume automatically.

```bash
docker compose up -d
```

### MongoDB

Set the following in your `.env`:

```dotenv
DB_BACKEND=mongo
MONGO_URI=mongodb://mongo:27017
MONGO_DB=mal_stremio
MONGO_UID_MAP_COLLECTION=uid_token_mapping
```

Then start with the `mongo` profile to also launch the MongoDB container:

```bash
docker compose --profile mongo up -d
```

> If you have an existing external MongoDB instance, set `MONGO_URI` to its connection string and skip the `--profile mongo` flag — only the `backend` service will start.

---

## 4. Verify It's Running

```bash
docker compose ps          # check containers are up
docker compose logs -f     # stream logs
```

Open `http://localhost:5000` (or your domain) in a browser. You should see the addon's home page.

---

## 5. Install the Addon in Stremio

1. On the addon's home page, click **Generate Token** and authorize via MyAnimeList.
2. Copy the manifest URL shown after authorization.
3. In Stremio, paste the manifest URL into the addon search box and click **Install**.

---

## 6. Updating

```bash
docker compose pull          # pull latest base images (if using a pre-built image)
docker compose build --no-cache   # rebuild from source
docker compose up -d         # restart with new image
```

Add `--profile mongo` to any of the above commands if you are using MongoDB.

---

## Environment Variable Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `SECRET_KEY` | Yes | — | Flask session secret — set to a long random string |
| `MAL_ID` | Yes | — | MAL API client ID |
| `MAL_SECRET` | Yes | — | MAL API client secret |
| `FLASK_RUN_HOST` | Yes | `localhost` | Your public hostname (used to build the OAuth redirect URL) |
| `FLASK_PORT` | No | `5000` | Host port the service is exposed on |
| `DB_BACKEND` | No | `sqlite` | Database backend: `sqlite` or `mongo` |
| `SQLITE_PATH` | No | `/app/data/app.db` | Path inside the container for the SQLite file |
| `MONGO_URI` | If mongo | — | MongoDB connection string |
| `MONGO_DB` | If mongo | — | MongoDB database name |
| `MONGO_UID_MAP_COLLECTION` | If mongo | — | Collection name for user token storage |
| `FLASK_DEBUG` | No | `False` | Set to `True` to enable debug mode (do not use in production) |
