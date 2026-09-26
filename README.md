# 🎬 AutoScriptor — AI Video Script Cloner

**AutoScriptor** — инструмент для контент-мейкеров, ютуберов и авторов Shorts/Reels. Анализирует структуру и темп любого успешного видео на YouTube и переписывает его сценарий своими словами с сохранением высокой динамики и удержания.

---

## ✨ Что генерирует AutoScriptor:

1. 🔥 **3 виральных варианта заголовка** для видео;
2. ⚡ **Мощный хук** для первых 3 секунд, удерживающий зрителя;
3. 📜 **Готовый сценарий для озвучки** (динамичные, короткие абзацы);
4. 🎬 **B-Roll идеи для монтажа** и видеоряда;
5. 📌 **SEO-описание и хэштеги** для публикации.

---

## 🚀 Два режима запуска

### Режим 1: Онлайн (GitHub Pages)
Вы можете пользоваться сайтом прямо в браузере без установки:
👉 **[https://krshorts000-cell.github.io/AutoScriptor/](https://krshorts000-cell.github.io/AutoScriptor/)**

> 💡 **Рекомендация для онлайн-режима**: используйте **Google Gemini** (бесплатный ключ на [Google AI Studio](https://aistudio.google.com/apikey)) или официальный API DeepSeek. Они нативно поддерживают прямые запросы из браузера.

---

### Режим 2: Локальный запуск (с поддержкой AI STAR и любых прокси)
Если вы используете сторонние агрегаторы (например, **AI STAR `ai.starimg.ru`**), браузерные ограничения CORS блокируют прямые запросы к их API. 

Для этого в проект встроен легковесный локальный прокси-сервер на чистом Python:

1. Скачайте или клонируйте репозиторий:
   ```bash
   git clone https://github.com/krshorts000-cell/AutoScriptor.git
   ```
2. Запустите:
   - В Windows: просто дважды кликните **`run.bat`**
   - Либо в терминале:
     ```bash
     python server.py
     ```
3. Сайт автоматически откроется по адресу `http://localhost:8000` с отключенными ограничениями CORS.

---

## 🔑 Поддерживаемые нейросети

* **DeepSeek / AI STAR**:
  - `deepseek-chat` (Официальный DeepSeek V3)
  - `deepseek-v4-pro` (AI STAR / агрегаторы)
  - `deepseek-v4.1-flash` (AI STAR Flash)
  - `deepseek-reasoner` (DeepSeek R1)
  - *Автоматическое определение ключей `sk-star-...` с подстановкой `https://ai.starimg.ru/v1`*
* **Google Gemini**:
  - `gemini-1.5-flash` (быстрый и бесплатный)
  - `gemini-1.5-pro` (глубокий анализ)
  - `gemini-2.5-flash` (новейшее поколение)
* **Qwen (DashScope / Alibaba Cloud)**:
  - `qwen-plus`
  - `qwen-max`

---

## 🛠 Технологии

* **HTML5 / JavaScript (ES6+)**
* **Tailwind CSS** + **FontAwesome Icons**
* **Python 3 Standard Library** (`http.server` & `urllib`) — никаких лишних зависимостей (`pip install` не требуется)
* Извлечение транскриптов YouTube через независимый API