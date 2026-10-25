# vcs-lite — propozycja: panel „Historia” na dole okna (jak Git → Log w PyCharmie)

Status: etap H1 przyjęty 2026-10-25 (DEC-VCS-116–119, Q-VCS-060 w `SPEC.md`); makieta zaakceptowana (wzorzec E-06), plan prac przyjęty. Reguły H-01–H-49 poniżej przyjęte przez użytkownika 2026-10-25 (DEC-VCS-120). Prośba użytkownika 2026-10-25: „przemyslal jak powinien wygladac i jaki zakres fynkcjonalnosci powinno miec dolna sekcja version history jaki w Pycharm”. Makieta: [ui-reference/E-06-historia.html](ui-reference/E-06-historia.html). Historia jest dziś w backlogu v2 (DEC-VCS-011), więc wejście do v1 zmienia zaakceptowaną decyzję.

## Co ma PyCharm (okno Git, karta Log, ⌘9)

| Część | Zawartość |
|---|---|
| Lewo | drzewo gałęzi: HEAD, lokalne, zdalne; pole filtra |
| Środek | lista commitów z grafem gałęzi (kolorowe tory, kropki, połączenia merge), tytuł z etykietami gałęzi i tagów, autor, data; pasek filtrów: tekst (wyrażenie regularne, wielkość liter), Gałąź, Użytkownik, Data, Ścieżki |
| Prawo | pliki zmienione w commicie (drzewo folderów), pod nimi szczegóły: pełna wiadomość, hash, autor, data, „w N gałęziach” |
| Zachowanie | dwuklik na pliku: diff pliku w tym commicie; strzałki i Enter po liście; commity niewypchnięte wyróżnione |
| Menu commita | kopiuj hash, utwórz łatkę, cherry-pick, checkout, pokaż repo w tej wersji, porównaj z lokalną, reset, revert, cofnij commit, edytuj wiadomość, fixup, rebase interaktywny, nowa gałąź, nowy tag |
| Historia pliku | „Show History” z menu pliku: ten sam widok zawężony do pliku |

## Fakty sprawdzone na tym Macu (git 2.47.1, 2026-10-25, tylko odczyt)

| Sprawdzenie | Wynik |
|---|---|
| największe repo użytkownika (`pi-mono`) | 3994 commity, 193 merge, 14 gałęzi |
| `git log --all --topo-order -z` z hashem, rodzicami, autorem, datą, etykietami i tytułem, cała historia `pi-mono` | 0,05 s, 650 KB |
| to samo, 500 commitów | 0,025 s, 82 KB |
| `git log -i -F --grep=fix -n 200` | 0,01 s |
| `git show --name-status -z --format= HEAD` (pliki commita) | 0,01 s |

Wniosek: git odpowiada w setnych częściach sekundy; o koszcie decyduje rysowanie, nie git. Rysowane są tylko widoczne wiersze (ok. 30), więc pamięć zależy od wysokości panelu, nie od długości historii.

## Zakres proponowany

### Etap H1 (rekomendacja): tylko odczyt

1. **Miejsce (DEC-VCS-118).** Panel zawsze widoczny, na całą szerokość okna nad paskiem stanu. Panel commita tylko pod listą plików; pasek repozytoriów sięga do historii. Wysokość ustawiana przeciągnięciem granicy i zapamiętana w ustawieniach.
2. **Lista commitów wybranego repo.** Graf gałęzi (tory i kropki, merge jako połączenie dwóch torów), tytuł, etykiety (`HEAD`, gałęzie lokalne, `origin/…`, tagi), autor, data („dziś 14:05”, „wczoraj 09:12”, „23.10.2026”). Commity niewypchnięte (przed upstreamem) ze strzałką ↑ i pogrubionym tytułem. Najnowsze na górze, kolejność topologiczna.
3. **Zakres gałęzi.** Przełącznik „Gałęzie: wszystkie / bieżąca” (PyCharm domyślnie pokazuje wszystkie).
4. **Filtr.** Jedno pole: tekst w wiadomości, początek hasha albo autor (`git log -i -F --grep`, `--author`); opóźnienie 250 ms jak w „Szukaj w plikach”.
5. **Szczegóły zaznaczonego commita.** Tytuł i treść wiadomości, skrócony hash, autor z e-mailem, data, rodzice (kliknięcie przechodzi do rodzica); lista plików zmienionych z kolorami statusu jak w liście plików (§9 wzorca), z folderem za nazwą.
6. **Dwuklik albo Enter na pliku** otwiera diff w przeglądarce: rodzic ↔ commit, tymi samymi stronami co dziś (`.md` wyrenderowany, tekst lewo–prawo, obrazki i PDF jako plik). Commit merge porównuje z pierwszym rodzicem.
7. **Menu commita (tylko odczyt):** „Kopiuj hash”, „Kopiuj adres commita” (adres `https://` z REQ-VCS-035 i `/commit/<hash>` dla GitHuba i GitLaba), „Otwórz w przeglądarce”.
8. **Klawiatura.** Strzałki po liście commitów; Enter albo Tab przenosi fokus do plików commita; ⌘F w panelu przenosi do pola filtra.
9. **Ładowanie.** 500 commitów na raz, kolejne 500 przy przewinięciu do końca; odświeżenie razem z odświeżeniem repo (po commicie, pull, powrocie fokusu), nigdy cyklicznie.

### Etap H2 (później, po H1)

Historia pliku („Pokaż historię” w menu kontekstowym pliku, `git log --follow -- <plik>`), filtr ścieżki, autor z listy, zakres dat, drzewo gałęzi po lewej stronie panelu.

### Poza zakresem (backlog v2, REQ-VCS-017)

Checkout commita, cherry-pick, revert, reset, rebase, amend, edycja wiadomości, tworzenie gałęzi i tagów, fetch. Panel tylko czyta repo.

## Najtrudniejsze miejsca

1. **Graf gałęzi.** Przypisanie torów: każdy commit dostaje kolumnę; pierwszy rodzic dziedziczy kolumnę dziecka, kolejni rodzice dostają wolne kolumny; tor kończy się, gdy dochodzi do rodzica. Czysta funkcja w `core` (bez Tk), testowana na małych historiach (liniowa, gałąź z merge, dwa merge naraz, gałąź bez merge, kilka korzeni). Na Canvas rysowane są tylko widoczne wiersze: kropka, odcinki w górę i w dół, łuki przejść między torami. Bardzo szerokie grafy (dziesiątki gałęzi) przycinane do 8 torów ze znakiem „…”.
2. **Pamięć (REQ-VCS-100).** 4000 commitów to krotki rzędu 2–3 MB; Canvas trzyma tylko widoczne wiersze. Pomiar `tests/measure_footprint.py` rozszerzony o otwarty panel na największym repo.
3. **Brak pracy w tle (REQ-VCS-101).** Log czytany przy starcie, zmianie repo i odświeżeniu; nic cyklicznie.
4. **Układ okna.** Panel zabiera wysokość liście plików; minimalne wysokości listy plików i panelu, żeby panel commita był zawsze widoczny.
5. **Niewypchnięte commity.** `git rev-list @{u}..HEAD` tylko przy gałęzi z upstreamem; bez upstreamu brak znacznika (jak w pasku bocznym).
6. **Etykiety.** `%D` z `git log` (np. `HEAD -> main, origin/main, tag: v0.3`) rozbite na etykiety; `origin/HEAD` pomijane jak w PyCharmie.

## Przypadki graniczne i reguły (krok 0, EARS)

### Źródła (przeczytane 2026-10-25)

| Źródło | Co z niego wynika |
|---|---|
| P. Vigier, „Commit graph drawing algorithms” (2019), https://pvigier.github.io/2019/05/06/commit-graph-drawing-algorithms.html | proste gałęzie: commit zajmuje kolumnę dziecka, którego jest pierwszym rodzicem; przy kilku takich dzieciach najbardziej lewą; pozostałe kolumny zwalniane bez przesuwania innych; strefa zakazana: commit nie może stać w kolumnie zajętej między nim a jego dzieckiem z merge; kolejność musi być topologiczna (data autora zawodzi przy rebase i cherry-pick, data commita przy przesuniętym zegarze); rysowanie tylko widocznej części (0,58 ms zamiast 106 ms) |
| DoltHub, „Drawing a commit graph” (2024), https://www.dolthub.com/blog/2024-08-07-drawing-a-commit-graph/ | trzy przypadki: czubek bez dzieci dostaje nową kolumnę, commit z dziećmi gałęzi bierze kolumnę najbardziej lewego, commit tylko z dziećmi merge szuka wolnej kolumny na prawo; linie gałęzi proste, połączenia jako krzywe Béziera; biblioteka gitgraph „nie radzi sobie z paginacją” |
| git, testy `t/t4214-log-graph-octopus.sh`, `t/t4215-log-skewed-merges.sh`, `t/t4202-log.sh` (https://github.com/git/git/tree/master/t) | kształty: merge ośmiornicy z 3–5 rodzicami, pierwszy rodzic po lewej („left-skewed”), rodzic ośmiornicy już na innym torze („crossover”), zagnieżdżone merge, kilka czubków, gałąź niezwiązana obok ośmiornicy; limit torów `--graph-lane-limit` z oznaczeniem przycięcia; poprawki kolorów torów w ośmiornicach (2018, 2019) |
| JetBrains, IntelliJ IDEA Help, karta Log (https://www.jetbrains.com/help/idea/log-tab.html) | długie krawędzie bez commitów domyślnie skracane strzałką; zwijanie liniowych gałęzi; „Show First Parent”, „No Merges” (w H1 pomijamy: Yagni) |
| Próby na tym Macu 2026-10-25 (OBS-VCS-015) | `--all` pokazuje `refs/stash` i `refs/notes`; `--decorate=full` odróżnia gałąź lokalną od zdalnej (lokalna `origin/fake` to `refs/heads/origin/fake`); płytki klon: commit `grafted` bez rodziców; świeże repo: `HEAD` jako argument daje błąd 128; `--grep` z `--author` to iloczyn, nie suma |

### Odczyt historii

| ID | Reguła (EARS) |
|---|---|
| H-01 | vcs-lite czyta historię jednym `git log --topo-order -z --decorate=full` z hashem, rodzicami, autorem, e-mailem, czasem autora, etykietami i tytułem, przez `GitCli` w trybie odczytu. |
| H-02 | Gdy zakres to „Wszystkie”, vcs-lite pokazuje commity osiągalne z gałęzi lokalnych, zdalnych, tagów i HEAD (`--branches --remotes --tags HEAD`), bez commitów `refs/stash` i `refs/notes`. |
| H-03 | Gdy zakres to „Bieżąca”, vcs-lite pokazuje commity osiągalne z HEAD. |
| H-04 | Jeśli repo nie ma HEAD (świeże repo), to vcs-lite nie podaje gitowi `HEAD`, a bez gałęzi i tagów pokazuje „Repo nie ma jeszcze commitów”. |
| H-05 | vcs-lite pokazuje dziecko nad rodzicem także wtedy, gdy rodzic ma późniejszą datę (rebase, cherry-pick, przesunięty zegar). |
| H-06 | vcs-lite wczytuje commity stronami po 500; gdy do końca wczytanej listy zostaje mniej niż 50 wierszy widocznych pod oknem, wczytuje następną stronę. |
| H-07 | vcs-lite rozpoznaje etykiety z `--decorate=full`: `refs/heads/…` gałąź lokalna, `refs/remotes/…` zdalna (bez `…/HEAD`), `tag: refs/tags/…` tag; `HEAD -> refs/heads/x` oznacza gałąź bieżącą, samo `HEAD` odłączony HEAD (etykieta „HEAD”); `grafted` nie jest etykietą. |
| H-08 | Gdy commit płytkiego klonu nie ma rodziców (`grafted`), vcs-lite rysuje go jak korzeń. |
| H-09 | Gdy tytuł commita jest pusty, vcs-lite pokazuje „(bez opisu)” w kolorze `dim`; tytuł, autor i treść są dekodowane UTF-8 z zastępowaniem błędnych bajtów. |
| H-10 | Gdy bieżąca gałąź ma upstream, commity z `git rev-list @{u}..HEAD` mają znacznik ↑ i pogrubiony tytuł; bez upstreamu i przy odłączonym HEAD znacznika nie ma. |
| H-11 | Jeśli git zwróci błąd, panel pokazuje „Nie udało się wczytać historii” i komunikat gita zamiast listy. |
| H-12 | Gdy wybrane repo jest niedostępne albo żadne nie jest wybrane, panel pokazuje „Repo niedostępne” albo pusty stan bez wywołania gita. |

### Graf gałęzi

| ID | Reguła (EARS) |
|---|---|
| H-20 | vcs-lite rysuje jeden commit na wiersz; tory to kolumny, a commit stoi na torze, który na niego czeka. |
| H-21 | Gdy na commit czeka kilka torów (kilkoro dzieci, rozgałęzienie), commit stoi na najbardziej lewym, a pozostałe tory dochodzą do niego łukiem i kończą się. |
| H-22 | Gdy na commit nie czeka żaden tor (czubek gałęzi), commit dostaje pierwszy wolny tor od lewej, a bez wolnego nowy tor z prawej. |
| H-23 | Pierwszy rodzic przejmuje tor commita, więc gałąź pierwszych rodziców jest prostą linią. |
| H-24 | Gdy commit ma kolejnych rodziców (merge), rodzic, na którego już czeka tor, dostaje łuk do tego toru, a pozostali pierwszy wolny tor. |
| H-25 | Gdy merge ma 3 i więcej rodziców (ośmiornica), każdy rodzic jest obsłużony jak w H-24, w kolejności rodziców. |
| H-26 | Gdy rodzic powtarza się na liście rodziców, vcs-lite liczy go raz. |
| H-27 | Tor jest zajęty od wiersza, w którym powstał, do wiersza commita, na którego czeka, więc linia nigdy nie przechodzi przez kropkę innego commita. |
| H-28 | Tor zwolniony w wierszu (korzeń, połączenie z H-21) jest wolny od następnego wiersza; wolne tory z prawej strony nie poszerzają grafu. |
| H-29 | Gdy commit nie ma rodziców (korzeń, gałąź `--orphan`, commit `grafted`), jego tor kończy się na kropce. |
| H-30 | Gdy repo ma kilka korzeni, każda niezwiązana historia jest rysowana osobno, bez połączeń między nimi. |
| H-31 | Nowy tor dostaje następny kolor z palety ośmiu kolorów po kolei; tor przejęty przez pierwszego rodzica zachowuje kolor; po zwolnieniu kolumny nowy tor w niej dostaje nowy kolor. |
| H-32 | Gdy rodzic nie jest jeszcze wczytany, tor biegnie do dołu listy; po wczytaniu następnej strony graf jest dokładany bez zmiany narysowanych wierszy. |
| H-33 | Gdy tor leży dalej niż w ósmej kolumnie, vcs-lite nie rysuje jego linii, a kropkę commita z takiego toru stawia w ósmej kolumnie jako pustą w środku (przycięcie). |
| H-34 | Podczas filtrowania graf nie ma linii: kropki stoją w jednej kolumnie, bo pominięte commity przerwałyby gałęzie. |
| H-35 | Układ grafu zależy tylko od kolejności commitów i ich rodziców: ten sam log daje zawsze ten sam graf. |

### Panel

| ID | Reguła (EARS) |
|---|---|
| H-40 | Panel jest zawsze widoczny (DEC-VCS-118); jego wysokość pochodzi z ustawień, a przeciągnięcie granicy zmienia ją w granicach: historia co najmniej 120 pt, górna część co najmniej 220 pt. |
| H-41 | Gdy zmienia się wybrane repo albo kończy się jego odświeżenie, vcs-lite czyta historię na nowo; nigdy cyklicznie. |
| H-42 | Gdy nowy odczyt zawiera zaznaczony commit, zaznaczenie i przewinięcie zostają; gdy go nie zawiera (amend, rebase, reset), zaznaczony jest pierwszy wiersz. |
| H-43 | Podczas odczytu historii operacje na repo pozostają dostępne; wynik odczytu, który się zestarzał (zmiana repo, filtra albo zakresu w trakcie), jest odrzucany. |
| H-44 | Gdy pole filtra nie jest puste, 250 ms po ostatnim znaku vcs-lite pokazuje sumę commitów z tekstem w wiadomości, z tekstem w autorze (bez wielkości liter) i, dla 4–40 znaków szesnastkowych, commitu o takim początku hasha; od najnowszego, najwyżej 500. |
| H-45 | Gdy commit jest zaznaczony, panel pokazuje tytuł, treść, skrócony hash, autora z e-mailem, pełną datę i rodziców oraz pliki: merge względem pierwszego rodzica, korzeń jako same dodane, zmiana nazwy jako „stara → nowa”, w kolorach statusu listy plików. |
| H-46 | Gdy użytkownik klika dwukrotnie plik commita albo naciska Enter, vcs-lite otwiera w przeglądarce diff rodzic ↔ commit według typu pliku (REQ-VCS-034); plik dodany ma pustą lewą stronę, usunięty pustą prawą. |
| H-47 | Menu commita ma „Kopiuj hash” (pełny), „Kopiuj adres commita” i „Otwórz w przeglądarce”; dwie ostatnie są aktywne, gdy adres zdalny (REQ-VCS-035) wskazuje GitHub, GitLab albo Bitbucket, i dają `https://<host>/<ścieżka bez .git>/commit/<hash>` (Bitbucket: `/commits/`). |
| H-48 | vcs-lite pokazuje datę jako „dziś 14:05”, „wczoraj 18:22” albo „24.10.2026” w strefie lokalnej, a pełną datę i godzinę w podpowiedzi. |
| H-49 | Nagłówek panelu podaje liczbę commitów w zakresie (`git rev-list --count`), z polską odmianą („1 commit”, „3 commity”, „5 commitów”). |

## Wpływ na architekturę i plan prac

### Zasada: historia jako drugi „moduł obok”, tak jak wyszukiwanie

„Szukaj w plikach” już ustaliło wzorzec, który dobrze się sprawdził: wartości i port w `core`, adapter na gicie w `core`, sesja bez Tk w `app`, widok w `ui`, złożenie w `ui/main.py` (DES-VCS-052–057). Historia powtarza ten kształt, więc nie wymyśla nowej architektury i nie dokłada odpowiedzialności do `AppModel` (dziś 705 linii, największy moduł `app`). Trzy warstwy zostają bez zmian: Tk tylko w `ui`, git tylko przez `GitCli`.

```
 ui/                                   app/                                    core/
 ┌────────────────────────────┐       ┌──────────────────────────────┐       ┌──────────────────────────────────┐
 │ MainWindow                 │       │ AppModel (bez nowych zadań   │       │ log.py  (wartości, bez I/O)       │
 │  PanedWindow pionowy:      │       │  historii; jedna nowa liczba │       │  Commit, Ref, CommitFile,          │
 │   góra: pasek repo │ pliki │       │  RepoView.refreshes)         │       │  CommitDetails, LogQuery           │
 │                   │ commit│       │        ▲ subscribe            │       │  «Protocol» HistoryReader          │
 │   dół: HistoryPanel        │       │        │                      │       ├──────────────────────────────────┤
 ├────────────────────────────┤ render│ HistorySession               │ uses  │ gitlog.py  GitLog(git)            │
 │ ui/history_panel.py        │◀──────│  zakres, filtr (opóźnienie), │──────▶│  read(repo, query) → LogPage      │
 │  HistoryPanel (nagłówek)   │       │  strony commitów, układ      │       │  details(repo, hash)              │
 │  CommitList (Canvas,       │──────▶│  grafu, zaznaczenie, szczegóły│       │  unpushed(repo) → set[hash]       │
 │   tylko widoczne wiersze)  │ zdarz.│  more(), open_file(), kopiuj │       ├──────────────────────────────────┤
 │  CommitView (szczegóły,    │       │        │ open_versions        │       │ graph.py  GraphLayout             │
 │   pliki commita)           │       │        ▼                      │       │  extend(commits) → [GraphRow]     │
 └────────────────────────────┘       │ PageOpener (wydzielony       │       │  czysta, bez Tk, krok po kroku    │
                                      │  z AppModel: typ pliku →     │       ├──────────────────────────────────┤
                                      │  strona w przeglądarce)      │       │ repo.py  GitRepo.blob(rev, path)  │
                                      └──────────────────────────────┘       └──────────────────────────────────┘
```

### Wpływ na istniejące moduły

| Moduł | Zmiana | Rodzaj |
|---|---|---|
| `core/log.py` | nowy: wartości `Commit(hash, parents, author, email, time, refs, subject)`, `Ref(kind, name)` (lokalna, zdalna, tag, `HEAD`), `CommitFile(status, path, old_path)`, `CommitDetails`, `LogQuery(scope, text, skip, limit)`, `LogPage(commits, more)`; czyste parsery wyjścia `git log -z` i `%D`; port `HistoryReader` | nowy, czysty |
| `core/gitlog.py` | nowy adapter `GitLog(git)`: `git log --topo-order -z --format=…` (z `--all` albo bez), `--skip`/`-n` stronami po 500, filtr `-i -F --grep`/`--author` albo hash; pliki commita `git diff-tree -r -z -M --name-status --root` (merge: względem pierwszego rodzica); `git rev-list @{u}..HEAD` | nowy |
| `core/graph.py` | nowy: `GraphLayout.extend(commits) → list[GraphRow]`; stan torów przechodzi między stronami, więc „kolejne 500” dokleja graf bez liczenia od nowa; `GraphRow` to tylko liczby (kolumna kropki, odcinki z kolumny do kolumny, kolor toru), żadnych współrzędnych ekranu | nowy, czysty, najwięcej testów |
| `core/repo.py` | `GitRepo.blob(rev, path)` zamiast samego `content(side, path)` dla HEAD i indeksu; `content` korzysta z `blob` | mała refaktoryzacja |
| `core/settings.py` | pole `history_height` (domyślnie 240), zapisywane jak `list_view` | rozszerzenie |
| `app/model.py` | **wydzielenie** `PageOpener` (`app/opening.py`): wybór strony według typu pliku (`activate`, `open_file`, `_show_change`, `_read`, `_show`, `_compare`) przenosi się do osobnej klasy, a `AppModel` deleguje; nowa metoda `open_versions(repo, path, left, right, titles)` obsługuje i zmiany, i pliki z commitów. Do `RepoView` dochodzi licznik `refreshes`. Właściwość `history_height` | refaktoryzacja przed zmianą, potem drobne |
| `app/history.py` | nowy `HistorySession`, jak `SearchSession`: stan bez Tk, opóźnienie filtra 250 ms, numery zapytań (starsze wyniki odrzucane), klucze Workera `history:…` (nie blokują operacji na repo, REQ-VCS-016), `subscribe` | nowy |
| `ui/main_window.py` | `_build`: `tk.PanedWindow` pionowy (góra i historia, przeciągana granica, `minsize` 220 i 120); panel commita przenosi się do prawej kolumny, pod listę plików; pasek boczny dostaje pełną wysokość góry; zapis wysokości po puszczeniu granicy | zmiana układu |
| `ui/history_panel.py` | nowy: `HistoryPanel` (nagłówek: pole filtra, `SegmentedControl` z `widgets.py`, licznik), `CommitList` (Canvas, rysuje tylko widoczne wiersze i ich kawałki grafu), `CommitView` (szczegóły i pliki; kolory i `fit_pieces` z listy plików) | nowy |
| `ui/main.py` | złożenie: `GitLog`, `HistorySession`, okno 1100 × 820 | kilka linii |
| `ui/theme.py` | tokeny E-06: tory, etykiety | rozszerzenie |
| `tests/world.py`, `fakes.py` | `world.history_session()`, repo z gałęziami i merge | rozszerzenie |
| `tests/measure_footprint.py` | panel zawsze widoczny: pomiar z historią repo o ~4000 commitach | rozszerzenie |

### Jak historia wie, że trzeba przeczytać log od nowa

Bez nowego mechanizmu zdarzeń: `HistorySession` subskrybuje `AppModel` (istniejący wzorzec obserwatora) i porównuje parę (wybrane repo, `RepoView.refreshes`). Zmiana repo, odświeżenie po commicie, pull, przycisk „Odśwież” i powrót fokusu (DEC-VCS-059) już podbijają ten licznik, więc historia dostaje te same chwile odczytu co status i nic nie działa cyklicznie (REQ-VCS-101). Wynik identyczny z poprzednim (ten sam pierwszy hash i etykiety) nie przerysowuje listy ani nie gubi zaznaczenia.

### Kolejność prac (każdy krok kończy się zielonymi testami i może być osobnym commitem)

| Krok | Treść | Ryzyko, które zdejmuje |
|---|---|---|
| 0 | Przypadki graniczne grafu i logu z internetu → reguły EARS H-01–H-49 (wyżej), scenariusze Gherkin AT-VCS-049–060, REQ-VCS-036–040 (DEC-VCS-117); E-06 w `ui-reference/` | luki w specyfikacji |
| 1 | Refaktoryzacja bez zmiany zachowania: `PageOpener` z `AppModel`, `GitRepo.blob` | „najpierw ułatw zmianę, potem zrób łatwą zmianę” (Kent Beck); `AppModel` nie rośnie |
| 2 | Nowy układ okna: `PanedWindow`, commit pod listą plików, pusta historia („Wczytuję…”), wysokość w ustawieniach, okno 1100 × 820; krok ręczny | największa zmiana wyglądu, sprawdzona na ekranie przed logiką |
| 3 | `core/log.py` i `core/gitlog.py` na tymczasowych repo | poprawność odczytu (Unicode, puste repo, odłączony HEAD, merge, root, zmiany nazw) |
| 4 | `core/graph.py` według scenariuszy z kroku 0 | najtrudniejszy algorytm, w pełni bez Tk |
| 5 | `app/history.py` z `ManualWorker` i `FakeTimers` | wyścigi: stare wyniki, filtr w trakcie pisania, zmiana repo w czasie odczytu |
| 6 | `ui/history_panel.py`: lista z grafem, szczegóły, pliki, diff w przeglądarce, menu, klawiatura | rysowanie tylko widocznych wierszy |
| 7 | Pomiar pamięci i czasu, kroki `MANUAL-UI.md`, `DESIGN.md`, `TRACE.md` | REQ-VCS-100 przy stale widocznej historii (dziś 45,9 MB z limitu 60) |

### Dlaczego tak (zasady)

- **Kształt jak wyszukiwanie:** ten sam podział na port, adapter, sesję i widok; nowa osoba czytająca kod rozpozna go od razu.
- **SRP i brak „boskiego” modelu:** historia ma własną sesję; jedyna zmiana w `AppModel` to wydzielenie otwierania stron, które i tak jest osobną odpowiedzialnością.
- **Czyste rdzenie:** parsowanie i graf to funkcje na wartościach; testy bez gita i bez ekranu, szybkie i dokładne dla przypadków granicznych.
- **DRY:** diff pliku z commita idzie tą samą drogą co dziś (`PageOpener` → strony `.md`, tekstowe, obrazki, PDF); kolory i skracanie z listy plików; `SegmentedControl` z `widgets.py`.
- **Yagni:** bez własnego indeksu i pamięci podręcznej (git odpowiada w setnych częściach sekundy); bez drzewa gałęzi i historii pliku w H1.
- **Natywny Tk:** `tk.PanedWindow` daje przeciąganie granicy i minimalne rozmiary bez własnej obsługi myszy.

## Decyzje (2026-10-25)

1. H1 w v1, tylko odczyt: tak (DEC-VCS-116).
2. Graf w H1: tak, najpierw przypadki graniczne z internetu jako Gherkin albo EARS, potem testy, potem kod (DEC-VCS-117).
3. Dolny panel zawsze widoczny; panel commita tylko pod listą plików; pasek repozytoriów do historii (DEC-VCS-118).
