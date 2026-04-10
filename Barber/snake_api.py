import sqlite3
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

DB_PATH = os.path.join(os.path.dirname(__file__), "snake_scores.db")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_name TEXT NOT NULL,
            score INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


init_db()


class ScoreSubmission(BaseModel):
    player_name: str
    score: int


@app.get("/leaderboard")
def get_leaderboard():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT player_name, score, created_at FROM scores ORDER BY score DESC LIMIT 10"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.post("/score")
def submit_score(submission: ScoreSubmission):
    name = submission.player_name.strip()[:30]
    if not name:
        return {"error": "Player name is required"}, 400
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO scores (player_name, score) VALUES (?, ?)",
        (name, submission.score),
    )
    conn.commit()
    conn.close()
    return {"status": "ok"}


# Serve the Mini App HTML
app.mount("/static", StaticFiles(directory=os.path.dirname(__file__)), name="static")


@app.get("/snake_app.html")
def serve_snake_app():
    return FileResponse(os.path.join(os.path.dirname(__file__), "snake_app.html"))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("SNAKE_API_PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
