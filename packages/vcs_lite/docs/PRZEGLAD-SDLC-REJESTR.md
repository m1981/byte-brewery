# Przegląd SDLC — rejestr zmian i działań

Plan i DoD: [PRZEGLAD-SDLC-PILOTAZ.md](PRZEGLAD-SDLC-PILOTAZ.md).

Rejestr obejmuje historię metody oraz wynikające z przeglądu działania. Nie zastępuje Git ani rejestru wymagań produktu. Identyfikatory `PIL-Z-*` i `PIL-U-*` są lokalne dla tego pilotażu i nie należą do korpusu sprawdzanego przez checker ID produktu.

## Historia zmian

| ID | Data | Zmiana | Powód / źródło | Autor | Weryfikacja |
|---|---|---|---|---|---|
| PIL-Z-001 | 2026-10-28 | Utworzenie planu v0.1 i rejestru; trzy przypadki, kryteria, DoD oraz hipotezy korzyści. | Zlecenie użytkownika zapisania projektu przeglądu na podstawie krytycznej oceny SWE-052 i SWE-054. | Agent | Kontrola kompletności dokumentów; wynik kontroli repozytorium w commicie. Pilotaż nie został wykonany. |

| PIL-Z-002 | 2026-10-28 | Akceptacja pilotażu i wykonanie etapu 1; plan v0.2, ustalona baza, zapisane różnice użytkownika, środowisko i SHA-256 źródeł. | Użytkownik: „akceptuje pilotarz wykonaj etap 1 (chyba ze cos przeoczylem)”. | Agent | Bezpośredni odczyt Git, wersji i sum plików; dowody w sekcji wyników planu. Etapy 2–6 niewykonane. |

| PIL-Z-003 | 2026-10-28 | Plan v0.3: wykonany etap 2, mapa źródeł i ról, próba nawigacji trzech zmian, ocena korzyści; otwarte PIL-U-001–004. | Polecenie użytkownika wykonania etapu 2 z uwzględnieniem korzyści. | Agent | Odczyt bazy c19208d i roboczego promptu; sumy źródeł zgodne z etapem 1. Szczegóły i ograniczenia w planie. |

Każda kolejna zmiana metody lub decyzja o działaniu otrzymuje nowy wiersz: co zmieniono, dlaczego, na czyjej podstawie i jak sprawdzono. Nie usuwamy historii; korekta wskazuje korygowany wpis. SHA zapisujemy dla dowodu lub badanej wersji, nie wymagamy samoodwołania do commita zawierającego dany wpis.

## Ustalenia i działania

Etapy 1–2 mają wyniki w planie. Cztery otwarte ustalenia poniżej wynikają z analizy dokumentów; nie są oceną poprawności implementacji. Nie wykonano napraw.

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

## Ustalenia etapu 2

Wspólne metadane: autor agent, data 2026-10-28, baza `c19208dd4ce797ec5183c3127e832c5282a30aba`; PROMPT-STARTOWY w wariancie roboczym z etapu 1. Priorytety wstępne. Wszystkie wpisy: **status otwarte; działanie proponowane, niezatwierdzone do wdrożenia; właściciel agent**. Wyzwalacz dalszej pracy: ocena w etapie 5 po analizie dowodów; nie blokują etapu 3. Historia każdego wpisu: utworzony w etapie 2, bez naprawy i bez dowodu zamknięcia. „Dowód” poniżej wskazuje dokument bazowy i sekcję; historia Git pozwala odczytać wskazaną wersję.

### PIL-U-001 — sprzeczne instrukcje commitowania

- **Rodzaj / kryterium:** niespójność; jednoznaczne obowiązujące reguły współpracy.
- **Dowód:** WSPOLPRACA, „Bez zmian”: commity i pushe robi użytkownik. PROMPT-STARTOWY, „Zasady pracy”: agent robi commit po logicznym przyroście bez pytania, cytat z 2026-10-26; jednocześnie w liście lektur deklarowane pierwszeństwo WSPOLPRACA. SPEC, Punkt wznowienia 2d, zapisuje to samo późniejsze polecenie użytkownika.
- **Oczekiwane / zaobserwowane:** jedna obowiązująca instrukcja; dwa przeciwne zalecenia, rozstrzygalne dopiero przez odnalezienie późniejszej zgody użytkownika.
- **Skutek / priorytet:** średni; ryzyko zbędnych pytań lub pozostawiania przyrostów bez commita. Push nadal wymaga polecenia — nie rozszerzać zgody na commity.
- **Propozycja / następny krok:** uzgodnić WSPOLPRACA z już udzieloną zgodą, w prompcie zostawić odsyłacz; retrospektywy zachować jako historię. Przygotować minimalną zmianę po etapie 4.
- **Warunek zamknięcia:** oba punkty wejścia prowadzą do tej samej reguły commit/push, z cytatem i zakresem; kontrola nie wymaga nowego uzyskiwania istniejącej zgody. Weryfikacja: odczyt dokumentów po poprawce, zapis SHA i wyniku.

### PIL-U-002 — prompt kopiuje nieaktualne dane i ograniczenia

- **Rodzaj / kryterium:** niespójność; aktualność informacji sterujących pracą.
- **Dowód:** PROMPT-STARTOWY podaje „limit 60 MB”, „Obecnie 650 testów”, zakresy kończące się na DEC-VCS-124, DES-VCS-071 i AT-VCS-063. SPEC: DEC-VCS-134, REQ-VCS-100 wskazują 85 MiB; istnieją DES-VCS-080 i AT-VCS-070. Usunięte przez użytkownika pięć końcowych wierszy nie usuwa tych zapisów.
- **Oczekiwane / zaobserwowane:** prompt kieruje do aktualnego progu i dokumentów; podaje starszy próg i niepełną mapę. Nie zastępujemy liczby 650 nową „aktualną liczbą” bez wyniku na właściwej wersji.
- **Skutek / priorytet:** średni; niewłaściwe kryterium oceny oraz zbędne odczyty i ręczne synchronizacje.
- **Propozycja / następny krok:** zastąpić kopiowany próg i zakresy odnośnikami do REQ oraz źródeł; wynik testów odsyłać do zapisu wersji i wykonania. Zachować użyteczne pułapki techniczne. Przygotować diff z zachowaniem roboczych zmian użytkownika.
- **Warunek zamknięcia:** prompt nie przedstawia historycznego progu/wyniku jako bieżącego; odnalezienie 85 MiB i odrębnych 100 MiB nie wymaga historii rozmowy. Weryfikacja: scenariusz odczytu prompt → REQ, SHA i wynik; sprawdzenie zachowania zmian użytkownika.

### PIL-U-003 — „Punkt wznowienia” jest jednocześnie kroniką i listą zadań

- **Rodzaj / kryterium:** niespójność statusu / usprawnienie; jednoznaczny następny krok.
- **Dowód:** SPEC, Punkt wznowienia: pkt 2c mówi „czeka na krok 19” i „niezatwierdzone w git”; późniejszy pkt 2d potwierdza kroki 18–19 i wykonane commity, lecz pkt 3 ponownie opisuje 2c jako niezatwierdzone. Pkt 15–16 opisują P21 jako propozycję, a osobna sekcja „Notatnik P21 — przyjęte” podaje wdrożenie; krok 30 MANUAL-UI czeka już tylko na próbę wyglądu. Sekcja wdrożenia P21 relacjonuje pomiar starego progu, bez późniejszego wyniku testu dla 85 MiB.
- **Oczekiwane / zaobserwowane:** jedno bieżące zadanie/status z historią obok; konieczność uzgadniania wielu „następnych kroków”. Historycznych wyników i decyzji nie należy usuwać ani poprawiać wstecznie.
- **Skutek / priorytet:** średni; ryzyko powtarzania wykonanych prac, niepotrzebnych pytań i pominięcia rzeczywiście otwartej próby.
- **Propozycja / następny krok:** wydzielić krótką bieżącą tabelę stan–dowód–właściciel–następny krok i jawnie oznaczyć kronikę; uzupełnić status pamięci dopiero po weryfikacji dowodu w etapie 4. Wskazać odsyłacze zamiast kopiowania całych opisów.
- **Warunek zamknięcia:** powtórzona próba nawigacyjna daje aktualny stan i krok dla trzech przypadków bez przeglądania kroniki; zapisane wyniki historyczne pozostają dostępne. Weryfikacja: trzy odpowiedzi z odnośnikami, wersja i liczba koniecznych miejsc odczytu.

### PIL-U-004 — zakres kompaktowych liczników rozproszony między rodzajami zapisów

- **Rodzaj / kryterium:** brak jednoznacznego skonsolidowanego statusu / usprawnienie; zgodność zakresu i statusu.
- **Dowód:** SPEC, DEC-VCS-132 i REQ-VCS-040 dotyczą plików commita; Punkt wznowienia 12–14 dodaje sumę, lewą listę commitów i kompaktowe kolory. SLOWNIK „Liczby zmian” i UI-REFERENCE „P21” opisują wspólny wygląd B/E/F; MANUAL-UI krok 29 nadal skupia się na plikach commita i czeka na ocenę. DES-VCS-079 opisuje statystyki szczegółów commita. To rozproszenie jest potwierdzone; brak implementacji lub brak testów nie został stwierdzony.
- **Oczekiwane / zaobserwowane:** łatwo wskazać przyjęty zakres B/E/F i oddzielny stan weryfikacji; zakres odtwarzamy z kilku sekcji, bez jednego wpisu zamknięcia zmiany.
- **Skutek / priorytet:** średni; ponowne pomylenie sumy commita ze statystyką pliku albo uznanie potwierdzenia jednego obszaru za potwierdzenie wszystkich.
- **Propozycja / następny krok:** etap 4 najpierw sprawdzi istniejące decyzje, testy i akceptacje; dopiero wtedy wskazać wymagane uzupełnienie REQ/DES lub statusu ręcznej weryfikacji. Nie dodawać nowych ID wyłącznie dla wypełnienia tabeli.
- **Warunek zamknięcia:** jeden wskazany zapis zakresu odsyła do B/E/F, właściwych dowodów i jawnych braków; status nie wykracza poza dowód. Weryfikacja: porównanie tego zapisu z decyzjami, testami i ręcznymi wynikami na oznaczonej wersji.
