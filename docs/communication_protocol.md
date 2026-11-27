# Protokół komunikacji szeregowej (PC <-> Arduino)

## Parametry połączenia
- **Interfejs:** USB / UART
- **Prędkość transmisji (Baudrate):** `9600`
- **Format ramki:** 8N1, kodowanie ASCII, separator końca linii `\n`
- **Opóźnienie startowe po otwarciu portu:** `2.0 s` (czas na restart bootloadera Arduino po sygnale DTR)

## Mapa komunikatów i reakcja sprzętowa

| Stan w Pythonie | Ramka UART | Wyświetlacz OLED/LCD (I2C) | Brzęczyk aktywny | Silnik wibracyjny |
| :--- | :--- | :--- | :--- | :--- |
| `CZUWANIE` | `STANDBY\n` | Komunikat gotowości / OK | Wyłączony (`LOW`) | Wyłączony (`LOW`) |
| `OSTRZEŻENIE` | `WARNING\n` | Alert ostrzegawczy (np. `OBUDZ SIE!`) | Włączony (`HIGH` / puls) | Włączony (`HIGH`) |
| `BRAK TWARZY / BRAK OCENY` | `NO_FACE\n` | Informacja o braku wykrycia kierowcy | Wyłączony (`LOW`) | Wyłączony (`LOW`) |