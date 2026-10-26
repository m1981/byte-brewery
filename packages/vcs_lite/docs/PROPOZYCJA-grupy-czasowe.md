# vcs-lite — grupy plików według czasu ostatniego zapisu

Status 2026-10-26: pilotaż odczytowy wykonany; kierunek grupowania przyjęty (DEC-VCS-126, Q-VCS-065): „d1 tak, pokaz makiete”. Linie P18 ocenione pozytywnie; uproszczenie etykiet w [P19](ui-mockups/p19-etykiety-czasu.html) do wyboru (Q-VCS-066). P17 — sortowanie i kolumna +/− — zaakceptowane osobno (DEC-VCS-125), przed wdrożeniem. Użytkownik: „D1 jest super a widziales jakies wzorce jak mozna by grupowac pliki zmienione w podobnym czasie przez agenta. Jak chcesz mozesz zrobic pilotaz pomiarowy w w tym repo i ../doc oraz ../iso-template-engine”. Lokalizacje potwierdzone: „Tak, docs i iso-template-agent”.

## Wzorce i ich zastosowanie

Źródła sprawdzone 2026-10-26:

| Wzorzec | Co robi | Wniosek dla vcs-lite (propozycja agenta) |
|---|---|---|
| [JetBrains Local History](https://www.jetbrains.com/help/pycharm/local-history.html) | Historia zapisów dla pliku, folderu lub projektu; zmiany z IDE i spoza niego, etykiety zdarzeń. | Zakres czasu jest zrozumiałą etykietą grupy. Pełna historia wymaga rejestrowania zdarzeń. |
| [JetBrains Changelists](https://www.jetbrains.com/help/pycharm/managing-changelists.html) | Nazwane grupy zmian związanych z zadaniami; aktywna lista zbiera nowe zmiany, użytkownik może je przenosić. | Przynależność do zadania jest odrębną informacją od czasu zapisu. |
| [VS Code Local History, opis wprowadzenia w 1.66](https://code.visualstudio.com/updates/v1_66#_local-history) | Historia pliku; `workbench.localHistory.mergeWindow` ogranicza liczbę wpisów przez łączenie bliskich zapisów. | Próg czasu może ograniczać szum, ale to przykład dla zapisów jednego pliku, nie gotowe grupowanie plików agenta. |
| [Apache Beam session windows](https://beam.apache.org/documentation/programming-guide/#session-windows) | Grupy zdarzeń rozdzielane przerwą bez aktywności. | Wzorzec algorytmu: przerwa między sąsiednimi zapisami zamiast sztywnych przedziałów zegara. Nie jest to wzorzec interfejsu Git. |

Żadne z tych źródeł nie potwierdza rozpoznawania autora niezatwierdzonych zmian na podstawie `mtime`. Do etykiety „agent / zadanie” potrzebne byłyby jawne identyfikatory sesji i zapis ścieżek zmienionych przez tę sesję. Dwa równoległe zadania mogą zapisywać w tym samym czasie, a jeden plik może zawierać zmiany kilku zadań.

## Metoda

Jednorazowy odczyt 2026-10-26 o 21:35:53 CET, przed dopisaniem wyników pilotażu do repo. Repozytoria: `~/PycharmProjects/byte-brewery` (root bieżącego pakietu), `~/PycharmProjects/docs`, `~/PycharmProjects/iso-template-agent`.

1. `GitCli` w trybie `read_only=True`, `git status --porcelain=v2 -z --branch --untracked-files=all`. Ten tryb wyłącza opcjonalne blokady Git.
2. Unikalne ścieżki z statusu i `lstat().st_mtime_ns` — czas samego dowiązania dla symlinków. Bez odczytu zawartości plików, diffów i logów rozmów. Kontrola SHA-256 indeksu przed i po odczycie.
3. Malejący czas, przy remisie ścieżka. Nowa grupa, gdy przerwa między sąsiadami jest **większa** od progu; równa progowi pozostaje razem. Porównanie progów 30 s, 1, 2, 5, 10, 15 min. Osobno symulacja grup w granicach statusów Git oraz dodatkowego limitu rozpiętości grupy 15 min.
4. Pliki bez czasu wyłączone z grup czasowych i policzone osobno (w tej próbce: 0). Snapshot nie jest atomowy: inny proces może pisać podczas odczytu.

Skrypt do powtórzenia: [tools/measure_change_groups.py](../tools/measure_change_groups.py). Przykład z katalogu pakietu:

```sh
../../.venv/bin/python tools/measure_change_groups.py --output /tmp/vcs-time-new.json ../.. ~/PycharmProjects/docs ~/PycharmProjects/iso-template-agent
```

Skrypt tworzy nowy plik wynikowy, odmawia nadpisania istniejącego. Zarchiwizowane [wyniki zbiorcze](experiments/time-groups-20261026/results.json) nie zawierają pełnej listy ścieżek z innych repozytoriów. Surowy snapshot pozostał w scratchpadzie pilotażu (`/private/tmp/vcs-lite-time-pilot/snapshot.json`).

## Wyniki

Liczby poniżej to grupy całego repo, niezależnie od statusu Git; każdy plik liczony raz.

| Repo | Pliki | 30 s | 1 min | 2 min | 5 min | 10 min | 15 min |
|---|---:|---:|---:|---:|---:|---:|---:|
| byte-brewery | 2 | 2 | 2 | 2 | 2 | 2 | 2 |
| docs | 394 | 9 | 8 | 8 | 8 | 8 | 8 |
| iso-template-agent | 21 | 7 | 7 | 5 | 4 | 4 | 3 |

`iso-template-agent`, próg 5 min, godziny Europe/Warsaw:

| Ostatnie zapisy | Pliki | Lokalizacja |
|---|---:|---|
| 26.10, 21:14:06 | 3 | `reference/process-map` i `reference/process-simulator` |
| 26.10, 20:57:54–21:02:03 | 6 | `reference/process-map`, dokumenty acceptance i evidence |
| 23.10, 11:33:54–11:35:01 | 11 | `reference/repository-evolution` |
| 19.10, 00:17:59 | 1 | dokument w katalogu głównym |

Próg 15 min łączy dwie najnowsze serie w jedną o rozpiętości 16,2 min. Nie znamy przypisania plików do zadań, więc nie jest to dowód, że połączenie byłoby błędne. Przy 5 min dodatkowy limit rozpiętości 15 min nie zmienił wyniku w żadnym repo.

Po zachowaniu podziału statusów Git `iso-template-agent` ma **7 sekcji czasowych**: 1 w Staged, 2 w Changes i 4 w Unversioned. To inne pytanie niż liczba 4 grup całego repo. `byte-brewery` ma 2 sekcje, `docs` ma 8. Proponowany interfejs zachowuje statusy Git.

W `docs` 348 z 394 plików leży w jednym katalogu eksportu `chatgpt-…` i ma czasy w przedziale ok. 16 s. Wniosek z nazw i metadanych: prawdopodobna paczka importu/eksportu; sam pilotaż nie obserwował jej powstania. Ten przykład pokazuje, dlaczego bliskość czasu nie oznacza zadania agenta. W bieżącym repo są tylko 2 zmienione pliki — za mało do oceny sensowności grupowania.

| Repo | Git status | Odczyty metadanych i przygotowanie rekordów | Grupowanie, 6 progów |
|---|---:|---:|---:|
| byte-brewery | 22,13 ms | 1,65 ms | 0,04 ms |
| docs | 108,74 ms | 314,28 ms | 1,07 ms |
| iso-template-agent | 18,21 ms | 15,13 ms | 0,08 ms |

To pojedynczy pomiar, nie benchmark ani wynik odświeżania UI. Największy koszt to odczyty metadanych. Indeksy wszystkich 3 repo miały identyczne sumy przed i po. Pilotaż nie uruchamiał zapisujących poleceń Git ani nie zmieniał badanych plików.

## Rekomendacja D1 — przyjęta, DEC-VCS-126

Rozwinąć P17 o **delikatne separatory czasu wewnątrz obecnych grup Git**, domyślnie rozwinięte. Początkowy próg: przerwa większa niż 5 min. Nagłówek np. „26.10 · 20:58–21:02 · 4 pliki”; w podpowiedzi dokładne sekundy i reguła podziału. Nie nazywać grup zadaniami ani agentami. Przy jednym pliku nagłówek pokazuje pojedynczy czas. Brak czasu: ostatnia sekcja „Czas nieznany”. Kolumna +/− pozostaje przy plikach według zaakceptowanego P17, bez sumy sugerującej diff tylko z danego okresu.

Próg 5 min to kandydat do próby użytkowej, nie wynik optymalizacji: próbka nie ma oznaczonych prawdziwych sesji. Żeby uniknąć wielogodzinnych grup połączonych łańcuchem krótkich przerw, proponowany dodatkowy limit rozpiętości wynosi 15 min, liczony od najnowszego pliku grupy. Separator niczego nie stage'uje ani nie zmienia wyboru plików. Obliczenia przy dotychczasowym odświeżeniu; bez ciągłego obserwatora.

Dlaczego: pomaga przeglądać serie zapisów, zachowując rozróżnienie Staged / Changes / Unversioned. Jeśli nie: wdrożyć samo zaakceptowane P17. Interaktywny podgląd wyników porównuje progi i podział statusów; nie zastępuje makiety finalnego wyglądu separatorów. Makieta P18 w stylu P17 jest przygotowana. Po akceptacji wyglądu: REQ/DES/AT i TDD.

Ograniczenia do uwzględnienia w specyfikacji: `mtime` przechowuje tylko ostatni zapis, kolejna edycja przenosi cały plik; checkout, kopiowanie i narzędzia mogą zmieniać lub zachować dawne czasy; Staged używa czasu pliku roboczego, nie czasu stage. Usunięte pliki zwykle nie mają `mtime`. Pełna kolumna +/− opisuje bieżący diff, a nie zmiany w danej serii zapisów.

## P19 — mniej informacji w separatorach (do wyboru, Q-VCS-066)

Użytkownik po obejrzeniu P18: „Same sekcje z ta linia sa super ale Jakos duzo szumu tutaj” oraz „Moze pokazujmy zamiast tych dat i czasu po porsut x min ago, x h ago”. Linie i podział zachowujemy; proponowane etykiety zmienia [P19](ui-mockups/p19-etykiety-czasu.html). To własne warianty projektowe agenta, nie wyniki dodatkowego badania wzorców.

| Wariant | Etykiety i układ | Ocena agenta |
|---|---|---|
| **Czas względny — rekomendacja** | „5 min temu”, „2 h temu”; linia za tekstem jak w P18. Liczba plików tylko przy statusie Git i w dymku separatora. | Zachowuje czytelną hierarchię i pozwala ocenić świeżość jednym spojrzeniem. |
| W nagłówku | Czas pierwszej grupy przeniesiony do nagłówka Git: „CHANGES 6 · 5 min temu”; pozostałe grupy z własną linią i czasem. | Mniej wierszy. Ryzyko: czas przy Changes może wyglądać jak czas wszystkich plików statusu; dlatego nie jest rekomendowany. |
| Same linie | Granice grup bez etykiet; czas i zakres dostępne w dymkach. „Czas nieznany” zachowuje opis. | Najciszej, ale świeżość zmian wymaga najechania; słabszy do szybkiego przeglądu. |

Wszystkie trzy pokazują te same przykładowe pliki, grupy i liczby +/−. Względem P18 starszą serię przesunięto w przykładowych danych o 2 godziny, aby pokazać także etykietę godzin. Makieta ma stały czas odniesienia 26.10.2026, 21:19:06; nie jest bieżącym pomiarem. Opcja projektu pozwala przywrócić licznik plików w separatorach dwóch wariantów tekstowych i porównać jego wpływ.

Proponowane reguły po wyborze wariantu (do potwierdzenia):

- Wiek grupy to czas od **najnowszego zapisu**, również w Staged — nie czas stage. Tooltip mówi „Ostatnie zapisy na dysku” i podaje pełny zakres, rok, sekundy oraz liczbę plików. Etykieta „5 min temu” nie oznacza, że każdy plik został zapisany dokładnie wtedy.
- Mniej niż minuta: „przed chwilą”; mniej niż godzina: pełne minuty, np. „5 min temu”; mniej niż doba: pełne godziny, np. „2 h temu”; mniej niż tydzień: „1 dzień temu”, „3 dni temu”; starsze: data „18.10” (z rokiem, jeżeli inny niż bieżący). Minuty, godziny i dni zaokrąglane w dół. Dni oznaczają okresy 24 h, nie „wczoraj”.
- „Czas nieznany” bez licznika; dokładny powód w podpowiedzi. Zapis z przyszłości: „czas z przyszłości”, bez ujemnego wieku. Zbliżone lub identyczne etykiety są dozwolone; nie łączą grup. Podział nadal według zaakceptowanych progów 5/15 minut.
- Aktualizacja etykiet przy dotychczasowym odświeżeniu i powrocie fokusu, bez dodatkowego odpytywania Git. Makieta nie wprowadza zegara działającego w tle; sposób odświeżania samego tekstu podczas długiego oglądania wymaga ustalenia w projekcie implementacji.

Nie usuwamy innych informacji z listy: folderów, liczników przy statusach Git ani zer w kolumnie +/−. Dzięki temu porównanie dotyczy wyłącznie separatorów.

## Reguły wdrożenia — P17 i P19 przyjęte, DEC-VCS-127

Użytkownik: „super wykonaj”. Wybrany rekomendowany „Czas względny”. Poniższe szczegóły techniczne to decyzje agenta w przyjętym zakresie.

| Reguła | Zachowanie |
|---|---|
| R-01 | Tylko widok Zmiany: Conflicts, Staged, Changes, Unversioned; wewnątrz malejący `lstat().st_mtime_ns`, przy remisie pełna ścieżka alfabetycznie. Jedna ścieżka ma ten sam czas w Staged i Changes. |
| R-02 | Nowa grupa, jeśli przerwa od poprzedniego pliku > 300 s lub rozpiętość od najnowszego > 900 s. Równość progowi pozostaje w tej samej grupie. |
| R-03 | Brak pliku lub błąd lstat: końcowa sekcja „Czas nieznany”, pliki alfabetycznie. Brak separatorów w pustym Staged; jego podpowiedź pozostaje. |
| R-04 | Wiek od najnowszego zapisu grupy: poniżej minuty „przed chwilą”, poniżej godziny „N min temu”, poniżej doby „N h temu”, poniżej tygodnia „1 dzień temu” albo „N dni temu”; dalej data dd.mm, z rokiem gdy inny niż bieżący. Pełne jednostki, zaokrąglane w dół. Przyszłość: „czas z przyszłości”. |
| R-05 | Separator nie pokazuje liczby plików. Dymek podaje pełny zakres od najstarszego do najnowszego zapisu (rok, sekundy, strefa), licznik i regułę podziału. Wiek aktualizowany przy odrysowaniu/odświeżeniu, bez dodatkowego timera lub operacji Git. |
| R-06 | Separatory nie są plikami: kliknięcie nie zmienia zaznaczenia, strzałki/Shift/spacja/menu omijają je. Zaznaczenie po kluczu (status, ścieżka) przetrwa sortowanie; spacja używa widocznej kolejności. |
| R-07 | Foldery i Projekt zachowują dotychczasową kolejność i wygląd, bez liczników linii i separatorów czasu. |
| R-08 | Dymek i odrysowanie nie czytają plików. Metadane i liczniki pobierane w Workerze razem ze statusem; opublikowany wynik jest spójny w ramach jednego odświeżenia (system plików nie zapewnia atomowego snapshotu). |
| R-09 | Staged HEAD → indeks (także repo bez HEAD), Changes indeks → dysk, Unversioned pusta treść → dysk. Rename porównuje starą i nową treść, samo przeniesienie daje +0 −0. Git atrybuty diff stosowane dla śledzonych plików; bez external diff i textconv. |
| R-10 | Kolumna 116 pt (54+8+54), monospace 12 pt, margines prawy 16 pt, zera szare. Duże liczby z wąską spacją; jeśli nie mieszczą się w polu, skrót wizualny z pełną liczbą w dymku. Zielony plus, czerwony minus; cały diff pliku, bez sumy dla grupy. |
| R-11 | Binarny: „binarne”; konflikt: „konflikt”; niedostępny wynik: „—” z powodem. Przed pierwszym wynikiem „…”. Nie zamieniać błędów ani brakujących rekordów numstat na zera. |
| R-12 | Unversioned: strumieniowe liczenie LF i końcowej linii bez LF; pusty plik 0. NUL w pierwszych 8000 bajtach oznacza binarny (jak domyślna heurystyka Git). Symlink liczony po treści dowiązania, bez czytania jego celu. Katalog/specjalny plik daje „—” z powodem; błędy poszczególnych plików nie blokują reszty listy. |
| R-13 | Nazwa/folder skracane przed kolumną liczb; podpowiedź klawiszy przed liczbami tylko przy szerokości listy >= 650 pt, w węższej liście w dymku. Wiersz pliku 24 pt, separator 24 pt, nagłówek listy 28 pt. |
