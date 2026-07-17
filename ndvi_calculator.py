import ee
import geopandas as gpd
import gspread
import time
from datetime import datetime, timedelta
from oauth2client.service_account import ServiceAccountCredentials

# 1. Налаштування
SPREADSHEET_NAME = 'NDVI_Svitanok_SM'
SHEET_NAME = 'NDVI'
KML_FILE = 'fields_2026.kml'
PROJECT_ID = 'agro-ndvi-system'

# 2. Ініціалізація
ee.Initialize(project=PROJECT_ID)
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
client = gspread.authorize(creds)

spreadsheet = client.open(SPREADSHEET_NAME)
sheet = spreadsheet.worksheet(SHEET_NAME)

# 3. Функції для розрахунку
def load_kml_geometry(row_geometry):
    geom = row_geometry
    if geom.geom_type == 'MultiPolygon':
        geom = geom.geoms[0]
    coords = [[p[0], p[1]] for p in geom.exterior.coords]
    return ee.Geometry.Polygon([coords])

def get_ndvi(geometry):
    # Шукаємо в діапазоні останніх 15 днів
    current_date = datetime.now()
    
    # Перебираємо дні від сьогодні назад
    for i in range(16):
        target_date = current_date - timedelta(days=i)
        start_str = target_date.strftime('%Y-%m-%d')
        end_str = (target_date + timedelta(days=1)).strftime('%Y-%m-%d')
        
        # Шукаємо колекцію за конкретну добу
        collection = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
            .filterBounds(geometry) \
            .filterDate(start_str, end_str) \
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
            
        # Якщо є знімки, беремо найсвіжіший (перший у списку)
        if collection.size().getInfo() > 0:
            # Отримуємо перший знімок з колекції за цей день
            img = collection.first()
            ndvi = img.normalizedDifference(['B8', 'B4']).rename('NDVI')
            stats = ndvi.reduceRegion(reducer=ee.Reducer.mean(), geometry=geometry, scale=10, maxPixels=1e9)
            
            result = stats.getInfo().get('NDVI')
            if result is not None:
                # Повертаємо NDVI та дату знімка для інформації
                return result
                
    return None 

# 4. Основна логіка
if __name__ == "__main__":
    gdf = gpd.read_file(KML_FILE, driver='KML')
    header = sheet.row_values(1)
    field_to_col = {str(name).strip(): i + 1 for i, name in enumerate(header) if name}
    
    row_data = [''] * len(header)
    
    # Дата запису в таблицю
    now = datetime.now()
    row_data[0] = now.strftime("%d.%m.%Y") 
    row_data[1] = now.isocalendar()[1]
    
    for index, row in gdf.iterrows():
        field_name = str(row.get('f_name', '')).strip()
        
        if field_name in field_to_col:
            try:
                print(f"Рахую поле: {field_name}...")
                ee_geom = load_kml_geometry(row.geometry)
                ndvi = get_ndvi(ee_geom)
                
                col_index = field_to_col[field_name] - 1
                if ndvi is not None:
                    row_data[col_index] = f"{ndvi:.3f}"
                
                time.sleep(1)
            except Exception as e:
                print(f"Помилка при обробці поля {field_name}: {e}")
        
    sheet.append_row(row_data)
    print("Дані успішно записано (використано найсвіжіший знімок).")