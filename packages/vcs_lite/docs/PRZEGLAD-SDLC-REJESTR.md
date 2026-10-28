# Przegląd SDLC — rejestr zmian i działań

Plan i DoD: [PRZEGLAD-SDLC-PILOTAZ.md](PRZEGLAD-SDLC-PILOTAZ.md).

Rejestr obejmuje historię metody oraz wynikające z przeglądu działania. Nie zastępuje Git ani rejestru wymagań produktu. Identyfikatory `PIL-Z-*` i `PIL-U-*` są lokalne dla tego pilotażu i nie należą do korpusu sprawdzanego przez checker ID produktu.

## Historia zmian

| ID | Data | Zmiana | Powód / źródło | Autor | Weryfikacja |
|---|---|---|---|---|---|
| PIL-Z-001 | 2026-10-28 | Utworzenie planu v0.1 i rejestru; trzy przypadki, kryteria, DoD oraz hipotezy korzyści. | Zlecenie użytkownika zapisania projektu przeglądu na podstawie krytycznej oceny SWE-052 i SWE-054. | Agent | Kontrola kompletności dokumentów; wynik kontroli repozytorium w commicie. Pilotaż nie został wykonany. |

| PIL-Z-002 | 2026-10-28 | Akceptacja pilotażu i wykonanie etapu 1; plan v0.2, ustalona baza, zapisane różnice użytkownika, środowisko i SHA-256 źródeł. | Użytkownik: „akceptuje pilotarz wykonaj etap 1 (chyba ze cos przeoczylem)”. | Agent | Bezpośredni odczyt Git, wersji i sum plików; dowody w sekcji wyników planu. Etapy 2–6 niewykonane. |

Każda kolejna zmiana metody lub decyzja o działaniu otrzymuje nowy wiersz: co zmieniono, dlaczego, na czyjej podstawie i jak sprawdzono. Nie usuwamy historii; korekta wskazuje korygowany wpis. SHA zapisujemy dla dowodu lub badanej wersji, nie wymagamy samoodwołania do commita zawierającego dany wpis.

## Ustalenia i działania

Etap 1 ma zapis podstawy w planie; nie powstały jeszcze ustalenia o niespójnościach ani działania naprawcze. Wcześniejsze podejrzenia nie są automatycznie potwierdzonymi ustaleniami.

Dla każdego ustalenia dopisać sekcję według poniższego szablonu:

```text
ID: PIL-U-NNN
Data / autor:
Przypadek i badana wersja:
Rodzaj: niespójność / brak dowodu / pytanie / usprawnienie
Kryterium i jego źródło:
Dowód: plik + ID/fragment + commit albo zapis wykonania
Stan oczekiwany i zaobserwowany:
Skutek / ryzyko:
Priorytet: wysoki / średni / niski — uzasadnienie
Proponowane działanie i dotknięte artefakty:
Właściciel:
Następny krok i termin lub wyzwalacz:
Decyzja: proponowane / przyjęte / odrzucone — kto, kiedy, uzasadnienie
Status: otwarte / w realizacji / do weryfikacji / zamknięte / odroczone
Warunek zamknięcia:
Dowód weryfikacji: wersja, metoda, wynik, data, osoba
Historia zmian wpisu:
```

Priorytet wysoki: ryzyko utraty danych, błędnych działań Git lub deklarowania spełnienia kluczowego wymagania bez podstaw. Średni: rozbieżność wpływająca na działanie, weryfikację lub kolejne decyzje. Niski: lokalna wada redakcyjna bez wpływu na interpretację i zachowanie. Priorytet wynika ze skutku, nie z samego braku ID.

Wdrożenie kieruje wpis do weryfikacji. Zamknięcie wymaga dowodu spełnienia warunku; przy odrzuceniu odnotować „zamknięte bez naprawy” i uzasadnienie decyzji. Odroczenie pozostawia właściciela oraz termin lub wyzwalacz powrotu. Przy nawrocie problemu ponownie otworzyć wpis, zachowując wcześniejszy dowód zamknięcia.
