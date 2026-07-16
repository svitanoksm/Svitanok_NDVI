import geopandas as gpd
import pandas as pd
import os

def load_fields(file_path='fields.kml'):
    """
    Зчитує поля з KML-файлу за допомогою geopandas.
    Автоматично обробляє MultiGeometry та інші складні структури.
    """
    if not os.path.exists(file_path):
        print(f"Помилка: Файл {file_path} не знайдено.")
        return pd.DataFrame()

    try:
        # geopandas автоматично парсить KML і створює GeoDataFrame
        gdf = gpd.read_file(file_path)
        
        # Перевіряємо, чи є в KML колонки з іменами (зазвичай це 'Name')
        if 'Name' in gdf.columns:
            df = gdf[['Name', 'geometry']].copy()
            df = df.rename(columns={'Name': 'name'})
        else:
            # Якщо імен немає, створюємо їх автоматично
            df = gdf[['geometry']].copy()
            df['name'] = [f"Поле_{i+1}" for i in range(len(df))]
            
        print(f"--- Успішно зчитано {len(df)} полів через geopandas ---")
        return df

    except Exception as e:
        print(f"Помилка зчитування KML через geopandas: {e}")
        return pd.DataFrame()

# Основний блок для тестування (виконується при запуску скрипта)
if __name__ == "__main__":
    # Для тесту вказуємо файл, який ви створили
    test_file = 'test_field.kml'
    fields_df = load_fields(test_file)
    
    if not fields_df.empty:
        print("Перші 5 записів:")
        print(fields_df.head())
    else:
        print("Не вдалося завантажити дані.")
