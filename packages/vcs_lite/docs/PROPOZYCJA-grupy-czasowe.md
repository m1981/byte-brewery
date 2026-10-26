# vcs-lite — grupy plików według czasu ostatniego zapisu

Status 2026-10-26: pilotaż odczytowy wykonany; kierunek grupowania przyjęty (DEC-VCS-126, Q-VCS-065): „d1 tak, pokaz makiete”. [Makieta P18](ui-mockups/P18-grupy-czasowe.html) do akceptacji wyglądu (Q-VCS-066). P17 — sortowanie i kolumna +/− — zaakceptowane osobno (DEC-VCS-125), przed wdrożeniem. Użytkownik: „D1 jest super a widziales jakies wzorce jak mozna by grupowac pliki zmienione w podobnym czasie przez agenta. Jak chcesz mozesz zrobic pilotaz pomiarowy w w tym repo i ../doc oraz ../iso-template-engine”. Lokalizacje potwierdzone: „Tak, docs i iso-template-agent”.

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
