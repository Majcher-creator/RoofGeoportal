"""
Moduł do integracji z Geoportalem (WMTS)
Pobieranie ortofotomap z polskiego Geoportalu
"""

import requests
from io import BytesIO
from PIL import Image, UnidentifiedImageError
import math
from pyproj import Transformer


# URL serwisu WMTS Geoportalu
GEOPORTAL_WMTS_URL = "https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMTS/StandardResolution"
# Alternatywny URL WMS jako fallback
GEOPORTAL_WMS_URL = "https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMS/StandardResolution"
OSM_STATIC_URL = "https://staticmap.openstreetmap.de/staticmap.php"
GOOGLE_STATIC_URL = "https://maps.googleapis.com/maps/api/staticmap"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


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


def geokoduj_adres(adres):
    """
    Zamienia adres na współrzędne GPS (WGS84) przy użyciu Nominatim.
    """
    if not adres:
        return None
    try:
        params = {
            "q": adres,
            "format": "json",
            "limit": 1
        }
        headers = {"User-Agent": "RoofGeoportal/1.0 (contact: support@roofgeoportal.local)"}
        response = requests.get(NOMINATIM_URL, params=params, headers=headers, timeout=10)
        if response.status_code != 200:
            return None
        dane = response.json()
        if not dane:
            return None
        lat = float(dane[0]["lat"])
        lon = float(dane[0]["lon"])
        return lon, lat
    except (requests.RequestException, ValueError, KeyError, IndexError, TypeError):
        return None


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
    # Parametry WMTS zgodne z GetCapabilities Geoportalu
    params = {
        'SERVICE': 'WMTS',
        'REQUEST': 'GetTile',
        'VERSION': '1.0.0',
        'LAYER': 'ORTOFOTOMAPA',
        'STYLE': 'default',
        'FORMAT': 'image/jpeg',
        'TILEMATRIXSET': 'EPSG:2180',
        'TILEMATRIX': f'EPSG:2180:{zoom_level}',
        'TILEROW': str(tile_row),
        'TILECOL': str(tile_col)
    }
    
    try:
        response = requests.get(GEOPORTAL_WMTS_URL, params=params, timeout=10)
        
        if response.status_code == 200:
            # Sprawdź czy odpowiedź to obraz czy XML (błąd)
            content_type = response.headers.get('Content-Type', '')
            
            # Jeśli odpowiedź to XML, to prawdopodobnie błąd WMTS
            if 'xml' in content_type.lower() or response.content[:5] == b'<?xml':
                print(f"Błąd WMTS: otrzymano XML zamiast obrazu")
                if len(response.content) < 1000:
                    print(f"Odpowiedź: {response.content[:500].decode('utf-8', errors='ignore')}")
                return None
            
            # Sprawdź czy to rzeczywiście obraz
            if not (content_type.startswith('image/') or response.content[:2] == b'\xff\xd8'):
                print(f"Błąd: nieprawidłowy format odpowiedzi (Content-Type: {content_type})")
                print(f"Pierwsze bajty: {response.content[:20]}")
                return None
            
            img = Image.open(BytesIO(response.content))
            return img
        else:
            print(f"Błąd pobierania kafelka: HTTP {response.status_code}")
            if response.content:
                print(f"Treść błędu: {response.content[:200].decode('utf-8', errors='ignore')}")
            return None
            
    except Exception as e:
        print(f"Błąd podczas pobierania kafelka: {e}")
        import traceback
        traceback.print_exc()
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
    # Parametry macierzy kafelków dla EPSG:2180 z GetCapabilities Geoportalu
    # TopLeftCorner zgodny z oficjalną specyfikacją WMTS Geoportalu
    # Źródło: https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMTS/StandardResolution?SERVICE=WMTS&REQUEST=GetCapabilities
    origin_x = 0.0
    origin_y = 850000.0
    tile_size = 512  # Geoportal używa kafelków 512x512 dla StandardResolution
    
    # Rozdzielczość dla różnych poziomów zoom (metry na piksel)
    # Źródło: GetCapabilities WMTS Geoportalu, obliczone ze ScaleDenominator × 0.00028
    resolutions = {
        0: 8466.68360,
        1: 4233.34180,
        2: 2116.67090,
        3: 1058.33545,
        4: 529.16773,
        5: 264.58386,
        6: 132.29193,
        7: 66.14597,
        8: 26.45839,
        9: 13.22919,
        10: 6.61460,
        11: 2.64584,
        12: 1.32292,
        13: 0.52917,
        14: 0.26458,
        15: 0.13229
    }
    
    resolution = resolutions.get(zoom_level, 132.29193)  # Default to zoom 6 if not found
    
    # Oblicz indeksy kafelka
    # Origin jest w lewym górnym rogu (top-left), więc:
    # - tile_col rośnie w prawo (na wschód): (x - origin_x)
    # - tile_row rośnie w dół (na południe): (origin_y - y), bo Y rośnie na północ w EPSG:2180
    tile_col = int((x - origin_x) / (tile_size * resolution))
    tile_row = int((origin_y - y) / (tile_size * resolution))
    
    # Oblicz pozycję piksela w kafelku
    pixel_x = int(((x - origin_x) / resolution) % tile_size)
    pixel_y = int(((origin_y - y) / resolution) % tile_size)
    
    # Debug info
    print(f"DEBUG: x={x:.2f}, y={y:.2f}, zoom={zoom_level}")
    print(f"DEBUG: tile_col={tile_col}, tile_row={tile_row}, px=({pixel_x},{pixel_y})")
    
    return tile_col, tile_row, pixel_x, pixel_y


def pobierz_mape_wms(lon, lat, szerokosc_pikseli=800, wysokosc_pikseli=600):
    """
    Pobiera mapę używając WMS jako alternatywa dla WMTS
    
    Args:
        lon: Długość geograficzna (WGS84)
        lat: Szerokość geograficzna (WGS84)
        szerokosc_pikseli: Szerokość obrazu
        wysokosc_pikseli: Wysokość obrazu
        
    Returns:
        PIL.Image lub None
    """
    try:
        # Konwersja do EPSG:2180
        x, y = wgs84_do_epsg2180(lon, lat)
        
        # Oblicz bbox wokół punktu (np. 400m x 300m)
        width_m = 400
        height_m = 300
        
        bbox = f"{x-width_m/2},{y-height_m/2},{x+width_m/2},{y+height_m/2}"
        
        params = {
            'SERVICE': 'WMS',
            'REQUEST': 'GetMap',
            'VERSION': '1.3.0',
            'LAYERS': 'Raster',
            'STYLES': '',
            'CRS': 'EPSG:2180',
            'BBOX': bbox,
            'WIDTH': szerokosc_pikseli,
            'HEIGHT': wysokosc_pikseli,
            'FORMAT': 'image/jpeg'
        }
        
        print(f"Próba WMS: bbox={bbox}")
        response = requests.get(GEOPORTAL_WMS_URL, params=params, timeout=10)
        
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '')
            
            # Sprawdź czy to obraz
            if 'xml' in content_type.lower() or response.content[:5] == b'<?xml':
                print(f"WMS: otrzymano XML zamiast obrazu")
                return None
            
            if not (content_type.startswith('image/') or response.content[:2] == b'\xff\xd8'):
                print(f"WMS: nieprawidłowy format (Content-Type: {content_type})")
                return None
            
            img = Image.open(BytesIO(response.content))
            print(f"WMS: sukces! Rozmiar: {img.size}")
            return img
        else:
            print(f"WMS: błąd HTTP {response.status_code}")
            return None
            
    except Exception as e:
        print(f"WMS: błąd {e}")
        return None


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
    # Najpierw spróbuj WMS (prostsze i bardziej niezawodne)
    print(f"Próba pobrania mapy przez WMS dla lon={lon}, lat={lat}")
    mapa_wms = pobierz_mape_wms(lon, lat, szerokosc_pikseli, wysokosc_pikseli)
    
    if mapa_wms is not None:
        print("WMS: sukces!")
        return mapa_wms
    
    # Fallback na WMTS
    print("WMS nieudane, próba WMTS...")
    
    # Konwersja do EPSG:2180
    x, y = wgs84_do_epsg2180(lon, lat)
    
    # Pobierz kafelek centralny
    tile_col, tile_row, pixel_x, pixel_y = wspolrzedne_do_kafelka(x, y, zoom_level)
    
    # Dla uproszczenia pobierzmy jeden kafelek i wytnijmy fragment
    # W pełnej wersji należałoby złożyć kilka kafelków
    kafelek = pobierz_kafelek_wmts(tile_col, tile_row, zoom_level)
    
    if kafelek is None:
        print("WMTS również nieudane")
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


def pobierz_mape_openstreetmap(lon, lat, szerokosc_pikseli=800, wysokosc_pikseli=600, zoom=18):
    """
    Pobiera statyczną mapę z OpenStreetMap.
    """
    try:
        params = {
            "center": f"{lat},{lon}",
            "zoom": str(zoom),
            "size": f"{szerokosc_pikseli}x{wysokosc_pikseli}",
            "maptype": "mapnik"
        }
        response = requests.get(OSM_STATIC_URL, params=params, timeout=10)
        if response.status_code != 200:
            return None
        content_type = response.headers.get("Content-Type", "")
        if not content_type.startswith("image/"):
            return None
        return Image.open(BytesIO(response.content))
    except (requests.RequestException, UnidentifiedImageError, OSError):
        return None


def pobierz_mape_google(lon, lat, szerokosc_pikseli=800, wysokosc_pikseli=600, zoom=19, api_key=None):
    """
    Pobiera statyczną mapę z Google Maps (wymaga klucza API).
    """
    if not api_key:
        return None
    try:
        params = {
            "center": f"{lat},{lon}",
            "zoom": str(zoom),
            "size": f"{szerokosc_pikseli}x{wysokosc_pikseli}",
            "maptype": "satellite",
            "key": api_key
        }
        response = requests.get(GOOGLE_STATIC_URL, params=params, timeout=10)
        if response.status_code != 200:
            return None
        content_type = response.headers.get("Content-Type", "")
        if not content_type.startswith("image/"):
            return None
        return Image.open(BytesIO(response.content))
    except (requests.RequestException, UnidentifiedImageError, OSError):
        return None


def pobierz_mape_dla_wspolrzednych(
    wspolrzedne_text,
    szerokosc=800,
    wysokosc=600,
    map_source="geoportal",
    google_api_key=None
):
    """
    Parsuje tekst współrzędnych/adres i pobiera mapę z wybranego źródła.
    
    Args:
        wspolrzedne_text: Tekst ze współrzędnymi (np. "52.2297,21.0122" lub adres)
        szerokosc: Szerokość obrazu
        wysokosc: Wysokość obrazu
        map_source: Źródło mapy ("geoportal", "google_maps", "openstreetmap")
        google_api_key: Klucz API Google Maps (opcjonalny)
        
    Returns:
        tuple: (PIL.Image, lon, lat, error_message) lub (None, None, None, error_message)
    """
    try:
        # Spróbuj sparsować jako współrzędne
        parts = wspolrzedne_text.strip().replace(',', ' ').split()
        if len(parts) >= 2:
            lat = float(parts[0])
            lon = float(parts[1])
        else:
            lon = None
            lat = None
    except (ValueError, TypeError):
        lon = None
        lat = None

    if lon is None or lat is None:
        wynik = geokoduj_adres(wspolrzedne_text)
        if not wynik:
            return None, None, None, "Nie udało się rozpoznać adresu lub współrzędnych."
        lon, lat = wynik

    if map_source == "geoportal":
        mapa = pobierz_mape_dla_obszaru(lon, lat, szerokosc, wysokosc)
        if mapa is None:
            return None, lon, lat, "Nie udało się pobrać mapy z Geoportalu."
        return mapa, lon, lat, None

    if map_source == "openstreetmap":
        mapa = pobierz_mape_openstreetmap(lon, lat, szerokosc, wysokosc)
        if mapa is None:
            return None, lon, lat, "Nie udało się pobrać mapy z OpenStreetMap."
        return mapa, lon, lat, None

    if map_source == "google_maps":
        if not google_api_key:
            return None, lon, lat, "Brak klucza API Google Maps."
        mapa = pobierz_mape_google(lon, lat, szerokosc, wysokosc, api_key=google_api_key)
        if mapa is None:
            return None, lon, lat, "Nie udało się pobrać mapy z Google Maps."
        return mapa, lon, lat, None

    return None, lon, lat, "Nieznane źródło mapy."
