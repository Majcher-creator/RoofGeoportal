"""
Moduł pomocniczych funkcji geometrycznych
"""

import math
import numpy as np


def odleglosc_punkty(p1, p2):
    """
    Oblicza odległość euklidesową między dwoma punktami
    
    Args:
        p1: Punkt (x, y)
        p2: Punkt (x, y)
        
    Returns:
        float: Odległość między punktami
    """
    return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)


def kat_miedzy_liniami(p1, p2, p3):
    """
    Oblicza kąt między dwoma liniami spotykającymi się w p2
    
    Args:
        p1: Pierwszy punkt linii (x, y)
        p2: Punkt wspólny/wierzchołek (x, y)
        p3: Trzeci punkt linii (x, y)
        
    Returns:
        float: Kąt w stopniach (0-360)
    """
    v1 = (p1[0] - p2[0], p1[1] - p2[1])
    v2 = (p3[0] - p2[0], p3[1] - p2[1])
    
    kat1 = math.atan2(v1[1], v1[0])
    kat2 = math.atan2(v2[1], v2[0])
    
    kat = kat2 - kat1
    kat = math.degrees(kat)
    
    # Normalizacja do zakresu 0-360
    if kat < 0:
        kat += 360
        
    return kat


def czy_kat_wklesly(kat):
    """
    Sprawdza czy kąt jest wklęsły (reflex angle)
    
    Args:
        kat: Kąt w stopniach
        
    Returns:
        bool: True jeśli kąt jest wklęsły (> 180°)
    """
    return kat > 180


def pole_wielokata(punkty):
    """
    Oblicza pole powierzchni wielokąta używając wzoru Gaussa (shoelace formula)
    
    Args:
        punkty: Lista punktów [(x1, y1), (x2, y2), ...]
        
    Returns:
        float: Pole powierzchni
    """
    n = len(punkty)
    if n < 3:
        return 0
    
    pole = 0
    for i in range(n):
        j = (i + 1) % n
        pole += punkty[i][0] * punkty[j][1]
        pole -= punkty[j][0] * punkty[i][1]
    
    return abs(pole) / 2


def koryguj_dlugosc_dla_nachylenia(dlugosc_rzutu, kat_nachylenia_stopnie):
    """
    Koryguje długość rzutu o kąt nachylenia dachu
    
    Args:
        dlugosc_rzutu: Długość w rzucie poziomym
        kat_nachylenia_stopnie: Kąt nachylenia w stopniach
        
    Returns:
        float: Rzeczywista długość na nachylonej powierzchni
    """
    kat_rad = math.radians(kat_nachylenia_stopnie)
    if abs(math.cos(kat_rad)) < 0.001:  # Unikaj dzielenia przez zero
        return dlugosc_rzutu
    return dlugosc_rzutu / math.cos(kat_rad)


def koryguj_pole_dla_nachylenia(pole_rzutu, kat_nachylenia_stopnie):
    """
    Koryguje pole rzutu o kąt nachylenia dachu
    
    Args:
        pole_rzutu: Pole w rzucie poziomym
        kat_nachylenia_stopnie: Kąt nachylenia w stopniach
        
    Returns:
        float: Rzeczywiste pole na nachylonej powierzchni
    """
    kat_rad = math.radians(kat_nachylenia_stopnie)
    if abs(math.cos(kat_rad)) < 0.001:  # Unikaj dzielenia przez zero
        return pole_rzutu
    return pole_rzutu / math.cos(kat_rad)


def srodek_linii(p1, p2):
    """
    Oblicza punkt środkowy linii
    
    Args:
        p1: Pierwszy punkt (x, y)
        p2: Drugi punkt (x, y)
        
    Returns:
        tuple: Współrzędne punktu środkowego
    """
    return ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)


def czy_punkty_w_linii(p1, p2, p3, tolerancja=1.0):
    """
    Sprawdza czy trzy punkty leżą w przybliżeniu na jednej linii
    
    Args:
        p1, p2, p3: Punkty (x, y)
        tolerancja: Maksymalna dopuszczalna odległość od linii
        
    Returns:
        bool: True jeśli punkty są współliniowe
    """
    # Oblicz odległość p3 od linii p1-p2
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    
    # Wzór na odległość punktu od linii
    licznik = abs((y2 - y1) * x3 - (x2 - x1) * y3 + x2 * y1 - y2 * x1)
    mianownik = math.sqrt((y2 - y1)**2 + (x2 - x1)**2)
    
    if mianownik < 0.001:
        return False
        
    odleglosc = licznik / mianownik
    return odleglosc < tolerancja
