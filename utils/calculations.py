"""
Moduł do obliczeń geometrycznych związanych z dachem
"""

from utils.geometry import (
    odleglosc_punkty,
    kat_miedzy_liniami,
    czy_kat_wklesly,
    pole_wielokata,
    koryguj_dlugosc_dla_nachylenia,
    koryguj_pole_dla_nachylenia,
    srodek_linii
)


class AnalizatorDachu:
    """
    Klasa do analizy geometrii dachu i identyfikacji jego elementów
    """
    
    def __init__(self, punkty, skala, kat_nachylenia):
        """
        Args:
            punkty: Lista punktów dachu [(x, y), ...]
            skala: Skala w metrach na piksel
            kat_nachylenia: Kąt nachylenia dachu w stopniach
        """
        self.punkty = punkty
        self.skala = skala
        self.kat_nachylenia = kat_nachylenia
        
    def oblicz_krawedzie(self):
        """
        Tworzy listę krawędzi dachu z punktów
        
        Returns:
            list: Lista krawędzi [(p1, p2), ...]
        """
        krawedzie = []
        n = len(self.punkty)
        
        for i in range(n):
            p1 = self.punkty[i]
            p2 = self.punkty[(i + 1) % n]
            krawedzie.append((p1, p2))
            
        return krawedzie
    
    def klasyfikuj_krawedzie(self):
        """
        Klasyfikuje krawędzie jako: kalenice, okapy, skosy, kosze
        
        Returns:
            dict: Słownik z listami krawędzi dla każdego typu
        """
        krawedzie = self.oblicz_krawedzie()
        n = len(self.punkty)
        
        kalenice = []
        okapy = []
        skosy = []
        kosze = []
        
        for i in range(n):
            p_prev = self.punkty[(i - 1) % n]
            p_curr = self.punkty[i]
            p_next = self.punkty[(i + 1) % n]
            
            # Oblicz kąt w wierzchołku
            kat = kat_miedzy_liniami(p_prev, p_curr, p_next)
            
            krawedz = (p_curr, p_next)
            
            # Klasyfikacja na podstawie kąta i pozycji
            # To jest uproszczona heurystyka - w rzeczywistości potrzebna byłaby
            # bardziej zaawansowana analiza topologii dachu
            
            if czy_kat_wklesly(kat):
                # Kąt wklęsły - może być koszem
                kosze.append(krawedz)
            else:
                # Kąt wypukły
                # Heurystyka: krawędzie poziome to okapy/kalenice
                # krawędzie ukośne to skosy
                dx = abs(p_next[0] - p_curr[0])
                dy = abs(p_next[1] - p_curr[1])
                
                if dx > dy * 2:  # Bardziej pozioma
                    # Sprawdź czy to kalenica (wewnątrz) czy okap (na brzegu)
                    # Uproszczenie: górne krawędzie to kalenice, dolne to okapy
                    if p_curr[1] < sum(p[1] for p in self.punkty) / n:
                        kalenice.append(krawedz)
                    else:
                        okapy.append(krawedz)
                else:  # Bardziej pionowa - skos
                    skosy.append(krawedz)
        
        return {
            'kalenice': kalenice,
            'okapy': okapy,
            'skosy': skosy,
            'kosze': kosze
        }
    
    def oblicz_dlugosc_krawedzi(self, krawedz, czy_skos=False):
        """
        Oblicza długość krawędzi w metrach
        
        Args:
            krawedz: Krawędź (p1, p2)
            czy_skos: Czy krawędź jest skosem (wymaga korekty nachylenia)
            
        Returns:
            float: Długość w metrach
        """
        p1, p2 = krawedz
        dlugosc_piksele = odleglosc_punkty(p1, p2)
        dlugosc_metry = dlugosc_piksele * self.skala
        
        if czy_skos:
            dlugosc_metry = koryguj_dlugosc_dla_nachylenia(
                dlugosc_metry, 
                self.kat_nachylenia
            )
            
        return dlugosc_metry
    
    def oblicz_wszystkie_wymiary(self):
        """
        Oblicza wszystkie wymiary dachu
        
        Returns:
            dict: Słownik z wymiarami wszystkich elementów
        """
        klasyfikacja = self.klasyfikuj_krawedzie()
        
        wyniki = {
            'kalenice': [],
            'okapy': [],
            'skosy': [],
            'kosze': []
        }
        
        # Oblicz długości kalenic
        for i, krawedz in enumerate(klasyfikacja['kalenice']):
            dlugosc = self.oblicz_dlugosc_krawedzi(krawedz, czy_skos=False)
            wyniki['kalenice'].append({
                'id': i + 1,
                'dlugosc': round(dlugosc, 2),
                'punkty': krawedz,
                'srodek': srodek_linii(*krawedz)
            })
        
        # Oblicz długości okapów
        for i, krawedz in enumerate(klasyfikacja['okapy']):
            dlugosc = self.oblicz_dlugosc_krawedzi(krawedz, czy_skos=False)
            wyniki['okapy'].append({
                'id': i + 1,
                'dlugosc': round(dlugosc, 2),
                'punkty': krawedz,
                'srodek': srodek_linii(*krawedz)
            })
        
        # Oblicz długości skosów (z uwzględnieniem nachylenia)
        for i, krawedz in enumerate(klasyfikacja['skosy']):
            dlugosc = self.oblicz_dlugosc_krawedzi(krawedz, czy_skos=True)
            wyniki['skosy'].append({
                'id': i + 1,
                'dlugosc': round(dlugosc, 2),
                'punkty': krawedz,
                'srodek': srodek_linii(*krawedz)
            })
        
        # Oblicz długości koszy
        for i, krawedz in enumerate(klasyfikacja['kosze']):
            dlugosc = self.oblicz_dlugosc_krawedzi(krawedz, czy_skos=True)
            wyniki['kosze'].append({
                'id': i + 1,
                'dlugosc': round(dlugosc, 2),
                'punkty': krawedz,
                'srodek': srodek_linii(*krawedz)
            })
        
        return wyniki
    
    def oblicz_powierzchnie(self):
        """
        Oblicza powierzchnię dachu
        
        Returns:
            dict: Słownik z powierzchniami
        """
        # Pole rzutu
        pole_rzutu = pole_wielokata(self.punkty) * (self.skala ** 2)
        
        # Pole rzeczywiste z uwzględnieniem nachylenia
        pole_rzeczywiste = koryguj_pole_dla_nachylenia(
            pole_rzutu,
            self.kat_nachylenia
        )
        
        return {
            'pole_rzutu': round(pole_rzutu, 2),
            'pole_rzeczywiste': round(pole_rzeczywiste, 2)
        }
    
    def analiza_pelna(self):
        """
        Wykonuje pełną analizę dachu
        
        Returns:
            dict: Kompletne wyniki analizy
        """
        wymiary = self.oblicz_wszystkie_wymiary()
        powierzchnie = self.oblicz_powierzchnie()
        
        return {
            'wymiary': wymiary,
            'powierzchnie': powierzchnie,
            'parametry': {
                'kat_nachylenia': self.kat_nachylenia,
                'skala': self.skala,
                'liczba_punktow': len(self.punkty)
            }
        }


def oblicz_skale(punkt_a, punkt_b, rzeczywista_dlugosc):
    """
    Oblicza skalę na podstawie odcinka referencyjnego
    
    Args:
        punkt_a: Pierwszy punkt referencyjny (x, y)
        punkt_b: Drugi punkt referencyjny (x, y)
        rzeczywista_dlugosc: Rzeczywista długość w metrach
        
    Returns:
        float: Skala w metrach na piksel
    """
    dlugosc_piksele = odleglosc_punkty(punkt_a, punkt_b)
    
    if dlugosc_piksele < 1:
        return 0
        
    skala = rzeczywista_dlugosc / dlugosc_piksele
    return skala
