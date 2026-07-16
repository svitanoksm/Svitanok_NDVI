import geopandas as gpd
import gspread
import json
import os
import pandas as pd
from google.oauth2.service_account import Credentials
import xml.etree.ElementTree as ET

def load_fields(file_path='fields.kml'):
    try:
        # Парсимо KML як XML, щоб уникнути суворої перевірки геометрії
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # Спроба витягти хоча б назви та прості дані
        # (Надалі ми розширимо це до повного парсингу координат)
        print("KML успішно розпарсено як XML!")
        return "XML_SUCCESS" 
    except Exception as e:
        return f"Помилка парсингу XML: {e}"

def get_google_sheet():
    creds_json = os.environ.get('GCP_JSON')
    creds_dict = json.loads(creds_json)
    scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)
    return client.open_by_key("1wxSZsPpWLFDhP6i6Apc3sWXPnHhJRqpcSGKFxKQRMus").sheet1

if __name__ == "__main__":
    status = load_fields()
    print(f"Статус зчитування: {status}")
    
    try:
        sheet = get_google_sheet()
        print("Доступ до таблиці успішний!")
    except Exception as e:
        print(f"Помилка таблиці: {e}")
