import streamlit as st
import pandas as pd
import plotly.express as px

# Налаштування сторінки
st.set_page_config(layout="wide", page_title="Агро-аналітика")

# --- СТИЛІЗАЦІЯ ---
st.markdown("""
    <style>
    /* Стиль для всіх кнопок у сайдбарі */
    section[data-testid="stSidebar"] button {
        width: 100% !important;
        background-color: #e8f5e9 !important;
        border: 1px solid #2e7d32 !important;
        color: #2e7d32 !important;
        border-radius: 8px !important;
        padding: 15px 20px !important;
        font-weight: 600 !important;
        transition: all 0.3s;
    }
    /* Стиль при наведенні */
    section[data-testid="stSidebar"] button:hover {
        background-color: #2e7d32 !important;
        color: white !important;
        border-color: #1b5e20 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- ЗАВАНТАЖЕННЯ ДАНИХ ---
@st.cache_data(ttl=60)
def load_data():
    url_analytics = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS8w914SbEs4NIAQfwnj-QWD7dbF7G4ucRS6uBIw5vm9VAFSVzLWmrt6SU28clR08tcHl-TmEOZQ2aM/pub?gid=0&single=true&output=csv"
    url_rotation = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTssArF-8XWc7p8ZhZ5MsQkK7xsoluBbSY7jcNnupbCQfn3M2UrP-YmnQYDWSc3Ozjghu2_sZQHgf05/pub?gid=1536656189&single=true&output=csv"
    
    analytics = pd.read_csv(url_analytics, dtype=str)
    rotation = pd.read_csv(url_rotation)
    
    field_cols = [col for col in analytics.columns if col not in ['Дата початку тижня', 'Тиждень']]
    for col in field_cols:
        analytics[col] = analytics[col].str.replace(',', '.').astype(float)
    
    analytics['Дата початку тижня'] = pd.to_datetime(analytics['Дата початку тижня'])
    rotation['№ поля'] = rotation['№ поля'].astype(str)
    
    return analytics, rotation

analytics, rotation = load_data()

# Ініціалізація сторінки
if 'page' not in st.session_state:
    st.session_state.page = "Зведена аналітика"

# --- БІЧНЕ МЕНЮ ---
with st.sidebar:
    # Додавання логотипу
    st.image("logo.png", use_container_width=True)
        
    st.markdown("---")
    if st.button("Зведена аналітика"): st.session_state.page = "Зведена аналітика"
    if st.button("Аналіз одного поля"): st.session_state.page = "Аналіз одного поля"
    if st.button("Порівняння культур"): st.session_state.page = "Порівняння культур"

# --- ОСНОВНА ЧАСТИНА ---
st.title("🌾 Агро-аналітика: Вегетація та сівозміна")
field_list = [col for col in analytics.columns if col not in ['Дата початку тижня', 'Тиждень']]

if st.session_state.page == "Зведена аналітика":
    st.header("Розподіл культур по роках")
    years = sorted(rotation['Рік врожаю'].unique(), reverse=True)
    selected_year = st.selectbox("Оберіть рік врожаю", years)
    fields_in_year = rotation[rotation['Рік врожаю'] == selected_year]
    st.dataframe(fields_in_year[['№ поля', 'Культура', 'Площа посіву', 'Сорт, гібрид']], use_container_width=True)

elif st.session_state.page == "Аналіз одного поля":
    st.header("Детальний аналіз вегетації одного поля")
    
    # Додаємо фільтр за роком
    selected_year = st.selectbox("Оберіть рік", sorted(analytics['Дата початку тижня'].dt.year.unique(), reverse=True))
    
    # Додаємо фільтр за полем
    field_id = st.selectbox("Оберіть номер поля", field_list)
    
    if field_id:
        # Фільтруємо дані за вибраним роком
        data_filtered = analytics[analytics['Дата початку тижня'].dt.year == selected_year]
        
        # Побудова графіка за відфільтрованими даними
        fig = px.line(data_filtered, x='Дата початку тижня', y=field_id, title=f"Вегетація поля №{field_id} у {selected_year} році")
        st.plotly_chart(fig, use_container_width=True)

elif st.session_state.page == "Порівняння культур":
    st.header("Порівняння полів")
    field_id = st.selectbox("Оберіть базове поле", field_list)
    if field_id:
        selected_year = st.selectbox("Оберіть рік", sorted(analytics['Дата початку тижня'].dt.year.unique(), reverse=True))
        crop_info = rotation[(rotation['№ поля'] == field_id) & (rotation['Рік врожаю'] == selected_year)]
        if not crop_info.empty:
            crop_name = crop_info.iloc[0]['Культура']
            others = rotation[(rotation['Культура'] == crop_name) & (rotation['Рік врожаю'] == selected_year)]['№ поля'].unique()
            valid_others = [f for f in others if f in analytics.columns]
            data = analytics[analytics['Дата початку тижня'].dt.year == selected_year]
            fig = px.line(data, x='Дата початку тижня', y=valid_others, title=f"Порівняння: {crop_name} ({selected_year})")
            st.plotly_chart(fig, use_container_width=True)
