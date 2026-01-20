"""
Moduł do integracji z Geoportalem (WMTS)
Pobieranie ortofotomap z polskiego Geoportalu
"""

import requests
from io import BytesIO
from PIL import Image
import math
from pyproj import Transformer


# URL serwisu WMTS Geoportalu
GEOPORTAL_WMTS_URL = "https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMTS/StandardResolution"


def wgs84_do_epsg2180(lon, lat):
    """
    Konwertuje współrzędne WGS84 (GPS) do układu EPSG:2180 (PUWG 1992)
    
    Args:
        lon: Długość geograficzna (WGS84)
        lat: Szerokość geograficzna (WGS84)
        
    Returns:
        tuple: (x, y) w układzie EPSG:2180
    """
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:2180", always_xy=True)
    x, y = transformer.transform(lon, lat)
    return x, y


def epsg2180_do_wgs84(x, y):
    """
    Konwertuje współrzędne EPSG:2180 do WGS84
    
    Args:
        x: Współrzędna X (EPSG:2180)
        y: Współrzędna Y (EPSG:2180)
        
    Returns:
        tuple: (lon, lat) w WGS84
    """
    transformer = Transformer.from_crs("EPSG:2180", "EPSG:4326", always_xy=True)
    lon, lat = transformer.transform(x, y)
    return lon, lat


def pobierz_kafelek_wmts(tile_col, tile_row, zoom_level=14):
    """
    Pobiera pojedynczy kafelek z serwisu WMTS Geoportalu
    
    Args:
        tile_col: Kolumna kafelka
        tile_row: Wiersz kafelka
        zoom_level: Poziom powiększenia (domyślnie 14)
        
    Returns:
        PIL.Image lub None jeśli błąd
    """
    # Parametry WMTS
    params = {
        'SERVICE': 'WMTS',
        'REQUEST': 'GetTile',
        'VERSION': '1.0.0',
        'LAYER': 'ORTOFOTOMAPA',
        'STYLE': 'default',
        'FORMAT': 'image/jpeg',
        'TILEMATRIXSET': 'EPSG:2180',
        'TILEMATRIX': f'EPSG:2180:{zoom_level}',
        'TILEROW': tile_row,
        'TILECOL': tile_col
    }
    
    try:
        response = requests.get(GEOPORTAL_WMTS_URL, params=params, timeout=10)
        
        if response.status_code == 200:
            img = Image.open(BytesIO(response.content))
            return img
        else:
            print(f"Błąd pobierania kafelka: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"Błąd podczas pobierania kafelka: {e}")
        return None


def wspolrzedne_do_kafelka(x, y, zoom_level=14):
    """
    Konwertuje współrzędne EPSG:2180 na indeksy kafelka WMTS
    
    Args:
        x: Współrzędna X (EPSG:2180)
        y: Współrzędna Y (EPSG:2180)
        zoom_level: Poziom powiększenia
        
    Returns:
        tuple: (tile_col, tile_row, pixel_x, pixel_y)
    """
    # Parametry macierzy kafelków dla EPSG:2180
    # Uproszczone - w rzeczywistości należy pobrać z GetCapabilities
    origin_x = -5713134.0
    origin_y = 8693134.0
    tile_size = 256
    
    # Rozdzielczość dla różnych poziomów zoom (metry na piksel)
    resolutions = {
        10: 1587.50317,
        11: 793.75158,
        12: 529.16772,
        13: 264.58386,
        14: 132.29193,
        15: 66.14596,
        16: 26.45839,
        17: 13.22919,
        18: 6.61460
    }
    
    resolution = resolutions.get(zoom_level, 132.29193)
    
    # Oblicz indeksy kafelka
    tile_col = int((x - origin_x) / (tile_size * resolution))
    tile_row = int((origin_y - y) / (tile_size * resolution))
    
    # Oblicz pozycję piksela w kafelku
    pixel_x = int(((x - origin_x) / resolution) % tile_size)
    pixel_y = int(((origin_y - y) / resolution) % tile_size)
    
    return tile_col, tile_row, pixel_x, pixel_y


def pobierz_mape_dla_obszaru(lon, lat, szerokosc_pikseli=800, wysokosc_pikseli=600, zoom_level=14):
    """
    Pobiera ortofotomapę dla danego obszaru
    
    Args:
        lon: Długość geograficzna (WGS84)
        lat: Szerokość geograficzna (WGS84)
        szerokosc_pikseli: Szerokość obrazu wynikowego
        wysokosc_pikseli: Wysokość obrazu wynikowego
        zoom_level: Poziom powiększenia
        
    Returns:
        PIL.Image lub None
    """
    # Konwersja do EPSG:2180
    x, y = wgs84_do_epsg2180(lon, lat)
    
    # Pobierz kafelek centralny
    tile_col, tile_row, pixel_x, pixel_y = wspolrzedne_do_kafelka(x, y, zoom_level)
    
    # Dla uproszczenia pobierzmy jeden kafelek i wytnijmy fragment
    # W pełnej wersji należałoby złożyć kilka kafelków
    kafelek = pobierz_kafelek_wmts(tile_col, tile_row, zoom_level)
    
    if kafelek is None:
        return None
    
    # Wytnij i przeskaluj do żądanego rozmiaru
    # Centrowanie na wybranym punkcie
    tile_size = 256
    
    # Oblicz obszar do wycięcia (centrowany na punkcie)
    left = max(0, pixel_x - szerokosc_pikseli // 2)
    top = max(0, pixel_y - wysokosc_pikseli // 2)
    right = min(tile_size, left + szerokosc_pikseli)
    bottom = min(tile_size, top + wysokosc_pikseli)
    
    # Jeśli obszar wychodzi poza kafelek, trzeba pobrać dodatkowe kafelki
    # Dla uproszczenia zwracamy to co mamy
    if right - left < szerokosc_pikseli or bottom - top < wysokosc_pikseli:
        # Potrzebujemy więcej kafelków - złóż z 2x2
        return pobierz_mape_2x2(tile_col, tile_row, zoom_level, 
                               pixel_x, pixel_y, szerokosc_pikseli, wysokosc_pikseli)
    
    fragment = kafelek.crop((left, top, right, bottom))
    return fragment


def pobierz_mape_2x2(tile_col, tile_row, zoom_level, center_x, center_y, width, height):
    """
    Pobiera i składa 4 kafelki (2x2) aby pokryć większy obszar
    """
    tile_size = 256
    
    # Pobierz 4 kafelki
    tiles = []
    for dy in range(2):
        row = []
        for dx in range(2):
            tile = pobierz_kafelek_wmts(tile_col + dx, tile_row + dy, zoom_level)
            if tile:
                row.append(tile)
            else:
                # Stwórz pusty kafelek jeśli pobieranie się nie powiodło
                row.append(Image.new('RGB', (tile_size, tile_size), color='gray'))
        tiles.append(row)
    
    # Złóż kafelki w jeden obraz
    combined = Image.new('RGB', (tile_size * 2, tile_size * 2))
    for y, row in enumerate(tiles):
        for x, tile in enumerate(row):
            combined.paste(tile, (x * tile_size, y * tile_size))
    
    # Wytnij żądany obszar wokół punktu centralnego
    left = max(0, center_x - width // 2)
    top = max(0, center_y - height // 2)
    right = min(tile_size * 2, left + width)
    bottom = min(tile_size * 2, top + height)
    
    result = combined.crop((left, top, right, bottom))
    
    # Jeśli wycięty obszar jest mniejszy niż żądany, dopasuj
    if result.size != (width, height):
        result = result.resize((width, height), Image.Resampling.LANCZOS)
    
    return result


def pobierz_mape_dla_wspolrzednych(wspolrzedne_text, szerokosc=800, wysokosc=600):
    """
    Parsuje tekst współrzędnych i pobiera mapę
    
    Args:
        wspolrzedne_text: Tekst ze współrzędnymi (np. "52.2297,21.0122" lub adres)
        szerokosc: Szerokość obrazu
        wysokosc: Wysokość obrazu
        
    Returns:
        tuple: (PIL.Image, lon, lat) lub (None, None, None)
    """
    try:
        # Spróbuj sparsować jako współrzędne
        parts = wspolrzedne_text.strip().replace(',', ' ').split()
        if len(parts) >= 2:
            lat = float(parts[0])
            lon = float(parts[1])
            
            mapa = pobierz_mape_dla_obszaru(lon, lat, szerokosc, wysokosc)
            return mapa, lon, lat
    except:
        pass
    
    # Jeśli nie udało się sparsować jako współrzędne, 
    # można tu dodać geokodowanie adresu (wymaga dodatkowej usługi)
    # Na razie zwróćmy None
    return None, None, None
