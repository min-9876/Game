import asyncio
import os
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
import uvicorn

# --- ENVIRONMENT VARIABLES ---
API_ID = int(os.getenv("API_ID", "1234567"))  # Coolify Environment တွင် ပြောင်းရန်
API_HASH = os.getenv("API_HASH", "your_api_hash")
BOT_TOKEN = os.getenv("BOT_TOKEN", "your_bot_token")
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://...")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://your-coolify-domain.com")
OWNER_USERNAME = os.getenv("OWNER_USERNAME", "YOUR_USERNAME")
SUPPORT_GROUP = os.getenv("SUPPORT_GROUP", "YOUR_SUPPORT_GROUP")

# --- INITIALIZATIONS ---
app = FastAPI()
bot = Client(
    "snake_game_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database Setup (MongoDB)
db_client = AsyncIOMotorClient(MONGO_URI)
db = db_client["snake_game_db"]
scores_collection = db["scores"]


# --- TELEGRAM BOT HANDLER ---
@bot.on_message(filters.command("start"))
async def start_handler(client, message):
  user = message.from_user
  welcome_text = (
      f"👋 မင်္ဂလာပါ **{user.first_name}** !\n\n"
      "🐍 Snake Arena ဂိမ်းကို Web App ဖြင့် တိုက်ရိုက်ကစားရန် နှင့် "
      "ထိပ်တန်းကစားသမားများ၏ အမှတ်စာရင်းများကို ကြည့်ရှုရန် အောက်ပါ "
      "Button ကိုနှိပ်ပါ။"
  )

  keyboard = InlineKeyboardMarkup([
      [
          InlineKeyboardButton(
              "🎮 Play Game & Leaderboard",
              web_app=WebAppInfo(url=WEBAPP_URL),
          )
      ],
      [
          InlineKeyboardButton(
              "👑 Owner", url=f"https://t.me/{OWNER_USERNAME}"
          ),
          InlineKeyboardButton(
              "🛠 Support", url=f"https://t.me/{SUPPORT_GROUP}"
          ),
      ],
  ])

  await message.reply_text(
      welcome_text, reply_markup=keyboard, parse_mode="markdown"
  )


# --- BACKEND API FOR LEADERBOARD ---
class ScoreModel(BaseModel):
  user_id: int
  first_name: str
  score: int


@app.post("/api/save_score")
async def save_score(data: ScoreModel):
  existing = await scores_collection.find_one({"user_id": data.user_id})
  if existing:
    if data.score > existing["score"]:
      await scores_collection.update_one(
          {"user_id": data.user_id},
          {
              "$set": {
                  "score": data.score,
                  "first_name": data.first_name,
                  "updated_at": datetime.utcnow(),
              }
          },
      )
  else:
      await scores_collection.insert_one({
          "user_id": data.user_id,
          "first_name": data.first_name,
          "score": data.score,
          "updated_at": datetime.utcnow(),
      })
  return {"status": "success"}


@app.get("/api/leaderboard")
async def get_leaderboard():
  cursor = scores_collection.find({}).sort("score", -1).limit(10)
  top_players = []
  async for doc in cursor:
    top_players.append(
        {"first_name": doc["first_name"], "score": doc["score"]}
    )
  return {"status": "success", "top_players": top_players}


# Serve Static Frontend Files
app.mount("/", StaticFiles(directory="static", html=True), name="static")


# --- RUNNER ---
async def main():
  await bot.start()
  print("🤖 Telegram Bot Started Successfully!")
  config = uvicorn.Config(app, host="0.0.0.0", port=8080, log_level="info")
  server = uvicorn.Server(config)
  await server.serve()


if __name__ == "__main__":
  asyncio.run(main())
