# Barber Style Bot

A Telegram bot for barbershops with two features:
- **AI Hairstyle Recommendations** — customers send a photo and get 6 personalized hairstyle options generated on their actual photo
- **Barber Snake Game** — a mobile-first snake game customers can play while waiting, with a persistent leaderboard

---

## Architecture

```
Barber/
  bot.py               # Telegram bot (polling, runs locally or on a server)
  config.py            # Environment config and message templates
  openai_service.py    # Grok Vision analysis + OpenAI image generation
  api/
    _kv.py             # Vercel KV (Redis) helper
    leaderboard.py     # GET /api/leaderboard  — Vercel serverless function
    score.py           # POST /api/score        — Vercel serverless function
  public/
    snake_app.html     # Snake game (served as static file on Vercel)
  vercel.json          # Vercel deployment config
  requirements.txt     # Python dependencies
```

**The snake game + leaderboard API** are deployed on Vercel (free tier).  
**The Telegram bot** runs separately (locally with ngrok, or on any server).

---

## Features

### AI Hairstyle Recommendations
1. User sends a photo of their face
2. Grok Vision (xAI) analyzes hair type, texture, and face shape
3. OpenAI `gpt-image-1` generates 6 edited versions of the photo with different hairstyles
4. Bot sends all 6 images with style names and explanations

### Barber Snake Game
- Barbershop-themed design (gold palette, animated barber pole stripe)
- On-screen D-pad controls (up/down/left/right buttons) — no swipe, works inside Telegram
- Speed increases as score grows
- Snake has eyes, gold gradient body, and pulsing red food
- Floating "+10" popups and score glow animation
- Confetti effect for top 3 leaderboard finishes
- Haptic feedback via Telegram WebApp API

### Leaderboard
- Top 5 scores shown on the game's first screen
- "Show all" button expands to full ranking
- Scores stored in Vercel KV (Redis) — serverless, persistent, free
- Each game is recorded separately (not just best per player)

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment variables

Copy `.env.example` to `.env` and fill in the values:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
XAI_API_KEY=your_xai_api_key
OPENAI_API_KEY=your_openai_api_key
SNAKE_WEBAPP_URL=https://your-project.vercel.app/snake_app.html
SNAKE_API_PORT=8080
```

### 3. Get API keys

| Key | Where to get it |
|-----|----------------|
| `TELEGRAM_BOT_TOKEN` | [@BotFather](https://t.me/BotFather) on Telegram |
| `XAI_API_KEY` | [console.x.ai](https://console.x.ai) |
| `OPENAI_API_KEY` | [platform.openai.com](https://platform.openai.com) |

---

## Deploy the Snake Game to Vercel

### 1. Push to GitHub and import to Vercel

```bash
# Make sure snake_scores.db and .env are in .gitignore (they are)
git init
git add .
git commit -m "Initial commit"
# Push to GitHub, then import at vercel.com
```

### 2. Add Vercel KV storage

In the Vercel dashboard:
1. Go to **Storage** → **Create** → **KV**
2. Connect it to your project
3. Vercel automatically sets `KV_REST_API_URL` and `KV_REST_API_TOKEN` as env vars

### 3. Set environment variable in Vercel

In **Settings → Environment Variables**, add:
- `SNAKE_WEBAPP_URL` = `https://your-project.vercel.app/snake_app.html`

### 4. Update your local .env

```env
SNAKE_WEBAPP_URL=https://your-project.vercel.app/snake_app.html
```

Then restart the bot.

---

## Run the Bot

```bash
python bot.py
```

For the game to be accessible in Telegram during local development, the Vercel deployment must be live (or use ngrok to expose `snake_api.py` locally).

### Local development with the old FastAPI server

If you want to test the snake game locally before deploying:

```bash
python snake_api.py  # runs on port 8080
# In another terminal:
ngrok http 8080
# Set SNAKE_WEBAPP_URL in .env to the ngrok URL + /snake_app.html
```

---

## Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Show welcome message and main menu |
| `/help` | Show usage instructions |
| Send a photo | Trigger AI hairstyle analysis |
| "Choose Hair Style" button | Prompt for photo |
| "Play" button | Open the Snake game |

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Telegram bot | python-telegram-bot 21.6, polling mode |
| Vision analysis | Grok Vision (`grok-4-1-fast-non-reasoning`) via xAI API |
| Image generation | OpenAI `gpt-image-1` (photo editing) |
| Snake game | HTML5 Canvas, vanilla JS, Telegram WebApp API |
| Leaderboard API | Vercel serverless Python functions |
| Score storage | Vercel KV (Upstash Redis) |
| Hosting | Vercel (free tier) |
