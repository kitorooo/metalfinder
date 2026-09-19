import streamlit as st
import json
from groq import Groq

# Твой ключ от Groq
GROQ_API_KEY = "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"

st.set_page_config(page_title="Heavy Music Finder", layout="centered")

if "step" not in st.session_state:
    st.session_state.step = 1

def get_recommendations(genres, excluded, vibe, tempo, obscurity):
    client = Groq(api_key=GROQ_API_KEY)
    
    # 1. Автоматически получаем список доступных моделей аккаунта
    models_data = client.models.list()
    available_model_ids = [m.id for m in models_data.data]
    
    # Приоритетный выбор: ищем llama-3, qwen, mixtral или берем первую доступную
    selected_model = None
    for pref in ["llama-3", "llama3", "mixtral", "gemma"]:
        match = next((m for m in available_model_ids if pref in m.lower()), None)
        if match:
            selected_model = match
            break
            
    if not selected_model:
        selected_model = available_model_ids[0]
        
    genres_str = ", ".join(genres) if genres else "Любые в рамках тяжелой сцены"
    excluded_str = excluded if excluded else "Нет исключений"
    
    prompt = f"""
    Ты эксперт по тяжелой, андеграундной и атмосферной музыке (Black Metal, Death Metal, Doom, Post-Punk, Shoegaze, Sludge, Drone и т.д.).
    
    Подбери ровно 5 полноформатных музыкальных альбомов под следующий запрос:
    - Предпочтительные направления: {genres_str}
    - Исключить группы: {excluded_str}
    - Описание вайба / настроения: "{vibe}"
    - Желаемый темп/динамика: {tempo}
    - Уровень андерграундности (от 1 до 10): {obscurity}

    Верни ответ СТРОГО в виде JSON-списка:
    [
      {{
        "band": "Название группы",
        "album": "Название альбома",
        "year": "Год выпуска",
        "genre": "Точный поджанр",
        "key_track": "Ключевой трек для ознакомления",
        "reason": "Почему этот альбом подходит под настроение (2-3 предложения на русском языке)"
      }}
    ]
    """
    
    response = client.chat.completions.create(
        model=selected_model,
        messages=[
            {"role": "system", "content": "Ты музыкальный эксперт. Отвечай только валидным JSON-массивом."},
            {"role": "user", "content": prompt}
        ]
    )
    
    content = response.choices[0].message.content.strip()
    if content.startswith("```json"):
        content = content[7:]
    elif content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
        
    return json.loads(content.strip())

# --- ЭКРАН 1: ГЛАВНАЯ ---
if st.session_state.step == 1:
    st.title("🕯️ Heavy Music Finder")
    st.subheader("Подбор релизов по вайбу, звуку и атмосфере")
    st.write("Открой для себя новый андерграунд: от сырого блэка до погребального дума.")
    
    if st.button("Найти альбом 🔥", type="primary"):
        st.session_state.step = 2
        st.rerun()

# --- ЭКРАН 2: ФИЛЬТРЫ И ЖАНРЫ ---
elif st.session_state.step == 2:
    st.title("Предпочтения и фильтры")
    
    fav_genres = st.multiselect(
        "Любимые направления:",
        ["Black Metal", "Atmospheric Black", "Death Metal", "Doom Metal", "Funeral Doom", "Post-Punk", "Shoegaze / Blackgaze", "Sludge", "Dark Ambient"]
    )
    
    excluded_bands = st.text_input("Группы, которые НЕ предлагать (через запятую):", placeholder="Behemoth, Metallica...")
    
    if st.button("Далее ➡️"):
        st.session_state.fav_genres = fav_genres
        st.session_state.excluded_bands = excluded_bands
        st.session_state.step = 3
        st.rerun()

# --- ЭКРАН 3: ВАЙБ И ПАРАМЕТРЫ ---
elif st.session_state.step == 3:
    st.title("Какого звучания хочется сейчас?")
    
    vibe_query = st.text_area(
        "Опиши ощущение своими словами:", 
        placeholder="Например: сырой заброшенный завод, холодный дождь, монотонный давящий ритм, эхо и редкий гроул..."
    )
    
    tempo = st.select_slider("Темп / Динамика:", options=["Похоронный медленный", "Размеренный / Монотонный", "Умеренный", "Шквальный / Бластбит"])
    obscurity = st.slider("Степень андерграундности (1 — культовая классика, 10 — кассетный самиздат):", 1, 10, 6)
    
    if st.button("Сгенерировать подборку 💀", type="primary"):
        if not vibe_query.strip():
            st.warning("Опиши хотя бы пару слов про атмосферу!")
        else:
            st.session_state.vibe_query = vibe_query
            st.session_state.tempo = tempo
            st.session_state.obscurity = obscurity
            st.session_state.step = 4
            st.rerun()

# --- ЭКРАН 4: ВЫДАЧА РЕЗУЛЬТАТОВ ---
elif st.session_state.step == 4:
    st.title("Твоя подборка альбомов")
    st.caption(f"Запрос: *{st.session_state.vibe_query}*")
    
    if "results" not in st.session_state:
        with st.spinner("Нейросеть ищет релизы..."):
            try:
                albums = get_recommendations(
                    st.session_state.fav_genres,
                    st.session_state.excluded_bands,
                    st.session_state.vibe_query,
                    st.session_state.tempo,
                    st.session_state.obscurity
                )
                st.session_state.results = albums
            except Exception as e:
                st.error(f"Ошибка при запросе: {e}")
                st.session_state.results = []

    for idx, item in enumerate(st.session_state.get("results", [])):
        with st.container(border=True):
            st.subheader(f"💽 {item['band']} — {item['album']} ({item['year']})")
            st.write(f"**Жанр:** `{item['genre']}`")
            st.write(f"**Рекомендуемый трек:** 🎵 *{item['key_track']}*")
            st.write(item["reason"])
            
            col1, col2, _ = st.columns([1, 1, 4])
            with col1:
                st.button("👍 Вкатило", key=f"like_{idx}")
            with col2:
                st.button("👎 Мимо", key=f"dislike_{idx}")

    st.write("---")
    if st.button("🔄 Новый поиск"):
        if "results" in st.session_state:
            del st.session_state["results"]
        st.session_state.step = 1
        st.rerun()
