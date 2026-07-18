import streamlit as st
import pandas as pd
import plotly.express as px

# Налаштування сторінки
st.set_page_config(layout="wide", page_title="Агро-аналітика")

# --- СТИЛІЗАЦІЯ ---
st.markdown("""
    <style>
    .full-width-btn {
        display: block;
        width: 100% !important;
        background-color: #e8f5e9;
        border: 1px solid #2e7d32;
        color: #2e7d32;
        padding: 10px;
        text-align: center;
        text-decoration: none;
        border-radius: 8px;
        font-weight: 600;
        margin-bottom: 10px;
        transition: all 0.3s;
    }
    .full-width-btn:hover {
        background-color: #2e7d32;
        color: white;
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

# --- ЛОГІКА НАВІГАЦІЇ ---
query_params = st.query_params
current_page = query_params.get("page", "Зведена аналітика")

# --- БІЧНЕ МЕНЮ ---
with st.sidebar:
    st.image("logo.png", use_container_width=True)
    st.markdown("---")
    
    st.markdown('<a href="/?page=Зведена+аналітика" target="_self" class="full-width-btn">Сівозміна</a>', unsafe_allow_html=True)
    st.markdown('<a href="/?page=Аналіз+одного+поля" target="_self" class="full-width-btn">Аналіз по полю</a>', unsafe_allow_html=True)
    st.markdown('<a href="/?page=Порівняння+культур" target="_self" class="full-width-btn">Аналіз в розрізі культур</a>', unsafe_allow_html=True)
    st.markdown('<a href="/?page=Максимальний+NDVI+по+полям" target="_self" class="full-width-btn">Максимальний NDVI по полям</a>', unsafe_allow_html=True)

# --- ОСНОВНА ЧАСТИНА ---
st.title("Агро-аналітика: Вегетація та сівозміна")
field_list = analytics.columns[2:].tolist()

if current_page == "Зведена аналітика":
    st.header("Розподіл культур по роках")
    years = sorted(rotation['Рік врожаю'].unique(), reverse=True)
    selected_year = st.selectbox("Оберіть рік врожаю", years)
    fields_in_year = rotation[rotation['Рік врожаю'] == selected_year]
    st.dataframe(fields_in_year[['№ поля', 'Культура', 'Площа посіву', 'Сорт, гібрид']], use_container_width=True)

elif current_page == "Аналіз одного поля":
    st.header("Детальний аналіз вегетації одного поля")
    selected_year = st.selectbox("Оберіть рік", sorted(analytics['Дата початку тижня'].dt.year.unique(), reverse=True))
    field_id = st.selectbox("Оберіть номер поля", field_list)
    
    if field_id:
        data_filtered = analytics[analytics['Дата початку тижня'].dt.year == selected_year]
        fig = px.line(data_filtered, x='Дата початку тижня', y=field_id, title=f"Вегетація поля №{field_id} у {selected_year} році")
        st.plotly_chart(fig, use_container_width=True)

elif current_page == "Порівняння культур":
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

elif current_page == "Максимальний NDVI по полям":
    st.header("🏆 Рейтинг полів (1 — найвища вегетація)")
    
    # 1. Розрахунок максимуму по кожному полю
    analytics_numeric = analytics[field_list].apply(pd.to_numeric, errors='coerce')
    field_max = analytics_numeric.max().reset_index()
    field_max.columns = ['Поле', 'Максимальна вегетація']
    field_max = field_max.sort_values(by='Максимальна вегетація', ascending=False)
    
    # 2. Визначення потенціалу (1-5) згідно з вашими діапазонами
    field_max['Потенціал'] = pd.cut(
        field_max['Максимальна вегетація'], 
        bins=[0.649, 0.688, 0.726, 0.764, 0.802, 0.841], 
        labels=[5, 4, 3, 2, 1]
    )
    
    # 3. Функція для кольорів: 1-й рейтинг — зелений, 5-й — жовтий
    def color_potentials(val):
        colors = {
            1: 'background-color: #2e7d32; color: white', # Зелений
            2: 'background-color: #66bb6a; color: black', 
            3: 'background-color: #fff176; color: black', 
            4: 'background-color: #fff59d; color: black', 
            5: 'background-color: #fbc02d; color: black'  # Жовтий
        }
        return colors.get(val, '')

    if not field_max.empty:
        st.subheader("Таблиця лідерів")
        # Стилізація колонки "Потенціал"
        styled_df = field_max.style.map(color_potentials, subset=['Потенціал'])
        st.dataframe(styled_df, use_container_width=True)
    else:
        st.warning("Дані для розрахунку відсутні.")
