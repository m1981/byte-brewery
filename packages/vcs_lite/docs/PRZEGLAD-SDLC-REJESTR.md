# Przegląd SDLC — rejestr zmian i działań

Plan i DoD: [PRZEGLAD-SDLC-PILOTAZ.md](PRZEGLAD-SDLC-PILOTAZ.md).

Rejestr obejmuje historię metody oraz wynikające z przeglądu działania. Nie zastępuje Git ani rejestru wymagań produktu. Identyfikatory `PIL-Z-*` i `PIL-U-*` są lokalne dla tego pilotażu i nie należą do korpusu sprawdzanego przez checker ID produktu.

## Historia zmian

| ID | Data | Zmiana | Powód / źródło | Autor | Weryfikacja |
|---|---|---|---|---|---|
| PIL-Z-001 | 2026-10-28 | Utworzenie planu v0.1 i rejestru; trzy przypadki, kryteria, DoD oraz hipotezy korzyści. | Zlecenie użytkownika zapisania projektu przeglądu na podstawie krytycznej oceny SWE-052 i SWE-054. | Agent | Kontrola kompletności dokumentów; wynik kontroli repozytorium w commicie. Pilotaż nie został wykonany. |
| PIL-Z-002 | 2026-10-28 | Akceptacja pilotażu i wykonanie etapu 1; plan v0.2, ustalona baza, zapisane różnice użytkownika, środowisko i SHA-256 źródeł. | Użytkownik: „akceptuje pilotarz wykonaj etap 1 (chyba ze cos przeoczylem)”. | Agent | Bezpośredni odczyt Git, wersji i sum plików; dowody w sekcji wyników planu. Etapy 2–6 niewykonane. |
| PIL-Z-003 | 2026-10-28 | Plan v0.3: wykonany etap 2, mapa źródeł i ról, próba nawigacji trzech zmian, ocena korzyści; otwarte PIL-U-001–004. | Polecenie użytkownika wykonania etapu 2 z uwzględnieniem korzyści. | Agent | Odczyt bazy c19208d i roboczego promptu; sumy źródeł zgodne z etapem 1. Szczegóły i ograniczenia w planie. |
| PIL-Z-004 | 2026-10-28 | Plan v0.4: etap 3 wykonany na bazie c19208d; pełne dowody w experiments, aktualność TRACE i granice checkera. Dodano PIL-U-005. | Użytkownik: „wykonaj 3 rzetelnie”. | Agent | 22 testy bazowe przeszły; różnica TRACE pusta; próba nieaktualnego TRACE: 1 test przeszedł i odtworzył plik w kopii tymczasowej. |
| PIL-Z-005 | 2026-10-29 | Plan v0.5: etap 4, oceny 18 kryteriów, dowody 64 testów i 29 prób. Uzupełniono PIL-U-004; dodano PIL-U-006–007. | Użytkownik potwierdził kontynuację rzetelnego przeglądu po wskazaniu etapu 4. | Agent | 64 testy przeszły; 28/29 prób zgodnych; odtworzona wada etykiety konfliktu. Kod/testy zgodne z bazą i niezmienione. |

| PIL-Z-006 | 2026-10-29 | Etap 5: uporządkowano 7 ustaleń, dobrano 5 małych przyrostów, właścicieli, wyzwalacze i mierzalny odbiór korzyści. Priorytet PIL-U-005 obniżono do niskiego. | Użytkownik: „Wykonaj etap 5 rzetelnie i pamietaj o celu glownym”. | Agent | Zweryfikowano integralność dowodów etapu 4 i powiązanie każdego ustalenia z działaniem/odbiorem. Napraw nie wykonano. |

Każda kolejna zmiana metody lub decyzja o działaniu otrzymuje nowy wiersz: co zmieniono, dlaczego, na czyjej podstawie i jak sprawdzono. Nie usuwamy historii; korekta wskazuje korygowany wpis. SHA zapisujemy dla dowodu lub badanej wersji, nie wymagamy samoodwołania do commita zawierającego dany wpis.

## Ustalenia i działania

Etapy 1–5 mają wyniki w planie. Bieżąca kolejność i kryteria działań: [plan działań etapu 5](#etap-5--plan-działań-po-ocenie-dowodów). Siedem otwartych ustaleń obejmuje dokumentację, kontrolę struktury, lukę regresji notatek i odtworzoną wadę prezentacji konfliktu. Nie wykonano napraw.

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


### PIL-U-005 — sukces generatora nie dowodzi aktualności zapisanego TRACE

- **Metadane:** 2026-10-28, agent; baza c19208dd4ce797ec5183c3127e832c5282a30aba. Właściciel agent, status otwarte, działanie proponowane. Historia: wykryto i odtworzono w etapie 3; bez zmiany generatora.
- **Rodzaj / kryterium:** usprawnienie kontroli dowodów, nie stwierdzone naruszenie REQ-VCS-207. Kryterium pilotażu: odróżnić stan wejściowy od artefaktu naprawionego podczas testu.
- **Dowód:** `test_req_vcs_207_matrix_is_generated` zapisuje plik przed asercją. [Próba](experiments/sdlc-stage3-20261028/pytest-stale-trace-probe.log) celowo nieaktualnego TRACE zakończyła się sukcesem i odtworzeniem pliku; [wynik bazowy](experiments/sdlc-stage3-20261028/result.json) potwierdza, że oryginalny TRACE był aktualny.
- **Oczekiwane / zaobserwowane:** aby deklarować aktualność wersji zapisanej, trzeba porównać ją z wynikiem generatora. Sam dotychczasowy test dopuszcza sukces po samonaprawie.
- **Skutek / priorytet:** średni, wstępny; możliwość uznania nieaktualnego artefaktu za wcześniej zgodny, zwłaszcza przy testowaniu kopii indeksu, której zmian nie przeniesiono do commita.
- **Propozycja / następny krok:** w etapie 5 rozważyć tani warunek porównania TRACE po generacji albo osobny tryb weryfikacji bez zapisu. Zachować możliwość jawnego generowania. Nie zmieniać automatycznie REQ ani testu w ramach tego etapu.
- **Warunek zamknięcia:** po przyjęciu rozwiązania celowo nieaktualna macierz jest jawnie raportowana jako różnica stanu wejściowego (lub powoduje błąd weryfikacji), a aktualna przechodzi bez zmian. Oba wyniki mają SHA, polecenie i log; generowanie nadal możliwe osobno. Przy odrzuceniu propozycji zapisać uzasadnienie i sposób uwzględniania ograniczenia przy deklarowaniu zgodności.
- **Dowód zamknięcia:** brak; dotychczasowa próba potwierdza ograniczenie, nie jego naprawę. Termin/wyzwalacz: ocena usprawnień w etapie 5; nie blokuje etapu 4.

## Uzupełnienia po etapie 4

### PIL-U-004 — dodatkowy dowód z 2026-10-29

Agent sprawdził treść testów, a nie tylko ID. `test_gitlog.py` weryfikuje `details`, lecz nie `commit_totals`; FileList/CommitView mają asercje tekstu, geometrii i przewijania, ale nie kompaktowego odstępu/kolorów. Commity `769b966` i `cbeb5ff` dodające odpowiednio sumy E i kolorowy zapis nie zawierają zmian testów. Nowe [próby audytu](experiments/sdlc-stage4-20261029/probes.json) potwierdziły sumy dla dziewięciu przypadków i podstawowe kolory/odstęp; nie zmienia to pokrycia trwałą regresją. Osobna wada etykiety konfliktu otrzymuje PIL-U-007. Status PIL-U-004 nadal otwarty; następny krok w etapie 5: przygotować spójne uzupełnienie zakresu i dedykowanych regresji, bez ponownego żądania już udzielonych zgód. Warunek zamknięcia rozszerzony: trwałe asercje sum E, kolorów i istotnych błędów odczytu, powiązane z istniejącymi wymaganiami, oraz jawny status oceny B/E/F. Nie uznawać samego raportu audytu za zabezpieczenie kolejnych zmian.

### PIL-U-006 — brak regresji pełnego cyklu notatki

- **Metadane:** 2026-10-29, agent; baza c19208dd4ce797ec5183c3127e832c5282a30aba. Właściciel agent, status otwarte; działanie proponowane. Historia: ustalenie etapu 4, brak wdrożenia naprawy.
- **Rodzaj / kryterium:** luka weryfikacji; REQ-VCS-046, AT-VCS-070, DES-VCS-080 oraz kryteria 4–6 pilotażu.
- **Dowód:** bazowy `tests/ui/test_repo_notes.py` zawiera cztery testy. `test_at_vcs_070_notes_save_switch_and_reopen` wraca do repo w tym samym panelu; nie tworzy nowego panelu ani aplikacji. Test błędu wywołuje `flush`, nie callback WM_DELETE_WINDOW. Timer, FocusOut i kopiowanie nie mają w tych testach asercji wykonania. MANUAL-UI 30 pozostaje otwarte.
- **Oczekiwane / zaobserwowane:** nazwa i powiązanie AT sugerują szerszą ochronę, niż dają asercje. Dodatkowe [próby](experiments/sdlc-stage4-20261029/probes.json) potwierdziły timer, FocusOut, nowy panel odczytujący dysk, stan edycji, kopiowanie i callback zamknięcia przy błędzie. Nie stwierdzono utraty notatek; nie wykonano pełnego restartu aplikacji z odtworzeniem wybranego repo.
- **Skutek / priorytet:** średni; przyszła regresja zapisu/zamykania mogłaby przejść mimo zielonego AT, a ewentualna utrata tekstu miałaby istotny skutek. To ryzyko, nie potwierdzona utrata danych.
- **Propozycja / następny krok:** etap 5 — dobrać minimalny zestaw trwałych regresji: niezależny odczyt po nowym uruchomieniu, zdarzenie/timer, błąd i udane ponowienie zamknięcia. Osobno zachować ręczną ocenę P21; nie utożsamiać geometrii z akceptacją wyglądu. Właściciel prób automatycznych agent; ręcznego odbioru użytkownik po przygotowaniu przez agenta.
- **Warunek zamknięcia:** powtarzalne testy sprawdzają te ścieżki przy ustawieniach i repo tymczasowych, schowku-atrapie; wiążą się z istniejącymi ID. Raport wskazuje wersję, wynik i ograniczenia. Status próby 30 pozostaje jawny nawet jeśli zamknięto samą lukę automatycznej regresji.
- **Decyzja / dowód zamknięcia:** proponowane, bez wdrożenia i bez dowodu zamknięcia. Wyzwalacz: priorytetyzacja w etapie 5.

### PIL-U-007 — konflikt pokazany jak brak danych w kolumnie linii

- **Metadane:** 2026-10-29, agent; baza c19208dd4ce797ec5183c3127e832c5282a30aba. Właściciel agent, status otwarte; działanie proponowane. Historia: odtworzono w etapie 4.
- **Rodzaj / kryterium:** potwierdzona niespójność produktu; REQ-VCS-043 i AT-VCS-065 wymagają słowa „konflikt” dla konfliktu.
- **Dowód:** `ui/widgets.py::draw_compact_counts` dla rodzaju innego niż text wybiera „binarne” lub „—”; `FileList._draw_counts` używa tej funkcji. Próba `renderer_conflict` w [probes.json](experiments/sdlc-stage4-20261029/probes.json): oczekiwane `["konflikt"]`, otrzymane `["—"]`. Bazowy `draw_line_counts` zawierał osobny wariant konfliktu. 64 dobrane testy istniejące przeszły, bo test danych konfliktu nie weryfikuje etykiety Canvas.
- **Oczekiwane / zaobserwowane:** konflikt ma opis odróżniający go od błędu/braku statystyk; obecnie te stany mają tę samą etykietę. Brak dowodu wpływu na samo scalanie lub dane Git.
- **Skutek / priorytet:** średni; myląca informacja w kolumnie, regresja istniejącego zachowania po współdzieleniu renderera. Nie jest to zgłoszenie utraty danych.
- **Propozycja / następny krok:** etap 5 — zaplanować przywrócenie etykiety i minimalną regresję obejmującą wywołanie w FileList oraz zachowanie text/zero/binary/unknown; nie osłabiać wymagania, aby dopasować je do renderera.
- **Warunek zamknięcia:** test pokazuje niepowodzenie dla obecnej bazy i sukces po naprawie: konflikt ma właściwą etykietę, brak danych nadal „—”, zwykłe liczby zachowują kompaktowe kolory. Zachować commit, polecenie i wynik. Próba audytu nie jest jeszcze testem regresji produktu.
- **Decyzja / dowód zamknięcia:** propozycja niezatwierdzona do wdrożenia; brak dowodu zamknięcia. Wyzwalacz: ocena działań etapu 5.

## Etap 5 — plan działań po ocenie dowodów

Ocena agenta z 2026-10-29, na bazie dowodów etapów 2–4 dla `c19208d`. Zlecenie dotyczy oceny i zaplanowania działań, nie ich wdrożenia. Poniższy stan jest bieżący; opisy i priorytety w sekcjach wcześniejszych są historią ustaleń. Wszystkie siedem ustaleń pozostaje otwarte; nie ma jeszcze dowodów zamknięcia. Właścicielem przygotowania, wdrożenia i weryfikacji automatycznej jest agent. Użytkownik ocenia wyłącznie przygotowane próby ręczne i zmiany zakresu, które wymagają jego decyzji; nie przenosimy na niego utrzymania rejestru.

### Kolejność i minimalny zakres

Koszty są szacunkami aktywnej pracy agenta wraz z dobranymi testami i zapisem wyniku, bez oczekiwania na użytkownika. Nie są limitem ani obietnicą terminu. Nie sumujemy osobno kosztu każdego ID, gdy jedna zmiana rozwiązuje kilka ustaleń.

| Kolejność / ustalenia | Konkretne działanie i dotknięte miejsca | Odbiór przyrostu | Koszt / wyzwalacz |
|---|---|---|---|
| 1 — PIL-U-007 | W `widgets.draw_compact_counts` przywrócić etykietę konfliktu. W istniejących testach UI sprawdzić ścieżkę FileList → renderer, a wspólnym testem warianty text/zero/binary/unknown/conflict. Zachować kompaktowy odstęp i kolory. | Asercja „konflikt” oblewa na starej wersji, przechodzi po poprawce; „—” nadal oznacza brak danych. Dobraną regresję liczb B/F uruchomić raz po zmianie. Nie wymaga nowej makiety ani nowego wymagania: przywraca REQ-VCS-043 i AT-VCS-065. | 15–25 min. Pierwszy przyrost po zleceniu realizacji działań. |
| 2 — PIL-U-001–003 | WSPOLPRACA uzgodnić z istniejącym poleceniem o commitach; prompt kierować do reguły zamiast ją kopiować. Usunąć z promptu kopie progów, liczby testów i zakresów ID, zachować praktyczne instrukcje. W SPEC dodać krótki bieżący stan dla trzech badanych zmian i oznaczyć dawną część jako historię. SLOWNIK ma definiować pojęcia; status P21 zastąpić odnośnikiem do stanu bieżącego. Zachować robocze usunięcia użytkownika w prompcie i osobny staging `.gitignore`. | Z promptu można znaleźć właściwy próg, stan i następny krok każdej próby bez czytania kroniki. Reguła commit/push jednoznaczna; odnośniki poprawne; dawne decyzje i pomiary pozostają dostępne. Samo powstanie tabeli nie wystarcza: wykonać próbę nawigacji opisaną niżej. | 25–40 min. Przed kolejnym wznowieniem rozwoju produktu; może być niezależnym przyrostem po naprawie etykiety. |
| 3 — PIL-U-006 | Rozszerzyć `test_repo_notes.py` i integrację startu/zamykania: dwa niezależne uruchomienia z tym samym tymczasowym settings i repo, zapis/odczyt Unicode; osobno timer i FocusOut, błąd zamknięcia i udane ponowienie; istniejące próby kopiowania/pozycji przenieść tylko jeśli chronią zachowanie nieobjęte innym testem. Uściślić nazwę obecnego testu „reopen”, żeby nie obiecywała restartu. | Nowy proces odczytuje zapis bez wspólnego słownika drafts; błąd zapisu utrzymuje okno/tekst, późniejsze zamknięcie zapisuje. Atrapa schowka, izolowane ustawienia, timeout i sprzątanie procesów. Udowodnić, że odłączenie badanego zdarzenia lub ochrony zamknięcia powoduje niepowodzenie odpowiedniej asercji; nie pisać testu sprawdzającego wyłącznie istnienie bindingu. MANUAL-UI 30 pozostaje osobnym odbiorem wyglądu. | 40–65 min. Przed dalszą zmianą zapisu notatek lub deklaracją pełnego odbioru tej funkcji. |
| 4 — PIL-U-004 | W istniejących REQ/DES ująć zakres: B/F liczby pliku, E suma commita; powiązać przyjęte doprecyzowania i P21. W `test_gitlog.py` dodać dedykowane asercje `commit_totals`, a w historii sprawdzić przekazanie sum do E. Uzupełnić krok 29 o B/E/F. Wspólnych testów kolorów z przyrostu 1 nie kopiować do każdej listy. | Oczekiwane sumy wyliczone ręcznie z małych fixture (nie wyłącznie porównanie z drugim parserem produkcyjnym): zwykła zmiana, root, merge według pierwszego rodzica, rename/zero, binary, brak danych po błędzie Git. Asercja sumy E oraz istniejące testy plików F; żaden stan unknown nie udaje +0 −0. Status oceny wizualnej zapisany oddzielnie. | 30–50 min. Po przyroście 1, przed kolejną zmianą liczenia/prezentacji lub deklaracją pełnego odbioru liczników. |
| 5 — PIL-U-005 | W procedurze weryfikacji indeksu dopisać porównanie TRACE przed/po istniejącym generatorze, z jawnym wynikiem. Nie budować nowego parsera ani narzędzia do śledzenia wymagań. Gdy jest różnica, wygenerować TRACE w wersji przeznaczonej do commita, zaktualizować indeks i sprawdzić zmieniony stan. | Aktualny TRACE daje brak różnicy; celowo nieaktualny daje jawny błąd kontroli aktualności, nawet gdy sam pytest jest zielony. Próbę przeprowadzić na kopii, zachować obie wartości i wynik. Generowanie nadal działa. | 10–20 min. Przy najbliższym przyroście zmieniającym wejścia TRACE; można połączyć z weryfikacją przyrostu 3/4. |

Łączny szacunek: **120–200 minut** aktywnej pracy, w małych przyrostach. W razie ograniczonego budżetu pierwsze dwa dają konkretną naprawę i prostsze wznowienie za około 40–65 minut; pozostałe pozostają jawnie otwarte. Nie przekładamy braku czasu na status „gotowe”. Realny koszt zapisać po wykonaniu; powyższe widełki nie są pomiarem.

Przed wdrożeniem porównać właściwe pliki bieżącego HEAD z bazą przeglądu. Jeśli ustalenie zostało już naprawione innym commitem, sprawdzić jego warunek zamknięcia zamiast powtarzać zmianę. Uzgodnionych potrzeb nie zatwierdzać ponownie; nowe decyzje dotyczą tylko rzeczywistej zmiany zakresu. Etap 5 nie zmienia statusu propozycji na „przyjęte do wdrożenia”.

### Priorytety i podstawa oceny

| Ustalenie | Klasyfikacja po etapie 4 | Priorytet | Dlaczego / co pozostaje niepewne |
|---|---|---|---|
| PIL-U-007 | Potwierdzona wada produktu | średni, pierwsza naprawa | Odtworzona błędna etykieta, niewielka poprawka; brak dowodu błędnych operacji Git lub utraty danych. |
| PIL-U-001 | Potwierdzony konflikt instrukcji | średni | Utrudnia samodzielną kontynuację; istniejący cytat rozstrzyga regułę, nie potrzeba nowej decyzji użytkownika. |
| PIL-U-002 | Potwierdzona nieaktualna kopia informacji | średni | Może narzucić zły próg lub mylący stan; usuwać źródło duplikacji, nie tylko podmieniać liczby. |
| PIL-U-003 | Potwierdzony problem bieżącego statusu | średni | Utrudnia wznowienie i sprzyja powtarzaniu pracy; sam przegląd także wymaga krótkiego widoku stanu. |
| PIL-U-006 | Potwierdzona luka trwałej regresji; brak pełnego dowodu restartu/odbioru | średni | Potencjalny skutek utraty notatki istotny, ale próby ochrony zapisu przeszły; nie przedstawiamy ryzyka jako wykrytej utraty danych. |
| PIL-U-004 | Rozproszony zakres i luka dedykowanych regresji | średni | Nowe próby sum i kolorów przeszły, lecz nie chronią kolejnych zmian; nie stwierdzono błędnego sumowania. |
| PIL-U-005 | Ograniczenie kontroli aktualności, usprawnienie | niski (wcześniej średni, wstępny) | Rzeczywisty TRACE był aktualny; etap 3 pokazał tani sposób kontroli. Zmniejszony priorytet względem odtworzonej wady i braków regresji. |

Nie stosowano liczbowego „wyniku ryzyka”: nie mamy danych o częstości zdarzeń ani stratach. Kolejność opiera się na odtwarzalności, skutku, koszcie i zależnościach. Przy rzeczywistym błędzie zapisu/utracie notatki lub błędnej operacji Git priorytet odpowiedniego ustalenia wymaga natychmiastowej ponownej oceny. Tego nie zaobserwowano w pilotażu.

### Jak odbierzemy korzyść, nie samą dokumentację

1. **Powrót do pracy:** po przyroście 2 wystartować od promptu i dla pamięci, notatek oraz liczników wskazać obowiązującą regułę, stan, dowód i następny krok. Cel: 3/3 odpowiedzi bez czytania rozmowy/kroniki, z nie więcej niż dwoma przejściami po odnośnikach do bieżącego stanu; odczyt szczegółowego dowodu liczyć osobno. Zapisać rzeczywisty czas i odczytane sekcje. Nie mamy porównywalnego wcześniejszego pomiaru czasu, więc nie deklarować procentowej oszczędności.
2. **Mniej pomyłek:** poprawka PIL-U-007 ma przejść próbę negatywną → pozytywną; regresje sum/notatek muszą odrzucić celowo odłączoną badaną ścieżkę w kopii testowej. Potwierdzenie „test istnieje” nie jest kryterium sukcesu. Nie wymagać pełnego systemu mutation testing.
3. **Mniej utrzymania:** prompt i słownik mają odsyłać do zmiennych statusów/progów zamiast je kopiować. Przy następnej zmianie progu lub wyniku testu sprawdzić, czy prompt wymaga edycji; cel: nie. SPEC, test i dowód nadal muszą być spójne — nie redukować dokumentacji kosztem kryteriów produktu.
4. **Wiarygodne „gotowe”:** każdy zamykany wpis zawiera wersję, polecenie/metodę, wynik i odnośnik do dowodu. Osobno oznaczyć wdrożenie, testy i odbiór użytkownika. Po zakończeniu regresji nie odhaczać automatycznie kroków ręcznych 29/30.
5. **Nawroty:** przy kolejnym dotknięciu danego obszaru sprawdzić warunek zamknięcia i ewentualny nawrót w tym samym wpisie. Nie wprowadzać cyklicznego raportowania ani nowego rejestru tylko do liczenia usterek.

### Ograniczenie kosztu i zbędnych działań

Nie kopiujemy wszystkich 29 prób audytu do suity; wybieramy brakujące zachowania i używamy istniejących fixture. Nie uruchamiamy całej suity po każdej zmianie dokumentu. Zmiana samej etykiety wymaga testów prezentacji, nie ponownego pomiaru pamięci. Wątek zapisu notatek wymaga integracji cyklu życia, a nie testowania każdego prywatnego pomocnika. Pełny przebieg lub pomiar wydajności rozszerzamy dopiero, gdy zakres zmiany albo wynik wskazuje taką potrzebę.

Nie rozszerzamy checkera na wszystkie pliki, nie tworzymy nowych ID dla samych duplikatów i nie dopisujemy kolejnych dokumentów sterujących. Źródłem działań jest ten rejestr; plan zawiera tylko podsumowanie i odnośnik. Archiwalne dowody są niezmienne; dowód zamknięcia jest nowym zapisem, nie podmianą dawnej porażki. Ewentualny wspólny odbiór UI 29/30 można przygotować w jednym oknie po poprawkach, ale wynik i zakres każdego kroku zapisać osobno.

Hipotezy przyczyn (bez udowodnionego związku przyczynowego): ręczne kopiowanie stanu sprzyja starzeniu promptu; dopisywanie kroniki w miejscu bieżących zadań utrudnia nawigację; współdzielenie renderera bez testu wszystkich stanów sprzyja regresji etykiety. Działania mają zmniejszać te mechanizmy, nie tylko poprawiać pojedynczy tekst. Ich skuteczność pozostaje do sprawdzenia po wdrożeniu.
