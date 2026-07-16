import geopandas as gpd

def load_fields(file_path='fields.kml'):
    try:
        # Зчитуємо KML за допомогою драйвера KML
        fields = gpd.read_file(file_path, driver='KML')
        return fields
    except Exception as e:
        return f"Помилка: {e}"

# Тестовий запуск (виведе інформацію в консоль)
if __name__ == "__main__":
    data = load_fields()
    print(data)
