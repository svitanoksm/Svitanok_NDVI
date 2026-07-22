from datetime import datetime, timedelta
import os
import time
import ee
import geopandas as gpd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 1. Налаштування
SPREADSHEET_NAME = 'NDVI_Svitanok_SM'
SHEET_NAME = 'NDVI'
KML_FILE = 'fields_2026.kml'
PROJECT_ID = 'agro-ndvi-system'


def check_schedule_and_uniqueness():
  today = datetime.now()

  # Перевірка на понеділок (0 — це понеділок у Python)
  if today.weekday() != 0:
    print(f'Сьогодні не понеділок (день тижня: {today.weekday()}). Вихід.')
    return False

  # Перевірка на унікальність запуску за цей тиждень
  year_week = f"{today.isocalendar()[0]}-W{today.isocalendar()[1]}"
  marker_file = '.last_run_week.txt'

  if os.path.exists(marker_file):
    with open(marker_file, 'r') as f:
      last_run = f.read().strip()
    if last_run == year_week:
      print(
          f'Розрахунок за цей тиждень ({year_week}) вже був виконаний раніше.'
          ' Вихід.'
      )
      return False

  print(
      f'Успішна перевірка: сьогодні понеділок, розрахунок за тиждень'
      f' ({year_week}) ще не виконувався.'
  )
  return True


# 2. Ініціалізація з підтримкою автоматичної авторизації
def initialize_ee():
  if 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
    # Авторизація для хмари (GitHub Actions)
    credentials = ee.ServiceAccountCredentials(
        '', key_file=os.environ['GOOGLE_APPLICATION_CREDENTIALS']
    )
    ee.Initialize(credentials=credentials, project=PROJECT_ID)
  else:
    # Авторизація для локального ПК
    ee.Initialize(project=PROJECT_ID)


# 3. Функції для розрахунку
def load_kml_geometry(row_geometry):
  geom = row_geometry
  if geom.geom_type == 'MultiPolygon':
    geom = geom.geoms[0]
  coords = [[p[0], p[1]] for p in geom.exterior.coords]
  return ee.Geometry.Polygon([coords])


def get_ndvi(geometry):
  current_date = datetime.now()

  # Перебираємо дні від сьогодні назад
  for i in range(16):
    target_date = current_date - timedelta(days=i)
    start_str = target_date.strftime('%Y-%m-%d')
    end_str = (target_date + timedelta(days=1)).strftime('%Y-%m-%d')

    collection = (
        ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
        .filterBounds(geometry)
        .filterDate(start_str, end_str)
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
    )

    if collection.size().getInfo() > 0:
      img = collection.first()
      ndvi = img.normalizedDifference(['B8', 'B4']).rename('NDVI')
      stats = ndvi.reduceRegion(
          reducer=ee.Reducer.mean(),
          geometry=geometry,
          scale=10,
          maxPixels=1e9,
      )

      result = stats.getInfo().get('NDVI')
      if result is not None:
        return result

  return None


# 4. Основна логіка
if __name__ == '__main__':
  # Спочатку перевіряємо день тижня та чи був уже запуск цього тижня
  if not check_schedule_and_uniqueness():
    exit(0)

  initialize_ee()

  # Авторизація для Google Sheets
  scope = [
      'https://spreadsheets.google.com/feeds',
      'https://www.googleapis.com/auth/drive',
  ]
  creds = ServiceAccountCredentials.from_json_keyfile_name(
      'credentials.json', scope
  )
  client = gspread.authorize(creds)

  spreadsheet = client.open(SPREADSHEET_NAME)
  sheet = spreadsheet.worksheet(SHEET_NAME)

  gdf = gpd.read_file(KML_FILE, driver='KML')
  header = sheet.row_values(1)
  field_to_col = {
      str(name).strip(): i + 1 for i, name in enumerate(header) if name
  }

  row_data = [''] * len(header)

  now = datetime.now()
  row_data[0] = now.strftime('%d.%m.%Y')
  row_data[1] = now.isocalendar()[1]

  for index, row in gdf.iterrows():
    field_name = str(row.get('f_name', '')).strip()

    if field_name in field_to_col:
      try:
        print(f'Рахую поле: {field_name}...')
        ee_geom = load_kml_geometry(row.geometry)
        ndvi = get_ndvi(ee_geom)

        col_index = field_to_col[field_name] - 1
        if ndvi is not None:
          row_data[col_index] = f'{ndvi:.3f}'

        time.sleep(1)
      except Exception as e:
        print(f'Помилка при обробці поля {field_name}: {e}')

  sheet.append_row(row_data)
  print('Дані успішно записано (використано найсвіжіший знімок).')

  # Зберігаємо мітку про успішний запуск поточного тижня, щоб уникнути повторів
  year_week = f'{now.isocalendar()[0]}-W{now.isocalendar()[1]}'
  with open('.last_run_week.txt', 'w') as f:
    f.write(year_week)
