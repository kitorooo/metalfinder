import streamlit as st
import json
from google import genai
from google.genai import types

# Вставь сюда свой API-ключ Gemini
GEMINI_API_KEY = "ВСТАВЬ_СВОЙ_КЛЮЧ_СЮДА"

st.set_page_config(page_title="Heavy Music Finder", layout="centered")

if "step" not in st.session_state:
    st.session_state.step = 1

def get_recommendations(genres, excluded, vibe, tempo, obscurity):
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    prompt = f"""
    Ты эксперт по тяжелой, андеграундной и атмосферной музыке (Black Metal, Death Metal, Doom, Post-Punk, Shoegaze, Sludge, Drone и т.д.).
    
    Подбери ровно 5 полноформатных музыкальных альбомов под следующий запрос:
    - Предпочтительные направления: {', '.join(genres) if genres else 'Любые в рамках тяжелой сцены'}
    - Исключить группы: {excluded if excluded else 'Нет исключений'}
    - Описание вайба / настроения: "{vibe}"
    - Желаемый темп/динамика: {tempo}
    - Уровень андерграундности (от 1 до 10): {obscurity}

    Верни ответ СТРОГО в виде JSON списка:
    [
      {{
        "band": "Название группы",
        "album": "Название альбома",
        "year": "Год выпуска",
        "genre": "Точный поджанр",
        "key_track": "Ключевой трек для ознакомления",
        "reason": "Почему этот альбом подходит под настроение (2-3 предложения)"
      }}
    ]
    """
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        )
    )
    return json.loads(response.text)

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
        with st.spinner("Нейросеть вглядывается в бездну и ищет релизы..."):
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