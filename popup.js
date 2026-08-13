document.addEventListener('DOMContentLoaded', () => {
  // Подгружаем сохраненные настройки
  const storedKey = localStorage.getItem('ai_api_key');
  const storedProvider = localStorage.getItem('ai_provider');
  if (storedKey) document.getElementById('apiKey').value = storedKey;
  if (storedProvider) document.getElementById('aiProvider').value = storedProvider;
});

document.getElementById('submitBtn').addEventListener('click', async () => {
  const key = document.getElementById('apiKey').value.trim();
  const provider = document.getElementById('aiProvider').value;
  
  if (!key) return alert("❌ Введите API ключ!");
  
  // Сохраняем ключи
  localStorage.setItem('ai_api_key', key);
  localStorage.setItem('ai_provider', provider);
  
  // Меняем интерфейс
  document.getElementById('submitBtn').classList.add('hidden');
  document.getElementById('loader').classList.remove('hidden');
  document.getElementById('resultContainer').classList.add('hidden');

  try {
    // 1. Получаем доступ к текущей открытой вкладке
    let [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    if (!tab.url.includes("youtube.com")) {
      throw new Error("Расширение работает только на страницах YouTube (Видео или Shorts)!");
    }

    // 2. Внедряем скрипт-парсер прямо в страницу YouTube
    const injection = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: extractSubtitlesFromYouTubePage
    });

    const transcript = injection[0].result;
    if (!transcript) throw new Error("Субтитры не найдены. Возможно, они полностью отключены автором.");

    // 3. Отправляем в ИИ
    const aiData = await callAI(provider, key, transcript);

    // 4. Отрисовываем результаты
    document.getElementById('resTitleHook').innerText = (Array.isArray(aiData.title) ? aiData.title.join(' | ') : aiData.title) + "\n\nХУК:\n" + aiData.hook;
    document.getElementById('resScript').innerText = aiData.script;
    document.getElementById('resSEO').innerText = aiData.seo_description + "\n\n" + aiData.hashtags;
    
    document.getElementById('resultContainer').classList.remove('hidden');

  } catch (err) {
    alert("⚠️ Ошибка: " + err.message);
  } finally {
    document.getElementById('submitBtn').classList.remove('hidden');
    document.getElementById('loader').classList.add('hidden');
  }
});

// ==========================================
// ЭТА ФУНКЦИЯ ВЫПОЛНЯЕТСЯ ВНУТРИ YOUTUBE
// ==========================================
async function extractSubtitlesFromYouTubePage() {
  try {
    let tracks = null;
    
    // Ищем скрытый объект ytInitialPlayerResponse в коде страницы
    const match = document.body.innerHTML.match(/"captionTracks":(\[.*?\])/);
    if (match) {
      tracks = JSON.parse(match[1]);
    }
    
    if (!tracks || tracks.length === 0) return null;
    
    // Выбираем русский, английский или дефолтный трек
    let track = tracks.find(t => t.languageCode === 'ru') || tracks.find(t => t.languageCode === 'en') || tracks[0];
    
    // Скачиваем XML (запрос разрешен, так как мы уже находимся на домене youtube.com)
    const res = await fetch(track.baseUrl);
    const xml = await res.text();
    
    // Очищаем XML от тегов и таймкодов
    return xml
      .replace(/<[^>]+>/g, ' ')
      .replace(/&amp;/g, '&')
      .replace(/&quot;/g, '"')
      .replace(/&#39;/g, "'")
      .replace(/\s+/g, ' ')
      .trim();
  } catch (e) {
    return null;
  }
}

// ==========================================
// ЛОГИКА ЗАПРОСА К НЕЙРОСЕТЯМ
// ==========================================
async function callAI(provider, key, text) {
  const prompt = `Ты эксперт по контенту на YouTube и создании Shorts/Reels с высоким удержанием. 
Перепиши этот сценарий своими словами, сохранив динамику для быстрого монтажа, но сделай его уникальным.
Формат ответа СТРОГО в JSON (без маркдауна):
{
  "title": "3 кликабельных заголовка",
  "hook": "Мощный хук для первых 3 секунд",
  "script": "Полный текст сценария",
  "seo_description": "SEO описание",
  "hashtags": "#тег1 #тег2"
}`;

  let endpoint, headers, body;

  if (provider === 'gemini') {
    endpoint = `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${key}`;
    headers = { "Content-Type": "application/json" };
    body = {
      contents: [{ role: "user", parts: [{ text: prompt + "\n\nИсходник:\n" + text }] }],
      generationConfig: { responseMimeType: "application/json" }
    };
  } else {
    endpoint = provider === 'qwen' 
      ? "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions" 
      : "https://api.deepseek.com/chat/completions";
    
    headers = { "Content-Type": "application/json", "Authorization": `Bearer ${key}` };
    body = {
      model: provider === 'qwen' ? "qwen-plus" : "deepseek-chat",
      messages: [
        { role: "system", content: prompt },
        { role: "user", content: "Исходник:\n" + text }
      ],
      response_format: { type: "json_object" }
    };
  }

  const res = await fetch(endpoint, { method: "POST", headers, body: JSON.stringify(body) });
  const rawData = await res.json();

  if (!res.ok) throw new Error(rawData.error?.message || "Ошибка API ИИ");

  let contentStr = provider === 'gemini' 
    ? rawData.candidates[0].content.parts[0].text 
    : rawData.choices[0].message.content;

  contentStr = contentStr.replace(/```json/gi, '').replace(/```/gi, '').trim();
  return JSON.parse(contentStr);
}
