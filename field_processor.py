import geopandas as gpd
import gspread
import json
import os
from google.oauth2.service_account import Credentials

# 1. Функція зчитування полів
def load_fields(file_path='fields.kml'):
    try:
        fields = gpd.read_file(file_path, driver='KML')
        return fields
    except Exception as e:
        return f"Помилка зчитування KML: {e}"

# 2. Функція підключення до таблиці
def get_google_sheet():
    # Отримуємо JSON з секретів GitHub
    creds_json = os.environ.get('GCP_JSON')
    creds_dict = json.loads(creds_json)
    
    scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)
    
    # Відкриваємо таблицю за ID
    sheet = client.open_by_key("1wxSZsPpWLFDhP6i6Apc3sWXPnHhJRqpcSGKFxKQRMus").sheet1
    return sheet

# 3. Основна логіка виконання
if __name__ == "__main__":
    # Спочатку перевіряємо поля
    fields_data = load_fields()
    print("Поля завантажено:")
    print(fields_data)
    
    # Потім перевіряємо доступ до таблиці
    try:
        sheet = get_google_sheet()
        print("Доступ до таблиці отримано успішно!")
    except Exception as e:
        print(f"Помилка доступу до таблиці: {e}")
