from datetime import datetime, timedelta
import os
import time
import ee
import geopandas as gpd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ==========================
# Налаштування
# ==========================

SPREADSHEET_NAME = 'NDVI_Svitanok_SM'
SHEET_NAME = 'NDVI'
KML_FILE = 'fields_2026.kml'
PROJECT_ID = 'agro-ndvi-system'


# ==========================
# Ініціалізація Earth Engine
# ==========================

def initialize_ee():
    if 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
        credentials = ee.ServiceAccountCredentials(
            '',
            key_file=os.environ['GOOGLE_APPLICATION_CREDENTIALS']
        )
        ee.Initialize(credentials=credentials, project=PROJECT_ID)
    else:
        ee.Initialize(project=PROJECT_ID)


# ==========================
# Перевірка останнього запуску
# ==========================

def check_last_run(sheet):
    values = sheet.col_values(1)

    # Якщо є тільки заголовок
    if len(values) <= 1:
        print("Попередніх запусків немає.")
        return True

    last_date_str = values[-1].strip()

    try:
        last_date = datetime.strptime(last_date_str, "%d.%m.%Y")
    except Exception:
        print(f"Не вдалося прочитати дату '{last_date_str}'. Запускаємо.")
        return True

    next_allowed = last_date + timedelta(days=7)

    if datetime.now() < next_allowed:
        remaining = next_allowed - datetime.now()

        print(
            f"Останній запуск був {last_date.strftime('%d.%m.%Y')}."
        )
        print(
            f"До наступного запуску залишилось приблизно "
            f"{remaining.days} днів."
        )

        return False

    print("Минуло більше 7 днів. Починаємо розрахунок.")
    return True


# ==========================
# Завантаження полігона
# ==========================

def load_kml_geometry(row_geometry):
    geom = row_geometry

    if geom.geom_type == 'MultiPolygon':
        geom = geom.geoms[0]

    coords = [[p[0], p[1]] for p in geom.exterior.coords]

    return ee.Geometry.Polygon([coords])


# ==========================
# Пошук найсвіжішого NDVI
# ==========================

def get_ndvi(geometry):

    current_date = datetime.now()

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

            image = collection.first()

            ndvi = image.normalizedDifference(
                ['B8', 'B4']
            ).rename('NDVI')

            stats = ndvi.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=geometry,
                scale=10,
                maxPixels=1e9,
            )

            value = stats.getInfo().get('NDVI')

            if value is not None:
                return value

    return None


# ==========================
# Основна програма
# ==========================

if __name__ == '__main__':

    initialize_ee()

    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive',
    ]

    creds = ServiceAccountCredentials.from_json_keyfile_name(
        'credentials.json',
        scope
    )

    client = gspread.authorize(creds)

    spreadsheet = client.open(SPREADSHEET_NAME)
    sheet = spreadsheet.worksheet(SHEET_NAME)

    # Перевірка останнього запуску
    if not check_last_run(sheet):
        exit(0)

    gdf = gpd.read_file(KML_FILE, driver='KML')

    header = sheet.row_values(1)

    field_to_col = {
        str(name).strip(): i + 1
        for i, name in enumerate(header)
        if name
    }

    row_data = [''] * len(header)

    now = datetime.now()

    row_data[0] = now.strftime('%d.%m.%Y')
    row_data[1] = now.isocalendar()[1]

    for _, row in gdf.iterrows():

        field_name = str(row.get('f_name', '')).strip()

        if field_name in field_to_col:

            try:

                print(f'Розрахунок поля: {field_name}')

                ee_geom = load_kml_geometry(row.geometry)

                ndvi = get_ndvi(ee_geom)

                col_index = field_to_col[field_name] - 1

                if ndvi is not None:
                    row_data[col_index] = f'{ndvi:.3f}'

                time.sleep(1)

            except Exception as e:

                print(f'Помилка для поля {field_name}: {e}')

    sheet.append_row(row_data)

    print("===================================")
    print("Дані успішно записані.")
    print("Наступний запуск буде можливий через 7 днів.")
    print("===================================")
