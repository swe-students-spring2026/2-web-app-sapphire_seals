### 1) Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running (includes Docker Compose).

### 2) Clone the repository

```bash
git clone https://github.com/swe-students-spring2026/2-web-app-sapphire_seals.git
cd 2-web-app-sapphire_seals
```

### 3) Configure environment variables (`.env`)

Create and configure a local `.env` file from the example:

```bash
cp .env.example .env
```

Notes:
- `FLASK_PORT` should be `5000` to match the default Docker port mapping in `docker-compose.yml`.
- If you change Mongo credentials, also update `MONGO_URL` so the username/password match.

### 4) Build and start the application

From the project root:

```bash
docker compose up --build
```

This starts:
- `flask-app` (Flask service)
- `mongodb` (MongoDB service)

### 5) Bootstrap the MongoDB data

In a new terminal (with containers still running), run:

```bash
cd mongodb
sh db-bootstrap.sh
cd ..
```

This imports the initial collections (`halls`, `menus`, `foods`, and `tags`) into MongoDB.

### 6) Access the running app

- App: `http://localhost:5000`
- Mongo health check route: `http://localhost:5000/mongo/ping/`