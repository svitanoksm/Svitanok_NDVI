import xml.etree.ElementTree as ET
import pandas as pd
from shapely.geometry import Polygon

def load_fields(file_path='fields.kml'):
    """
    Зчитує поля з KML-файлу, ігноруючи складну ієрархію fastkml.
    Повертає DataFrame з назвами полів та їх геометрією.
    """
    try:
        # Визначаємо простір імен KML
        ns = {'kml': 'http://www.opengis.net/kml/2.2'}
        
        # Парсимо файл
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        features = []
        
        # Шукаємо всі Placemark у документі
        for placemark in root.findall('.//kml:Placemark', ns):
            # Отримуємо назву поля
            name_elem = placemark.find('kml:name', ns)
            name = name_elem.text if name_elem is not None else "Без назви"
            
            # Отримуємо координати
            coords_elem = placemark.find('.//kml:coordinates', ns)
            if coords_elem is not None:
                coords_str = coords_elem.text.strip()
                
                # Перетворюємо рядок координат у список точок (tuple)
                points = []
                for point in coords_str.split():
                    parts = point.split(',')
                    # Беремо тільки довготу та широту (0-й та 1-й елементи)
                    points.append((float(parts[0]), float(parts[1])))
                
                # Створюємо геометрію Polygon
                geom = Polygon(points)
                features.append({'name': name, 'geometry': geom})
        
        # Повертаємо результат як DataFrame
        df = pd.DataFrame(features)
        print(f"--- Успішно зчитано {len(df)} полів ---")
        return df

    except Exception as e:
        error_msg = f"Помилка зчитування KML: {e}"
        print(error_msg)
        return pd.DataFrame()

# Приклад виклику:
if __name__ == "__main__":
    fields_df = load_fields('test_field.kml') # Вкажіть тут назву вашого файлу
    if not fields_df.empty:
        print(fields_df.head())
