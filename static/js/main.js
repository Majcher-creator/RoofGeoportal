/**
 * RoofGeoportal - Frontend JavaScript
 * Logika interfejsu użytkownika i interakcji z mapą
 */

// Stałe konfiguracyjne
const CONFIG = {
    canvasWidth: 800,
    canvasHeight: 600,
    punktRadius: 5,
    liniaWidth: 2
};

// Kolory elementów
const KOLORY = {
    punkt: '#667eea',
    linia: '#333',
    kalenica: '#dc3545',
    okap: '#007bff',
    skos: '#28a745',
    kosz: '#ffc107',
    punktAB: '#ff6b6b'
};

// Stan aplikacji
const state = {
    obrazMapy: null,
    punktyDachu: [],
    punktA: null,
    punktB: null,
    trybWyboru: null, // null, 'punkt_a', 'punkt_b'
    wyniki: null
};

// Elementy DOM
const elements = {
    canvas: null,
    ctx: null,
    wspolrzedneInput: null,
    mapSourceSelect: null,
    googleApiKeyInput: null,
    zaladujMapeBtn: null,
    resetujPunktyBtn: null,
    wybierzABtn: null,
    wybierzBBtn: null,
    punktADisplay: null,
    punktBDisplay: null,
    rzeczywistaDlugoscInput: null,
    katNachyleniaInput: null,
    obliczBtn: null,
    resultsSection: null,
    loadingOverlay: null
};

/**
 * Inicjalizacja aplikacji
 */
function init() {
    // Pobierz elementy DOM
    elements.canvas = document.getElementById('mapa-canvas');
    elements.ctx = elements.canvas.getContext('2d');
    elements.wspolrzedneInput = document.getElementById('wspolrzedne-input');
    elements.mapSourceSelect = document.getElementById('map-source-select');
    elements.googleApiKeyInput = document.getElementById('google-api-key-input');
    elements.zaladujMapeBtn = document.getElementById('zaladuj-mape-btn');
    elements.resetujPunktyBtn = document.getElementById('resetuj-punkty-btn');
    elements.wybierzABtn = document.getElementById('wybierz-a-btn');
    elements.wybierzBBtn = document.getElementById('wybierz-b-btn');
    elements.punktADisplay = document.getElementById('punkt-a-display');
    elements.punktBDisplay = document.getElementById('punkt-b-display');
    elements.rzeczywistaDlugoscInput = document.getElementById('rzeczywista-dlugosc-input');
    elements.katNachyleniaInput = document.getElementById('kat-nachylenia-input');
    elements.obliczBtn = document.getElementById('oblicz-btn');
    elements.resultsSection = document.getElementById('results-section');
    elements.loadingOverlay = document.getElementById('loading-overlay');

    // Dodaj event listenery
    elements.zaladujMapeBtn.addEventListener('click', zaladujMape);
    elements.canvas.addEventListener('click', obsluzKlikNaMapie);
    elements.resetujPunktyBtn.addEventListener('click', resetujPunkty);
    elements.wybierzABtn.addEventListener('click', () => ustawTrybWyboru('punkt_a'));
    elements.wybierzBBtn.addEventListener('click', () => ustawTrybWyboru('punkt_b'));
    elements.obliczBtn.addEventListener('click', wykonajObliczenia);
    
    // Dodaj przycisk DEMO
    const demoBtn = document.getElementById('demo-btn');
    if (demoBtn) {
        demoBtn.addEventListener('click', () => {
            elements.wspolrzedneInput.value = 'demo';
            zaladujMape();
        });
    }

    // Obsługa Enter w polu współrzędnych
    elements.wspolrzedneInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            zaladujMape();
        }
    });

    if (elements.mapSourceSelect) {
        elements.mapSourceSelect.addEventListener('change', aktualizujPoleGoogleApi);
        aktualizujPoleGoogleApi();
    }

    console.log('RoofGeoportal zainicjalizowany');
}

/**
 * Ładowanie mapy z Geoportalu
 */
async function zaladujMape() {
    const wspolrzedne = elements.wspolrzedneInput.value.trim();
    const mapSource = elements.mapSourceSelect ? elements.mapSourceSelect.value : 'geoportal';
    const googleApiKey = elements.googleApiKeyInput ? elements.googleApiKeyInput.value.trim() : '';

    if (!wspolrzedne) {
        pokazKomunikat('Wprowadź współrzędne lub adres', 'error');
        return;
    }

    pokazLadowanie(true);

    try {
        const response = await fetch('/api/get_map', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                wspolrzedne: wspolrzedne,
                szerokosc: CONFIG.canvasWidth,
                wysokosc: CONFIG.canvasHeight,
                map_source: mapSource,
                google_api_key: googleApiKey
            })
        });

        const data = await response.json();

        if (data.success) {
            // Załaduj obraz
            const img = new Image();
            img.onload = () => {
                state.obrazMapy = img;
                rysujCanvas();
                if (data.notice) {
                    pokazKomunikat(data.notice, data.notice_level || 'info');
                } else {
                    pokazKomunikat('Mapa załadowana pomyślnie', 'success');
                }
            };
            img.src = 'data:image/png;base64,' + data.image;

            // Wyczyść poprzednie dane
            resetujPunkty();
        } else {
            pokazKomunikat(data.error || 'Błąd ładowania mapy', 'error');
        }
    } catch (error) {
        console.error('Błąd:', error);
        pokazKomunikat('Błąd połączenia z serwerem', 'error');
    } finally {
        pokazLadowanie(false);
    }
}

function aktualizujPoleGoogleApi() {
    if (!elements.googleApiKeyInput || !elements.mapSourceSelect) {
        return;
    }
    const czyGoogle = elements.mapSourceSelect.value === 'google_maps';
    elements.googleApiKeyInput.disabled = !czyGoogle;
    elements.googleApiKeyInput.setAttribute('aria-disabled', (!czyGoogle).toString());
    elements.googleApiKeyInput.placeholder = czyGoogle
        ? 'Wprowadź klucz API Google Maps'
        : 'Klucz Google Maps (tylko dla Google Maps)';
}

/**
 * Obsługa kliknięcia na mapie
 */
function obsluzKlikNaMapie(event) {
    if (!state.obrazMapy) {
        pokazKomunikat('Najpierw załaduj mapę', 'info');
        return;
    }

    const rect = elements.canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    if (state.trybWyboru === 'punkt_a') {
        state.punktA = [x, y];
        elements.punktADisplay.textContent = `(${Math.round(x)}, ${Math.round(y)})`;
        state.trybWyboru = null;
        aktualizujPrzyciskiWyboru();
        pokazKomunikat('Punkt A zaznaczony', 'success');
    } else if (state.trybWyboru === 'punkt_b') {
        state.punktB = [x, y];
        elements.punktBDisplay.textContent = `(${Math.round(x)}, ${Math.round(y)})`;
        state.trybWyboru = null;
        aktualizujPrzyciskiWyboru();
        pokazKomunikat('Punkt B zaznaczony', 'success');
    } else {
        // Dodaj punkt dachu
        state.punktyDachu.push([x, y]);
        pokazKomunikat(`Punkt ${state.punktyDachu.length} zaznaczony`, 'info');
    }

    rysujCanvas();
}

/**
 * Rysowanie na canvas
 */
function rysujCanvas() {
    const ctx = elements.ctx;

    // Wyczyść canvas
    ctx.clearRect(0, 0, CONFIG.canvasWidth, CONFIG.canvasHeight);

    // Rysuj mapę jeśli załadowana
    if (state.obrazMapy) {
        ctx.drawImage(state.obrazMapy, 0, 0, CONFIG.canvasWidth, CONFIG.canvasHeight);
    }

    // Rysuj wielokąt dachu
    if (state.punktyDachu.length > 0) {
        ctx.strokeStyle = KOLORY.linia;
        ctx.lineWidth = CONFIG.liniaWidth;
        ctx.beginPath();
        
        state.punktyDachu.forEach((punkt, i) => {
            if (i === 0) {
                ctx.moveTo(punkt[0], punkt[1]);
            } else {
                ctx.lineTo(punkt[0], punkt[1]);
            }
        });

        if (state.punktyDachu.length > 2) {
            ctx.closePath();
        }
        ctx.stroke();

        // Rysuj punkty dachu
        state.punktyDachu.forEach((punkt, i) => {
            rysujPunkt(punkt[0], punkt[1], KOLORY.punkt, i + 1);
        });
    }

    // Rysuj punkty A i B
    if (state.punktA) {
        rysujPunkt(state.punktA[0], state.punktA[1], KOLORY.punktAB, 'A');
    }
    if (state.punktB) {
        rysujPunkt(state.punktB[0], state.punktB[1], KOLORY.punktAB, 'B');
    }

    // Rysuj linię A-B
    if (state.punktA && state.punktB) {
        ctx.strokeStyle = KOLORY.punktAB;
        ctx.lineWidth = 3;
        ctx.setLineDash([5, 5]);
        ctx.beginPath();
        ctx.moveTo(state.punktA[0], state.punktA[1]);
        ctx.lineTo(state.punktB[0], state.punktB[1]);
        ctx.stroke();
        ctx.setLineDash([]);
    }

    // Rysuj wyniki jeśli są
    if (state.wyniki) {
        rysujWynikiNaMapie();
    }
}

/**
 * Rysowanie punktu na canvasie
 */
function rysujPunkt(x, y, kolor, etykieta) {
    const ctx = elements.ctx;

    // Punkt
    ctx.fillStyle = kolor;
    ctx.beginPath();
    ctx.arc(x, y, CONFIG.punktRadius, 0, 2 * Math.PI);
    ctx.fill();

    // Obramowanie
    ctx.strokeStyle = 'white';
    ctx.lineWidth = 2;
    ctx.stroke();

    // Etykieta
    if (etykieta) {
        ctx.fillStyle = 'white';
        ctx.strokeStyle = kolor;
        ctx.lineWidth = 3;
        ctx.font = 'bold 14px Arial';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        
        const offsetY = -15;
        ctx.strokeText(String(etykieta), x, y + offsetY);
        ctx.fillText(String(etykieta), x, y + offsetY);
    }
}

/**
 * Rysowanie wyników na mapie
 */
function rysujWynikiNaMapie() {
    if (!state.wyniki || !state.wyniki.wymiary) return;

    const ctx = elements.ctx;
    const wymiary = state.wyniki.wymiary;

    // Funkcja pomocnicza do rysowania krawędzi z etykietą
    function rysujKrawedz(krawedz, kolor, etykieta) {
        const [p1, p2] = krawedz.punkty;
        const [sx, sy] = krawedz.srodek;

        // Linia
        ctx.strokeStyle = kolor;
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(p1[0], p1[1]);
        ctx.lineTo(p2[0], p2[1]);
        ctx.stroke();

        // Etykieta z długością
        ctx.fillStyle = 'white';
        ctx.strokeStyle = kolor;
        ctx.lineWidth = 4;
        ctx.font = 'bold 12px Arial';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        
        const tekst = `${etykieta}: ${krawedz.dlugosc}m`;
        ctx.strokeText(tekst, sx, sy);
        ctx.fillText(tekst, sx, sy);
    }

    // Rysuj kalenice
    wymiary.kalenice.forEach((k, i) => {
        rysujKrawedz(k, KOLORY.kalenica, `K${i + 1}`);
    });

    // Rysuj okapy
    wymiary.okapy.forEach((o, i) => {
        rysujKrawedz(o, KOLORY.okap, `O${i + 1}`);
    });

    // Rysuj skosy
    wymiary.skosy.forEach((s, i) => {
        rysujKrawedz(s, KOLORY.skos, `S${i + 1}`);
    });

    // Rysuj kosze
    wymiary.kosze.forEach((k, i) => {
        rysujKrawedz(k, KOLORY.kosz, `KO${i + 1}`);
    });
}

/**
 * Resetowanie punktów
 */
function resetujPunkty() {
    state.punktyDachu = [];
    state.punktA = null;
    state.punktB = null;
    state.trybWyboru = null;
    state.wyniki = null;
    
    elements.punktADisplay.textContent = 'Nie zaznaczono';
    elements.punktBDisplay.textContent = 'Nie zaznaczono';
    elements.resultsSection.style.display = 'none';
    
    aktualizujPrzyciskiWyboru();
    rysujCanvas();
    
    pokazKomunikat('Punkty zresetowane', 'info');
}

/**
 * Ustawianie trybu wyboru punktu A lub B
 */
function ustawTrybWyboru(tryb) {
    state.trybWyboru = tryb;
    aktualizujPrzyciskiWyboru();
    
    const nazwa = tryb === 'punkt_a' ? 'A' : 'B';
    pokazKomunikat(`Kliknij na mapie aby zaznaczyć punkt ${nazwa}`, 'info');
}

/**
 * Aktualizacja wyglądu przycisków wyboru
 */
function aktualizujPrzyciskiWyboru() {
    if (state.trybWyboru === 'punkt_a') {
        elements.wybierzABtn.style.background = '#ff6b6b';
        elements.wybierzBBtn.style.background = '';
    } else if (state.trybWyboru === 'punkt_b') {
        elements.wybierzABtn.style.background = '';
        elements.wybierzBBtn.style.background = '#ff6b6b';
    } else {
        elements.wybierzABtn.style.background = '';
        elements.wybierzBBtn.style.background = '';
    }
}

/**
 * Wykonanie obliczeń
 */
async function wykonajObliczenia() {
    // Walidacja
    if (state.punktyDachu.length < 3) {
        pokazKomunikat('Zaznacz co najmniej 3 punkty dachu', 'error');
        return;
    }

    if (!state.punktA || !state.punktB) {
        pokazKomunikat('Zdefiniuj punkty referencyjne A i B', 'error');
        return;
    }

    const rzeczywistaDlugosc = parseFloat(elements.rzeczywistaDlugoscInput.value);
    if (!rzeczywistaDlugosc || rzeczywistaDlugosc <= 0) {
        pokazKomunikat('Podaj rzeczywistą długość odcinka AB', 'error');
        return;
    }

    const katNachylenia = parseFloat(elements.katNachyleniaInput.value);
    if (isNaN(katNachylenia) || katNachylenia < 0 || katNachylenia > 90) {
        pokazKomunikat('Podaj prawidłowy kąt nachylenia (0-90°)', 'error');
        return;
    }

    pokazLadowanie(true);

    try {
        const response = await fetch('/api/calculate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                punkty_dachu: state.punktyDachu,
                punkt_a: state.punktA,
                punkt_b: state.punktB,
                rzeczywista_dlugosc: rzeczywistaDlugosc,
                kat_nachylenia: katNachylenia
            })
        });

        const data = await response.json();

        if (data.success) {
            state.wyniki = data.wyniki;
            wyswietlWyniki(data.wyniki);
            rysujCanvas();
            pokazKomunikat('Obliczenia wykonane pomyślnie', 'success');
        } else {
            pokazKomunikat(data.error || 'Błąd obliczeń', 'error');
        }
    } catch (error) {
        console.error('Błąd:', error);
        pokazKomunikat('Błąd połączenia z serwerem', 'error');
    } finally {
        pokazLadowanie(false);
    }
}

/**
 * Wyświetlanie wyników w panelu
 */
function wyswietlWyniki(wyniki) {
    // Powierzchnie
    document.getElementById('pole-rzutu').textContent = 
        wyniki.powierzchnie.pole_rzutu + ' m²';
    document.getElementById('pole-rzeczywiste').textContent = 
        wyniki.powierzchnie.pole_rzeczywiste + ' m²';

    // Parametry
    document.getElementById('param-kat').textContent = 
        wyniki.parametry.kat_nachylenia + '°';
    document.getElementById('param-skala').textContent = 
        wyniki.parametry.skala.toFixed(4) + ' m/px';
    document.getElementById('param-punkty').textContent = 
        wyniki.parametry.liczba_punktow;

    // Wymiary elementów
    wyswietlListeWymiarow('kalenice', wyniki.wymiary.kalenice, 'Kalenica');
    wyswietlListeWymiarow('okapy', wyniki.wymiary.okapy, 'Okap');
    wyswietlListeWymiarow('skosy', wyniki.wymiary.skosy, 'Skos');
    wyswietlListeWymiarow('kosze', wyniki.wymiary.kosze, 'Kosz');

    // Pokaż sekcję wyników
    elements.resultsSection.style.display = 'block';
    
    // Przewiń do wyników
    elements.resultsSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

/**
 * Wyświetlanie listy wymiarów dla danego typu elementu
 */
function wyswietlListeWymiarow(typ, lista, nazwa) {
    const element = document.getElementById(`${typ}-lista`);
    
    if (lista.length === 0) {
        element.textContent = 'Brak';
        return;
    }

    element.innerHTML = '';
    
    lista.forEach(item => {
        const div = document.createElement('div');
        div.className = `dimension-item ${typ.slice(0, -1)}`; // usuń 'i' z końca
        div.textContent = `${nazwa} ${item.id}: ${item.dlugosc} m`;
        element.appendChild(div);
    });
}

/**
 * Pokazywanie/ukrywanie overlaya ładowania
 */
function pokazLadowanie(pokaz) {
    elements.loadingOverlay.style.display = pokaz ? 'flex' : 'none';
}

/**
 * Wyświetlanie komunikatu
 */
function pokazKomunikat(tekst, typ = 'info') {
    const container = document.getElementById('message-container');
    
    const message = document.createElement('div');
    message.className = `message ${typ}`;
    message.textContent = tekst;
    
    container.appendChild(message);
    
    // Auto-usuwanie po 5 sekundach
    setTimeout(() => {
        message.style.animation = 'slideIn 0.3s ease reverse';
        setTimeout(() => {
            container.removeChild(message);
        }, 300);
    }, 5000);
}

// Inicjalizacja po załadowaniu DOM
document.addEventListener('DOMContentLoaded', init);
