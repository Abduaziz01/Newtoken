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
