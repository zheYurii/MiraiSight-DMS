<div align="center">

# 👁️ MiraiSight DMS-AI

**Driver Monitoring System Prototype for Next-Gen ADAS**  
*Od analizy obrazu AI w czasie rzeczywistym do wielozmysłowej reakcji sprzętowej*

[![Version](https://img.shields.io/badge/version-0.1.0--alpha-blue.svg?style=flat-square)](https://github.com/miraisight/miraisight-dms)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.x-5C3EE8.svg?style=flat-square&logo=opencv&logoColor=white)](https://opencv.org/)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-Face_Landmarker-0097A7.svg?style=flat-square&logo=google&logoColor=white)](https://developers.google.com/mediapipe)
[![Arduino](https://img.shields.io/badge/Hardware-Arduino_Uno%2FNano-00979D.svg?style=flat-square&logo=arduino&logoColor=white)](https://www.arduino.cc/)
[![EU GSR Compliant Concept](https://img.shields.io/badge/Regulation-EU_GSR_2024-2EA44F.svg?style=flat-square)](#kontekst-rynkowy-i-regulacyjny)
[![Privacy](https://img.shields.io/badge/Privacy-100%25_Local_Processing-success.svg?style=flat-square)](#prywatność-i-bezpieczeństwo-danych)

---

[**O projekcie**](#-o-projekcie) •
[**Kluczowe funkcjonalności**](#-kluczowe-funkcjonalności) •
[**Architektura systemu**](#️-architektura-systemu) •

</div>

---

## 📖 O projekcie

**MiraiSight DMS-AI** to zintegrowany prototyp systemu monitorowania stanu kierowcy (*Driver Monitoring System – DMS*), będący częścią zaawansowanych systemów wspomagania kierowcy (**ADAS** – *Advanced Driver Assistance Systems*). 

Tradycyjne systemy ostrzegania często ograniczają się do wyświetlenia płaskiego komunikatu na ekranie nawigacji, który łatwo przeoczyć w stanie silnego zmęczenia. **MiraiSight DMS-AI** rozwiązuje ten problem, łącząc komputerową analizę wizyjną w czasie rzeczywistym z fizycznym modułem wykonawczym, który oddziałuje na **trzy zmysły kierowcy jednocześnie**:
1. **Wzrok** – natychmiastowy komunikat ostrzegawczy na dedykowanym wyświetlaczu (symulacja cyfrowych zegarów kokpitu).
2. **Słuch** – przenikliwy sygnał akustyczny generowany przez aktywny brzęczyk.
3. **Dotyk (Haptyka)** – fizyczne wibracje silnika haptycznego symulujące drżenie fotela kierowcy lub wolantu.

### Kontekst rynkowy i regulacyjny
Zgodnie z rozporządzeniem Komisji Europejskiej (**General Safety Regulation – GSR**), od **7 lipca 2024 r.** systemy monitorowania senności i uwagi kierowcy są obowiązkowym wyposażeniem wszystkich nowo homologowanych i rejestrowanych pojazdów w Unii Europejskiej. Repozytorium `miraisight-dms` dostarcza kompletną platformę demonstracyjną łączącą warstwę oprogramowania AI z dedykowanym modułem sprzętowym.

---

## ✨ Kluczowe funkcjonalności

* **Analiza wizyjna w czasie rzeczywistym:** Płynne przechwytywanie strumienia wideo i precyzyjna detekcja punktów charakterystycznych twarzy przy użyciu potoku **OpenCV + MediaPipe**.
* **Inteligentna logika czasowa:** Algorytm analizuje czas trwania zamknięcia powiek, odróżniając naturalne, krótkie mrugnięcia od faktycznego mikro-snu za pomocą konfigurowalnych progów czasowych.
* **Bezpieczna obsługa stanów nieoznaczonych:** Utrata widoczności twarzy w kadrze (np. zasłonięcie kamery, odwrócenie głowy, wyjście poza kadr) nigdy nie jest klasyfikowana jako stan „bezpieczny” – system natychmiast przechodzi w dedykowany stan.
* **Niskoopóźnieniowa komunikacja:** Szybka wymiana ramek stanu pomiędzy jednostką obliczeniową a mikrokontrolerem za pośrednictwem interfejsu szeregowego (`UART / USB`).
* **Synchroniczna reakcja multimodalna:** Pojedyncze zdarzenie przekroczenia progu senności wyzwala w ułamku sekundy zsynchronizowaną reakcję wszystkich trzech wyjść sprzętowych (wyświetlacz I2C, brzęczyk, silnik wibracyjny) oraz automatycznie przywraca stan czuwania po odzyskaniu koncentracji przez kierowcę.
* **Prywatność w fazie projektowania:** Całość przetwarzania obrazu odbywa się w 100% lokalnie w pamięci operacyjnej urządzenia - system domyślnie nie zapisuje ani nie wysyła nagrań wideo do chmury.

---

## 🏗️ Architektura systemu

### Architektura MVP (Host PC + Moduł Wykonawczy Hardware)
W konfiguracji zawartej w tym repozytorium ciężar wnioskowania AI/ML oraz logiki czasowej spoczywa na jednostce centralnej (pełniącej funkcję komputera pokładowego pojazdu). Komunikuje się ona przez port szeregowy z mikrokontrolerem zarządzającym peryferiami wykonawczymi.

```mermaid
flowchart LR
    subgraph Host ["Jednostka Obliczeniowa (Python 3)"]
        CAM["📷 Kamera
(Obraz na żywo)"] --> AI["🧠 AI / ML
(MediaPipe Face Landmarker)"]
        AI --> LOGIC["⏱️ Logika Czasowa
(Stan + Progi Czasowe)"]
    end

    LOGIC == "USB / UART
(pyserial)" ==> MCU["🔌 Mikrokontroler
(Arduino Uno / Nano)"]

    subgraph Cockpit ["Moduł Wykonawczy Kokpitu"]
        MCU --> DISP["🖥️ Wyświetlacz OLED/LCD (I2C)
(Symulacja zegarów)"]
        MCU --> BUZZ["🔊 Brzęczyk aktywny
(Alarm dźwiękowy)"]
        MCU --> VIB["📳 Silnik wibracyjny
(Haptyka fotela)"]
    end
```

---

<div align="center">
  <sub>MiraiSight DMS-AI • Advanced Driver Assistance Systems (ADAS) Prototype</sub>
</div>
