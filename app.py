"""
Aplikacja Flask do pomiaru dachów na podstawie ortofotomap z Geoportalu
"""

from flask import Flask, render_template, request, jsonify, send_file
from io import BytesIO
import base64
import json
import os
from PIL import Image

from utils.geoportal import pobierz_mape_dla_wspolrzednych
from utils.calculations import AnalizatorDachu, oblicz_skale


app = Flask(__name__)
app.config['SECRET_KEY'] = 'roof-geoportal-secret-key-2024'
app.config['GOOGLE_MAPS_API_KEY'] = os.environ.get('GOOGLE_MAPS_API_KEY', '')


@app.route('/')
def index():
    """Strona główna aplikacji"""
    return render_template('index.html')


@app.route('/api/get_map', methods=['POST'])
def get_map():
    """
    Endpoint do pobierania mapy z Geoportalu
    
    Oczekiwane dane POST:
        wspolrzedne: współrzędne GPS lub adres
        szerokosc: szerokość obrazu (opcjonalne)
        wysokosc: wysokość obrazu (opcjonalne)
        demo: tryb demonstracyjny (opcjonalne)
        
    Zwraca:
        JSON z obrazem mapy w base64
    """
    try:
        data = request.get_json()
        
        wspolrzedne = data.get('wspolrzedne', '')
        szerokosc = data.get('szerokosc', 800)
        wysokosc = data.get('wysokosc', 600)
        demo_mode = data.get('demo', False)
        map_source = data.get('map_source', 'geoportal')
        google_api_key = data.get('google_api_key') or app.config.get('GOOGLE_MAPS_API_KEY')
        demo_used = False
        notice = None
        notice_level = None
        
        if not wspolrzedne:
            return jsonify({
                'success': False,
                'error': 'Brak współrzędnych'
            }), 400
        
        # Tryb demonstracyjny - użyj przykładowego obrazu
        if demo_mode or wspolrzedne.lower() in ['demo', 'test']:
            demo_image_path = os.path.join('static', 'images', 'demo_map.png')
            if os.path.exists(demo_image_path):
                mapa = Image.open(demo_image_path)
                lon, lat = 21.0122, 52.2297  # Warszawa
                demo_used = True
                notice = 'Załadowano mapę demonstracyjną (tryb DEMO)'
                notice_level = 'info'
            else:
                return jsonify({
                    'success': False,
                    'error': 'Brak pliku demonstracyjnego'
                }), 400
        else:
            # Pobierz mapę z Geoportalu
            mapa, lon, lat, error_message = pobierz_mape_dla_wspolrzednych(
                wspolrzedne,
                szerokosc,
                wysokosc,
                map_source=map_source,
                google_api_key=google_api_key,
                return_error=True
            )
            
            # Jeśli nie udało się pobrać z Geoportalu, użyj trybu demo
            if mapa is None:
                demo_image_path = os.path.join('static', 'images', 'demo_map.png')
                if os.path.exists(demo_image_path):
                    mapa = Image.open(demo_image_path)
                    lon, lat = 21.0122, 52.2297
                    app.logger.warning('Mapa niedostępna - użyto mapy demonstracyjnej')
                    demo_used = True
                    notice = error_message or 'Mapa niedostępna - użyto mapy demonstracyjnej'
                    notice_level = 'warning'
                else:
                    return jsonify({
                        'success': False,
                        'error': error_message or 'Nie udało się pobrać mapy. Sprawdź dane wejściowe.'
                    }), 400
        
        # Konwertuj obraz do base64
        buffer = BytesIO()
        mapa.save(buffer, format='PNG')
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        response = {
            'success': True,
            'image': img_base64,
            'lon': lon,
            'lat': lat,
            'szerokosc': mapa.width,
            'wysokosc': mapa.height,
            'demo': demo_used
        }
        if notice:
            response['notice'] = notice
        if notice_level:
            response['notice_level'] = notice_level

        return jsonify(response)
        
    except Exception as e:
        app.logger.error(f'Błąd w get_map: {str(e)}')
        return jsonify({
            'success': False,
            'error': f'Błąd serwera: {str(e)}'
        }), 500


@app.route('/api/calculate', methods=['POST'])
def calculate():
    """
    Endpoint do obliczania parametrów dachu
    
    Oczekiwane dane POST:
        punkty_dachu: lista punktów [(x, y), ...]
        punkt_a: punkt referencyjny A (x, y)
        punkt_b: punkt referencyjny B (x, y)
        rzeczywista_dlugosc: rzeczywista długość A-B w metrach
        kat_nachylenia: kąt nachylenia dachu w stopniach
        
    Zwraca:
        JSON z wynikami obliczeń
    """
    try:
        data = request.get_json()
        
        # Pobierz dane z requestu
        punkty_dachu = data.get('punkty_dachu', [])
        punkt_a = data.get('punkt_a')
        punkt_b = data.get('punkt_b')
        rzeczywista_dlugosc = data.get('rzeczywista_dlugosc')
        kat_nachylenia = data.get('kat_nachylenia', 0)
        
        # Walidacja danych
        if len(punkty_dachu) < 3:
            return jsonify({
                'success': False,
                'error': 'Zaznacz co najmniej 3 punkty dachu'
            }), 400
        
        if not punkt_a or not punkt_b:
            return jsonify({
                'success': False,
                'error': 'Zdefiniuj punkty referencyjne A i B'
            }), 400
        
        if not rzeczywista_dlugosc or rzeczywista_dlugosc <= 0:
            return jsonify({
                'success': False,
                'error': 'Podaj rzeczywistą długość odcinka AB'
            }), 400
        
        # Konwersja punktów z list na tuple
        punkty_dachu = [tuple(p) for p in punkty_dachu]
        punkt_a = tuple(punkt_a)
        punkt_b = tuple(punkt_b)
        
        # Oblicz skalę
        skala = oblicz_skale(punkt_a, punkt_b, rzeczywista_dlugosc)
        
        if skala <= 0:
            return jsonify({
                'success': False,
                'error': 'Błąd obliczania skali - punkty A i B są zbyt blisko'
            }), 400
        
        # Utwórz analizator dachu
        analizator = AnalizatorDachu(
            punkty=punkty_dachu,
            skala=skala,
            kat_nachylenia=kat_nachylenia
        )
        
        # Wykonaj pełną analizę
        wyniki = analizator.analiza_pelna()
        
        return jsonify({
            'success': True,
            'wyniki': wyniki
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Błąd obliczeń: {str(e)}'
        }), 500


@app.route('/api/health', methods=['GET'])
def health():
    """Endpoint do sprawdzania statusu aplikacji"""
    return jsonify({
        'status': 'ok',
        'message': 'RoofGeoportal API działa poprawnie'
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    
    print("=" * 60)
    print("RoofGeoportal - Aplikacja do pomiaru dachów")
    print("=" * 60)
    print("Uruchamianie serwera...")
    print(f"Otwórz przeglądarkę: http://localhost:{port}")
    print("Naciśnij Ctrl+C aby zatrzymać serwer")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=port)
