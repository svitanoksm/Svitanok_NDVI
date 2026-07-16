import pandas as pd
import gspread
import json
import os
from fastkml import kml
from shapely.geometry import shape
from google.oauth2.service_account import Credentials

# 1. Надійна функція зчитування KML
def load_fields(file_path='fields.kml'):
    try:
        with open(file_path, 'rb') as f:
            k = kml.KML()
            k.from_string(f.read())
        
        features = []
        
        # Доступ до об'єктів без виклику функцій
        def traverse(feature):
            # Якщо це Placemark, додаємо його
            if isinstance(feature, kml.Placemark):
                features.append({'name': feature.name, 'geometry': shape(feature.geometry)})
            # Якщо є вкладені об'єкти, перевіряємо їх
            if hasattr(feature, 'features'):
                # Доступ до властивості features без дужок
                child_features = feature.features
                if callable(child_features):
                    for f in child_features():
                        traverse(f)
                elif isinstance(child_features, (list, tuple)):
                    for f in child_features:
                        traverse(f)

        # Починаємо обхід
        for feature in list(k.features()):
            traverse(feature)
        
        return pd.DataFrame(features)
    except Exception as e:
        return f"Помилка зчитування KML: {e}"

# 2. Функція підключення до Google Таблиці
def get_google_sheet():
    creds_json = os.environ.get('GCP_JSON')
    if not creds_json:
        raise ValueError("Секрет GCP_JSON не знайдено в налаштуваннях GitHub!")
    
    creds_dict = json.loads(creds_json)
    scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)
    
    # Відкриваємо таблицю
    return client.open_by_key("1wxSZsPpWLFDhP6i6Apc3sWXPnHhJRqpcSGKFxKQRMus").sheet1

# 3. Основна логіка
if __name__ == "__main__":
    print("--- Початок обробки ---")
    
    # Крок 1: Зчитуємо поля
    fields_df = load_fields()
    if isinstance(fields_df, pd.DataFrame):
        print(f"Успішно зчитано {len(fields_df)} полів.")
        print(f"Перші поля: {list(fields_df['name'].head())}")
    else:
        print(fields_df) # Виведе помилку, якщо щось не так
        
    # Крок 2: Перевіряємо таблицю
    try:
        sheet = get_google_sheet()
        print("Доступ до Google Таблиці успішний!")
    except Exception as e:
        print(f"Помилка доступу до таблиці: {e}")
        
    print("--- Обробку завершено ---")
