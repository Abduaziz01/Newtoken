"""
GitHub Daily Commit Bot — улучшенная версия
- Автовосстановление при ошибках
- Retry логика для GitHub API
- Валидация токена
- Защита от дублей коммитов
- Пауза/возобновление
- Подробный статус
- /reset для перезапуска

Установка: pip install python-telegram-bot requests apscheduler
Запуск:    BOT_TOKEN=токен python bot.py
"""

import os
import sqlite3
import asyncio
import base64
import logging
import time
from datetime import datetime, timezone
from functools import wraps

import requests
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Update, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes, ConversationHandler,
)
from telegram.error import TelegramError

# ─────────────────────────────────────────────
# НАСТРОЙКИ
# ─────────────────────────────────────────────
BOT_TOKEN   = os.getenv("BOT_TOKEN", "8552815437:AAFQoYpXIQxQq_PRHtVApWjFfql1mY7-S2Y")
DB_PATH     = "users.db"
COMMIT_HOUR = int(os.getenv("COMMIT_HOUR", "10"))   # час UTC для коммита
COMMIT_MIN  = int(os.getenv("COMMIT_MIN",  "0"))

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
log = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# СОСТОЯНИЯ ДИАЛОГА
# ─────────────────────────────────────────────
GITHUB_LOGIN, GITHUB_PASSWORD, REPO_NAME, FILE_UPLOAD = range(4)

# ─────────────────────────────────────────────
# БАЗА ДАННЫХ
# ─────────────────────────────────────────────
COLS = [
    "chat_id", "github_login", "github_token", "repo_name",
    "file_content", "file_name", "current_line", "total_lines",
    "setup_done", "paused", "last_commit_date", "fail_count",
]

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                chat_id          INTEGER PRIMARY KEY,
                github_login     TEXT,
                github_token     TEXT,
                repo_name        TEXT,
                file_content     TEXT,
                file_name        TEXT,
                current_line     INTEGER DEFAULT 0,
                total_lines      INTEGER DEFAULT 0,
                setup_done       INTEGER DEFAULT 0,
                paused           INTEGER DEFAULT 0,
                last_commit_date TEXT    DEFAULT '',
                fail_count       INTEGER DEFAULT 0
            )
