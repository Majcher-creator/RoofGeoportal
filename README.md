# 🏠 RoofGeoportal

Aplikacja webowa do automatycznego pomiaru i kalkulacji parametrów dachów na podstawie zdjęć satelitarnych z polskiego Geoportalu.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 📋 Spis treści

- [Opis projektu](#opis-projektu)
- [Funkcjonalności](#funkcjonalności)
- [Wymagania systemowe](#wymagania-systemowe)
- [Instalacja](#instalacja)
- [Uruchomienie](#uruchomienie)
- [Instrukcja użytkowania](#instrukcja-użytkowania)
- [Struktura projektu](#struktura-projektu)
- [Technologie](#technologie)
- [Licencja](#licencja)

## 📖 Opis projektu

RoofGeoportal to kompleksowe narzędzie umożliwiające:
- Pobieranie ortofotomap wysokiej rozdzielczości z polskiego Geoportalu (WMTS)
- Interaktywne zaznaczanie dachów na mapie satelitarnej
- Automatyczne wykrywanie i klasyfikację elementów dachu (kalenice, okapy, skosy, kosze)
- Obliczanie rzeczywistych wymiarów z uwzględnieniem kąta nachylenia
- Wizualizację wyników na mapie

Aplikacja została stworzona z myślą o dekarżach, architektach, rzeczoznawcach majątkowych oraz wszystkich osobach potrzebujących szybkich i dokładnych pomiarów dachów.

## ✨ Funkcjonalności

### Backend (Python/Flask)
- ✅ Integracja z WMTS Geoportal.gov.pl
- ✅ Konwersja współrzędnych WGS84 ↔ EPSG:2180
- ✅ Pobieranie i łączenie kafelków mapy
- ✅ API REST do komunikacji z frontendem
- ✅ Tryb DEMO z przykładową mapą testową

### Obliczenia geometryczne
- ✅ Kalkulacja skali na podstawie odcinka referencyjnego
- ✅ Automatyczne wykrywanie:
  - **Kalenic** - górne krawędzie dachu
  - **Okapów** - dolne krawędzie
  - **Skosów** - boczne krawędzie
  - **Koszy** - wewnętrzne kąty (doliny)
- ✅ Obliczenia uwzględniające kąt nachylenia dachu
- ✅ Powierzchnia rzeczywista vs. powierzchnia rzutu

### Frontend (HTML/CSS/JavaScript)
- ✅ Intuicyjny interfejs użytkownika
- ✅ Canvas HTML5 do interaktywnego rysowania
- ✅ Wizualizacja wyników z kolorowymi oznaczeniami
- ✅ Responsywny design
- ✅ Komunikaty i walidacja danych

## 💻 Wymagania systemowe

- **Python:** 3.8 lub nowszy
- **System operacyjny:** Linux, macOS, Windows
- **Przeglądarka:** Firefox, Chrome, Edge (najnowsza wersja)
- **Połączenie z internetem** (do pobierania map z Geoportalu)

## 📥 Instalacja

### 1. Sklonuj repozytorium

```bash
git clone https://github.com/Majcher-creator/RoofGeoportal.git
cd RoofGeoportal
```

### 2. Utwórz wirtualne środowisko (opcjonalnie, ale zalecane)

```bash
python -m venv venv

# Linux/macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Zainstaluj zależności

```bash
pip install -r requirements.txt
```

## 🚀 Uruchomienie

### Uruchom aplikację Flask

```bash
python app.py
```

Aplikacja uruchomi się na porcie 5000. Zobaczysz komunikat:

```
============================================================
RoofGeoportal - Aplikacja do pomiaru dachów
============================================================
Uruchamianie serwera...
Otwórz przeglądarkę: http://localhost:5000
Naciśnij Ctrl+C aby zatrzymać serwer
============================================================
```

### Otwórz w przeglądarce

Przejdź do adresu: **http://localhost:5000**

## 📚 Instrukcja użytkowania

### Krok 1: Załaduj mapę

1. W polu "Wprowadź współrzędne GPS" wpisz współrzędne w formacie:
   - `szerokość długość` (np. `52.2297 21.0122`)
   - Separator: spacja lub przecinek
   - Lub wpisz **"demo"** aby załadować mapę testową

2. Kliknij **"Załaduj mapę"** lub **"Tryb DEMO"**

**Przykładowe współrzędne:**
- Warszawa, Plac Zamkowy: `52.2297 21.0122`
- Kraków, Rynek Główny: `50.0619 19.9369`
- Gdańsk, Długi Targ: `54.3487 18.6532`

**Tryb DEMO:**
- Jeśli Geoportal nie jest dostępny lub chcesz przetestować aplikację, użyj przycisku **"Tryb DEMO"**
- Zostanie załadowana przykładowa mapa z testowym budynkiem do pomiarów

### Krok 2: Zdefiniuj skalę

1. Kliknij **"Wybierz na mapie"** przy punkcie A
2. Kliknij na mapie w miejscu początku znanego odcinka (np. krawędź budynku)
3. Kliknij **"Wybierz na mapie"** przy punkcie B
4. Kliknij na mapie w miejscu końca znanego odcinka
5. Wpisz **rzeczywistą długość** odcinka A-B w metrach (np. `15.5`)

**Wskazówka:** Wybierz odcinek, którego długość znasz (np. z mapy zasadniczej, wymiar ściany budynku).

### Krok 3: Zaznacz dach

1. Klikaj kolejno na narożniki dachu (w kolejności wokół obrysu)
2. Zaznacz wszystkie narożniki - aplikacja automatycznie zamknie wielokąt
3. Jeśli pomylisz się, kliknij **"Resetuj punkty"** i zacznij od nowa

### Krok 4: Podaj kąt nachylenia

1. W polu **"Kąt nachylenia dachu"** wpisz kąt w stopniach (np. `30`)
2. Typowe wartości:
   - Dach płaski: 0-5°
   - Dach łagodny: 10-20°
   - Dach standardowy: 25-35°
   - Dach stromy: 40-50°

### Krok 5: Oblicz

1. Kliknij **"Oblicz parametry dachu"**
2. Aplikacja automatycznie:
   - Rozpozna elementy dachu
   - Obliczy wymiary
   - Wyświetli wyniki w tabeli
   - Zaznaczy elementy na mapie kolorami

### Interpretacja wyników

**Kolory elementów na mapie:**
- 🔴 **Czerwony** - Kalenice (górne krawędzie)
- 🔵 **Niebieski** - Okapy (dolne krawędzie)
- 🟢 **Zielony** - Skosy (boczne krawędzie)
- 🟡 **Żółty** - Kosze (wewnętrzne doliny)

**Panel wyników zawiera:**
- Powierzchnię rzutu (widok z góry)
- Powierzchnię rzeczywistą (z uwzględnieniem nachylenia)
- Długości wszystkich elementów dachu
- Parametry pomiaru (skala, kąt, liczba punktów)

## 📁 Struktura projektu

```
RoofGeoportal/
├── app.py                      # Główna aplikacja Flask
├── requirements.txt            # Zależności Python
├── README.md                   # Dokumentacja
├── .gitignore                  # Pliki ignorowane przez Git
│
├── static/                     # Pliki statyczne
│   ├── css/
│   │   └── style.css          # Stylowanie aplikacji
│   ├── js/
│   │   └── main.js            # Logika frontendu
│   └── images/                # Obrazy (ikony, loga)
│
├── templates/                  # Szablony HTML
│   └── index.html             # Strona główna
│
└── utils/                      # Moduły pomocnicze
    ├── geoportal.py           # Integracja z Geoportalem
    ├── calculations.py        # Obliczenia geometryczne
    └── geometry.py            # Funkcje geometrii
```

## 📸 Screenshots

### Interfejs główny
![Interfejs główny RoofGeoportal](https://github.com/user-attachments/assets/acf97e4c-bd0a-4525-a7a1-90e73d86c813)

### Mapa testowa w trybie DEMO
![Tryb DEMO z załadowaną mapą](https://github.com/user-attachments/assets/beb79d7e-0738-44c9-aab6-274cadeb7f36)

### Zaznaczone punkty referencyjne i narożniki dachu
![Zaznaczone punkty na mapie](https://github.com/user-attachments/assets/d0a3bcba-de90-4ff6-a22a-e011d804ac3c)

### Wyniki pomiarów
![Wyniki obliczeń z wizualizacją](https://github.com/user-attachments/assets/a0e45d57-d5ca-44f4-b163-b5af6f14d1e3)

## 🛠 Technologie

### Backend
- **Flask 3.0+** - framework webowy
- **Requests** - komunikacja HTTP z WMTS
- **Pillow (PIL)** - przetwarzanie obrazów
- **NumPy** - obliczenia numeryczne
- **OWSLib** - biblioteka do usług OGC/OWS
- **PyProj** - transformacje układów współrzędnych

### Frontend
- **HTML5 Canvas** - interaktywne rysowanie
- **Vanilla JavaScript** - logika aplikacji (bez frameworków)
- **CSS3** - stylowanie i animacje
- **Fetch API** - komunikacja z backendem

### Źródło danych
- **Geoportal.gov.pl WMTS** - ortofotomapy wysokiej rozdzielczości
- Serwis: https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMTS/StandardResolution

## 🔧 API Endpoints

### `GET /`
Strona główna aplikacji

### `POST /api/get_map`
Pobieranie mapy z Geoportalu

**Request body:**
```json
{
  "wspolrzedne": "52.2297 21.0122",
  "szerokosc": 800,
  "wysokosc": 600
}
```

**Response:**
```json
{
  "success": true,
  "image": "base64_encoded_image",
  "lon": 21.0122,
  "lat": 52.2297
}
```

### `POST /api/calculate`
Obliczanie parametrów dachu

**Request body:**
```json
{
  "punkty_dachu": [[x1, y1], [x2, y2], ...],
  "punkt_a": [xa, ya],
  "punkt_b": [xb, yb],
  "rzeczywista_dlugosc": 15.5,
  "kat_nachylenia": 30
}
```

**Response:**
```json
{
  "success": true,
  "wyniki": {
    "wymiary": {
      "kalenice": [...],
      "okapy": [...],
      "skosy": [...],
      "kosze": [...]
    },
    "powierzchnie": {
      "pole_rzutu": 120.5,
      "pole_rzeczywiste": 139.2
    },
    "parametry": {
      "kat_nachylenia": 30,
      "skala": 0.0194,
      "liczba_punktow": 4
    }
  }
}
```

## 🐛 Rozwiązywanie problemów

### Nie ładuje się mapa
- Sprawdź połączenie z internetem
- Upewnij się, że współrzędne są prawidłowe (zakres dla Polski: 49-55°N, 14-24°E)
- Sprawdź czy serwis Geoportalu jest dostępny

### Błędne wymiary
- Upewnij się, że prawidłowo zaznaczyłeś punkty A i B
- Sprawdź czy rzeczywista długość A-B jest poprawna
- Zweryfikuj kąt nachylenia dachu

### Aplikacja nie startuje
- Sprawdź czy masz zainstalowany Python 3.8+
- Upewnij się, że wszystkie zależności są zainstalowane: `pip install -r requirements.txt`
- Sprawdź czy port 5000 nie jest zajęty przez inną aplikację

## 📄 Licencja

MIT License

Copyright (c) 2024 RoofGeoportal

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## 👨‍💻 Autor

Projekt stworzony dla ułatwienia pracy dekarzy i rzeczoznawców.

## 🙏 Podziękowania

- **Główny Urząd Geodezji i Kartografii** za udostępnienie danych Geoportalu
- Społeczność Open Source za wspaniałe biblioteki

---

**Uwaga:** Dane map pochodzą z Geoportalu i podlegają odpowiednim licencjom. Aplikacja służy wyłącznie do celów informacyjnych i pomiarowych.