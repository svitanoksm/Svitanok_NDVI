import geopandas as gpd
import gspread
import json
import os
from google.oauth2.service_account import Credentials

def load_fields(file_path='fields.kml'):
    try:
        # Зчитуємо KML без додаткових драйверів
        fields = gpd.read_file(file_path)
        
        # Перевіряємо, чи є взагалі дані
        if fields.empty:
            return "Помилка: KML файл порожній"
            
        return fields
    except Exception as e:
        return f"Помилка зчитування KML: {e}"

def get_google_sheet():
    creds_json = os.environ.get('GCP_JSON')
    if not creds_json:
        raise ValueError("Секрет GCP_JSON не знайдено!")
        
    creds_dict = json.loads(creds_json)
    scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key("1wxSZsPpWLFDhP6i6Apc3sWXPnHhJRqpcSGKFxKQRMus").sheet1
    return sheet

if __name__ == "__main__":
    print("Починаємо процес...")
    fields_data = load_fields()
    
    if isinstance(fields_data, str):
        print(fields_data)
    else:
        print("Поля успішно завантажено!")
        # Виведемо назви стовпців, щоб зрозуміти структуру даних
        print(f"Колонки у файлі: {list(fields_data.columns)}")
    
    try:
        sheet = get_google_sheet()
        print("Доступ до таблиці отримано успішно!")
    except Exception as e:
        print(f"Помилка доступу до таблиці: {e}")
