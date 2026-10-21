# vcs-lite — projekt techniczny v1

Projekt realizuje [SPEC.md](SPEC.md) na stosie z DEC-VCS-012. Każda decyzja projektowa (DES) wskazuje wymagania, które obsługuje. Projekt zaakceptowany 2026-10-21 (DEC-VCS-030) z poprawkami DEC-VCS-024–029. Pytania projektowe są we wspólnym rejestrze w SPEC.md.

## Ograniczenia wejściowe

| Ograniczenie | Źródło |
|---|---|
| Python + Tkinter/ttk, git przez CLI, bez zewnętrznych zależności w czasie działania. | DEC-VCS-012 |
| Footprint ≤ 60 MB w warunkach REQ-VCS-100; brak pracy w tle w bezczynności. | REQ-VCS-100–101, DEC-VCS-013 |
| Pakiet w workspace uv byte-brewery: `packages/vcs_lite/`, układ `src/` + `tests/`, budowanie hatchling, jak `packages/utils`. | DEC-VCS-005, konwencja repo |
| Uruchamianie w środowisku workspace: `requires-python = ">=3.10"`, obecnie Python 3.12.11 z Tk 8.6. | `pyproject.toml`, `.venv`, sprawdzone 2026-10-21; DEC-VCS-025 |

## Architektura

Trzy warstwy. Tk występuje tylko w najwyższej, więc całą logikę i większość scenariuszy AT da się testować bez ekranu.

```
ui/ (Tk)          okno, widoki; tylko rysuje stan i przekazuje zdarzenia
   ▲  stan             │ zdarzenia
   │                   ▼
app/ (bez Tk)     AppModel: stan aplikacji, reguły aktywności przycisków,
                  szkice wiadomości, S-VCS-01; zleca operacje do Worker
   ▲  wyniki           │ operacje
   │                   ▼
core/ (bez Tk)    gitcli · status · repo · difftool · settings
```

| Moduł | Odpowiedzialność | REQ |
|---|---|---|
| `core/gitcli.py` | Jedyne miejsce, które uruchamia `git`: środowisko, limity czasu, dekodowanie wyjścia, zamiana błędów na wynik. | REQ-VCS-010, REQ-VCS-014, REQ-VCS-017 |
| `core/status.py` | Czysta funkcja: bajty `git status --porcelain=v2 -z --branch` → `RepoStatus` (gałąź, upstream, ahead/behind, wpisy). Implementuje T-VCS-01. | REQ-VCS-003–004, REQ-VCS-019 |
| `core/repo.py` | Operacje na jednym repo: status, treść stron diffu, stage, unstage, commit, push, pull. | REQ-VCS-005, REQ-VCS-009–013, REQ-VCS-020 |
| `core/difftool.py` | Port `ExternalDiffTool` i adapter `CommandTemplateDiffTool` (DES-VCS-036–039). Zastępuje wbudowany `diffmodel` (DEC-VCS-035). | REQ-VCS-023 |
| `core/settings.py` | Skan `rootdir` i trwały zapis wyboru repo. | REQ-VCS-001, DEC-VCS-007, DEC-VCS-016 |
| `app/model.py` | `AppModel`: lista repo, wybrane repo, grupy plików, aktywność przycisków, szkice per repo, stan S-VCS-01. | REQ-VCS-002, REQ-VCS-009, REQ-VCS-016, REQ-VCS-021–022 |
| `app/worker.py` | Wykonanie operacji poza wątkiem Tk; najwyżej jedna operacja na repo naraz. | REQ-VCS-016, REQ-VCS-101 |
| `ui/*.py` | `MainWindow` (E-01), `RepoList`, `FileTree`, `DiffView`, `CommitBar`, `SettingsDialog` (E-02). | E-01, E-02 |

## Decyzje projektowe

### Wywoływanie gita

| ID | Decyzja | REQ |
|---|---|---|
| DES-VCS-001 | Każde wywołanie: `git -C <repo> -c core.quotepath=false …`, `stdin=DEVNULL` (poza commitem), wyjście jako bajty. Komunikaty dla użytkownika dekodowane UTF-8 z `errors="replace"`. | REQ-VCS-008, REQ-VCS-010 |
| DES-VCS-002 | Środowisko: `GIT_TERMINAL_PROMPT=0`, żeby git nie pytał o hasło w niewidocznym terminalu. `GIT_OPTIONAL_LOCKS=0` przy odczytach, żeby `git status` nie przepisywał indeksu. | REQ-VCS-014, REQ-VCS-017; AT-VCS-017 |
| DES-VCS-003 | Limity czasu: operacje lokalne 30 s, push i pull 120 s. Przekroczenie kończy proces i daje komunikat zamiast zawieszenia. | REQ-VCS-014, AT-VCS-015 |
| DES-VCS-004 | SSH: jeśli użytkownik nie ustawił `GIT_SSH_COMMAND` ani `core.sshCommand`, narzędzie dodaje `ssh -o BatchMode=yes`, żeby ssh nie czekał na hasło do klucza. Ustawień użytkownika nie nadpisuje. | REQ-VCS-014, DEC-VCS-026 |

### Status i grupy

| ID | Decyzja | REQ |
|---|---|---|
| DES-VCS-005 | Polecenie statusu: `git status --porcelain=v2 -z --branch --untracked-files=all`. Ignorowane pliki nie są zgłaszane, bo nie ma `--ignored`. | REQ-VCS-003–004, DEC-VCS-006 |
| DES-VCS-006 | Parser rozpoznaje nagłówki `# branch.oid`, `# branch.head`, `# branch.upstream`, `# branch.ab` oraz wpisy `1`, `2`, `u`, `?`. Wpis trafia do grup zgodnie z T-VCS-01 (REQ-VCS-003, REQ-VCS-019). Brak HEAD rozpoznawany po `# branch.oid (initial)`, detached HEAD po `# branch.head (detached)`. | T-VCS-01, UC-VCS-02 2b |

### Treść stron diffu

| ID | Decyzja | REQ |
|---|---|---|
| DES-VCS-007 | HEAD: `git cat-file blob HEAD:<ścieżka>`. Indeks: `git cat-file blob :<ścieżka>`. Kopia robocza: odczyt pliku z dysku. Strona „pusta” to pusty tekst. Treść trafia do zewnętrznego narzędzia (DES-VCS-038). | T-VCS-01, REQ-VCS-023 |
| DES-VCS-008 | Rozmiar sprawdzany przed odczytem (`git cat-file -s`, `os.stat`). Powyżej 1 MB treść nie jest ładowana. Plik jest binarny, jeśli pierwsze 8000 bajtów zawiera bajt NUL (ta sama heurystyka co w gicie). Uśpione w v1 (DEC-VCS-044). | REQ-VCS-007, REQ-VCS-100 |
| DES-VCS-009 | WYCOFANE (DEC-VCS-035): wbudowany `diffmodel` na `difflib` zastąpiony zewnętrznym narzędziem. | REQ-VCS-006 |
| DES-VCS-010 | WYCOFANE (DEC-VCS-035): liczenie wbudowanego diffu w wątku Worker. | REQ-VCS-006 |

### Operacje zmieniające repo

| ID | Polecenie | REQ |
|---|---|---|
| DES-VCS-011 | Stage: `git add -- <ścieżka>`; obejmuje też usunięcia. | REQ-VCS-005 |
| DES-VCS-044 | Oznaczenie konfliktu jako rozwiązanego: `GitRepo.mark_resolved(change)`. Gdy plik istnieje, czyta go jako bajty i szuka pierwszej linii zaczynającej się od `<<<<<<<`, `>>>>>>>` albo `|||||||` (znaczniki domyślnej długości 7). Znaleziona linia: wyjątek `UnresolvedConflict` z nazwą pliku i numerem linii, bez wywołania gita. Brak znaczników: `git add -- <plik>`. Brak pliku w kopii roboczej (konflikt zmieniony/usunięty rozwiązany usunięciem): `git rm -q -- <plik>`. Sama linia `=======` nie jest sprawdzana, bo w Markdownie podkreśla nagłówek; rozwiązany plik i tak nie ma `<<<<<<<` ani `>>>>>>>`. Ograniczenie: inna długość znaczników ustawiona atrybutem `conflict-marker-size` nie jest wykrywana. W `AppModel` spacja na wierszu z grupy Conflicts wywołuje `mark_resolved`. | REQ-VCS-024, DEC-VCS-050 |
| DES-VCS-012 | Unstage: `git restore --staged -- <ścieżka>`; przy zmianie nazwy obie ścieżki. W repo bez commitów: `git rm --cached -- <ścieżka>`. | REQ-VCS-005, AT-VCS-009 |
| DES-VCS-013 | Commit: `git commit -F -`, wiadomość przez stdin, więc bez problemów z cudzysłowami i wieloma liniami. Hooki działają normalnie. | REQ-VCS-009–010 |
| DES-VCS-014 | Push: `git push`. Bez upstreamu narzędzie pyta, a po zgodzie wykonuje `git push -u origin HEAD`. | REQ-VCS-011–013 |
| DES-VCS-015 | Pull: `git pull --ff-only`. | REQ-VCS-020, DEC-VCS-014 |

### Współbieżność i odświeżanie

| ID | Decyzja | REQ |
|---|---|---|
| DES-VCS-016 | Worker uruchamia każdą operację w osobnym wątku i oznacza repo jako zajęte (stan W TOKU). Druga operacja na zajętym repo jest odrzucana, a w interfejsie i tak jest nieaktywna. Porównanie w zewnętrznym narzędziu ma osobny klucz (repo, grupa, plik), więc repo pozostaje dostępne, dopóki okno diffu jest otwarte. Każda operacja zapamiętuje repo wybrane w chwili kliknięcia (REQ-VCS-021), a nie w chwili wykonania. | REQ-VCS-016, S-VCS-01 |
| DES-VCS-017 | Wyniki wracają przez `queue.Queue`. Wątek Tk sprawdza kolejkę przez `after(50)` **tylko wtedy, gdy trwa jakaś operacja**. W bezczynności nie działa żaden timer. Klucz pozostaje zajęty do chwili oddania wyniku przez `drain()`, dlatego `on_done` może bezpiecznie zlecić następną operację na tym samym repo (np. push po commicie); `drain()` oddaje także wyniki, które skończyły się w trakcie opróżniania kolejki. | REQ-VCS-101 |
| DES-VCS-018 | Odświeżanie: po każdej operacji; po `<FocusIn>` okna (z opóźnieniem 300 ms, żeby kilka zdarzeń nie wywołało kilku odświeżeń); przyciskiem Refresh. Na fokus odświeżane są liczniki wszystkich repo obserwowanych, a pełny stan tylko wybranego. | REQ-VCS-015, REQ-VCS-002 |

### Ustawienia i stan

| ID | Decyzja | REQ |
|---|---|---|
| DES-VCS-019 | Ustawienia w `~/Library/Application Support/vcs-lite/settings.json`: `{"rootdir": "~/PycharmProjects", "repos": ["byte-brewery", …], "diff_tool": [...]}` (polecenie narzędzia diffu, DES-VCS-037). `rootdir` jest zapisywany z `~` i rozwijany przy użyciu. Brak pliku albo brak klucza oznacza wartości domyślne. Uszkodzony plik albo wartość złego typu daje błąd z komunikatem zamiast cichego wyzerowania wyboru. Zapis atomowy: plik tymczasowy, potem `os.replace`. Nic nie jest zapisywane w repozytoriach. | REQ-VCS-001, REQ-VCS-017 |
| DES-VCS-020 | Skan: `os.scandir(rootdir)`, tylko bezpośrednie podkatalogi. Katalogi zaczynające się od kropki są pomijane. Repo to katalog, w którym istnieje `.git`, jako katalog albo plik (worktree). Pozostałe są pomijane. | DEC-VCS-007, DEC-VCS-016, DEC-VCS-027 |
| DES-VCS-021 | Szkice wiadomości: słownik w `AppModel`, kluczem jest repo. Nie są zapisywane na dysk. | REQ-VCS-022, DEC-VCS-020 |

### Interfejs (Tk)

| ID | Decyzja | REQ |
|---|---|---|
| DES-VCS-042 | Wygląd okna według wzorca `docs/ui-reference/UI-REFERENCE.md` (DEC-VCS-045): tokeny kolorów, typografia, wymiary i stany w jednym module `ui/theme.py`; widżety biorą wartości wyłącznie z niego. Odstępstwa tylko z tabeli „Przybliżenia w Tk”. Widżety według DEC-VCS-047: pasek boczny, chipy, liczniki, kwadraty statusu i lista plików na `tk.Canvas` i `PhotoImage`; przyciski `ttk` aqua. | DEC-VCS-045, DEC-VCS-047, E-01 |
| DES-VCS-043 | `AppModel` podaje nazwę trwającej operacji (P4) i nazwę operacji, która się nie powiodła, razem z treścią od gita (P3); komunikat można zamknąć. Podaje też czas ostatniego odświeżenia wybranego repo dla paska stanu. Treść pytania o upstream według P9. | DEC-VCS-049, REQ-VCS-010, REQ-VCS-016, REQ-VCS-013 |
| DES-VCS-022 | Układ E-01: poziomy `ttk.PanedWindow` z dwiema kolumnami (repo, pliki) i dolny pasek commita; bez panelu diffu (DEC-VCS-035). Wymiary i kolejność elementów według wzorca (DES-VCS-042): pasek narzędzi, pasek boczny 230, lista plików, panel commita, pasek stanu. | E-01, DEC-VCS-015 |
| DES-VCS-023 | `RepoList`: `ttk.Treeview` z kolumnami nazwa, gałąź, liczba zmian. Repo NIEDOSTĘPNE jest wyszarzone. Wygląd elementu repo i stanów według wzorca (DES-VCS-042). | REQ-VCS-002, REQ-VCS-018 |
| DES-VCS-024 | `FileTree`: `ttk.Treeview` z węzłami grup i plikami. Stage i unstage: spacja lub menu kontekstowe; dwuklik lub Enter otwiera porównanie (DEC-VCS-040). Plik w obu grupach to dwa osobne wiersze. Grupy, kwadraty statusu i podpowiedzi według wzorca (DES-VCS-042). | REQ-VCS-003, REQ-VCS-005 |
| DES-VCS-025 | WYCOFANE (DEC-VCS-035): wbudowany `DiffView` na dwóch `tk.Text`. | REQ-VCS-006 |
| DES-VCS-026 | `CommitBar`: wieloliniowe pole wiadomości oraz przyciski z nazwą repo („Commit do byte-brewery”), Commit & Push, Pull i Refresh. Aktywność przycisków liczy `AppModel`. Skróty: ⌘1–⌘9, ⌘↩, ⌘⇧↩. Przyczynę nieaktywności przycisku Commit podaje `AppModel.commit_disabled_reason` (np. konflikt, brak Staged, pusta wiadomość; REQ-VCS-019). Commit & Push najpierw robi commit, a dopiero potem pyta o ustawienie upstreamu (kolejność UC-VCS-06, krok 3a); odmowa zostawia commit bez pusha (REQ-VCS-013). Układ panelu commita, tekst zastępczy i linia przyczyny według wzorca (DES-VCS-042). | REQ-VCS-009, REQ-VCS-021–022 |
| DES-VCS-027 | WYCOFANE (DEC-VCS-035): kolory wbudowanego diffu. Tryb ciemny i tak poza v1, DEC-VCS-028. | DEC-VCS-028 |

### Zewnętrzne narzędzie diffu

| ID | Decyzja | REQ |
|---|---|---|
| DES-VCS-036 | Port `ExternalDiffTool` w `core/difftool.py` (`typing.Protocol`): `open(left: Path, right: Path, left_title: str, right_title: str) -> RunningDiff`. Warstwa `app` zna tylko port. Konkretny adapter wybiera punkt startowy aplikacji (`ui/main.py`) na podstawie ustawień. | REQ-VCS-023, DEC-VCS-024 |
| DES-VCS-037 | Adapter `CommandTemplateDiffTool`: polecenie jako lista argumentów z polami `{left}`, `{right}`, `{left_title}`, `{right_title}`, zapisana w `settings.json`. Domyślnie Beyond Compare: `["/Applications/Beyond Compare.app/Contents/MacOS/bcomp", "{left}", "{right}", "-title1={left_title}", "-title2={right_title}"]`. Składnia `-title1`/`-title2` w BC4 na macOS potwierdzona ręcznie (OBS-VCS-008). Inne narzędzie podłącza się zmianą listy, bez zmian w kodzie. | REQ-VCS-023 |
| DES-VCS-038 | Strony z gita (HEAD, indeks) trafiają do plików tymczasowych tylko do odczytu (`0o444`). Strona z kopii roboczej to prawdziwa ścieżka, więc edycja w narzędziu zmienia plik na dysku. Pliki tymczasowe mają nazwę oryginalnego pliku (w katalogach `left/` i `right/`), żeby narzędzie rozpoznało typ pliku. Wątek Worker czeka na zakończenie procesu (`bcomp` czeka na zamknięcie okna), a potem usuwa pliki tymczasowe, także gdy narzędzie nie wystartowało, i odświeża repo. | REQ-VCS-017, REQ-VCS-023 |
| DES-VCS-039 | Gdy polecenie z ustawień nie istnieje albo kończy się błędem, narzędzie pokazuje komunikat ze ścieżką i stderr. Błąd to: proces nie wystartował albo zakończył się kodem różnym od 0 z niepustym stderr. Sam kod różny od 0 nie jest błędem, bo narzędzia diffu (także Beyond Compare) tak sygnalizują, że pliki się różnią. | REQ-VCS-023 |

DES-VCS-036–039 wchodzą do v1 i zastępują wbudowany diff (DEC-VCS-034, DEC-VCS-035). Edycja kopii roboczej w DES-VCS-038 jest dozwolona (DEC-VCS-039).

## Uruchamianie

| ID | Decyzja | REQ |
|---|---|---|
| DES-VCS-028 | Punkt wejścia `vcs-lite = "vcs_lite.ui.main:main"` w `[project.scripts]`, jak w `packages/utils`. | REQ-VCS-103 |
| DES-VCS-029 | Uruchamianie: `uv run vcs-lite` w katalogu byte-brewery, w środowisku workspace (obecnie Python 3.12.11, Tk 8.6). Kod nie korzysta z funkcji dostępnych tylko w Tk 9. | REQ-VCS-103, DEC-VCS-025 |
| DES-VCS-041 | Przed pierwszym `tkinter.Tk()` punkt startowy ustawia `TCL_LIBRARY` i `TK_LIBRARY` na `lib/tcl8.6` i `lib/tk8.6` Pythona bazowego (`sys.base_prefix`), o ile użytkownik ich nie ustawił i katalogi istnieją. Bez tego Tk nie startuje w venv z Pythona uv (OBS-VCS-009). | REQ-VCS-103, DEC-VCS-025 |
| DES-VCS-030 | Kod zgodny z Pythonem 3.10+, żeby nie zawężać `requires-python` całego workspace i nie zmieniać zależności pozostałych pakietów. | Ograniczenia wejściowe, DEC-VCS-025 |

## Testy

| ID | Decyzja | VER |
|---|---|---|
| DES-VCS-031 | Testy jednostkowe `core/` na tymczasowych repo tworzonych przez git CLI w `tmp_path`; push i pull na lokalnym repo bare jako `origin`. Każdy wiersz T-VCS-01 ma swój test. Nazwy testów według DEC-VCS-029. | VER-VCS-001–004, VER-VCS-009 |
| DES-VCS-032 | Scenariusze AT dotyczące przycisków, pól i grup są testowane na `AppModel`, bez Tk. Ręczna weryfikacja w Tk tylko dla układu okna. Zgodne z DEC-VCS-029. Atrapy w `tests/fakes.py`: `ManualWorker` (ten sam kontrakt co `Worker`, zadania uruchamiane jawnie przez `settle()`) i `FakeDiffTool` (zapisuje wywołania, może edytować prawą stronę). AT-VCS-015 korzysta z prawdziwego `Worker` i lokalnego serwera HTTP odpowiadającego 401. | VER-VCS-003, VER-VCS-005, VER-VCS-008, VER-VCS-010 |
| DES-VCS-033 | Nazwy testów zawierają ID scenariusza i wymagania, np. `test_at_vcs_010_req_vcs_009_commit_only_staged`. `ACCEPTANCE.feature` jest dokumentacją, a wykonują go zwykłe testy pytest, bez `pytest-bdd`. | DEC-VCS-029 |
| DES-VCS-034 | Skrypt pomiaru `tests/measure_footprint.py`: buduje środowisko z REQ-VCS-100 (3 repo, 300 zmian, otwarte porównanie w zewnętrznym narzędziu; mierzony tylko proces vcs-lite, DEC-VCS-042), uruchamia narzędzie, po 5 s odczytuje `footprint <pid>`, mierzy czas odświeżenia repo z 300 zmianami i zapisuje wyniki z wersją Pythona i Tk. | REQ-VCS-100, REQ-VCS-102, VER-VCS-006 |
| DES-VCS-035 | Test REQ-VCS-101: licznik wywołań w `gitcli` i sprawdzenie, że przez 10 s bezczynności bez fokusu nie było żadnego. | REQ-VCS-101 |
| DES-VCS-040 | Program sprawdzający śledzenie powiązań: `tests/traceability.py` (wczytanie dokumentów, testów i modułów, reguły, macierz) oraz `tests/test_traceability.py` (jeden test na regułę i testy samego programu). Zakresy z półpauzą są rozwijane; definicją jest wiersz tabeli zaczynający się od ID, nagłówek zaczynający się od ID albo tag `@AT_VCS_nnn`. Decyzje i wymagania oznaczone WYCOFANE lub ZASTĄPIONE nie liczą się jako pokrycie. Przełącznik `TDD_STARTED` w `test_traceability.py` włącza oblewanie za brak testów AT (DEC-VCS-037). Macierz trafia do `docs/TRACE.md`. | REQ-VCS-200–207, DEC-VCS-036, DEC-VCS-037 |

## Kolejność realizacji

1. Sprawdzanie śledzenia powiązań (REQ-VCS-200–207), DES-VCS-040.
2. `core/status.py` (czysta funkcja) z testami T-VCS-01 oraz `core/difftool.py` z adapterem testowym.
3. `core/gitcli.py` i `core/repo.py` z testami na tymczasowych repo, w tym push i pull.
4. `core/settings.py`, potem `app/model.py` i `app/worker.py` z testami AT na modelu.
5. `ui/` i ręczna weryfikacja w Tk.
6. Pomiar DES-VCS-034 i przejście DoD.

## Ryzyka

| Ryzyko | Skutek | Środek zaradczy |
|---|---|---|
| Beyond Compare 4 na Macu jest tylko na Intel i działa przez Rosettę (OBS-VCS-005). | Gdy Apple ograniczy Rosettę, diff przestanie działać. | Adapter wymienny (DES-VCS-037): zmiana polecenia w ustawieniach na BC5 lub inne narzędzie. |
| Brak wbudowanego diffu (DEC-VCS-035). | Bez działającego narzędzia zewnętrznego nie ma żadnego podglądu zmian. | Komunikat DES-VCS-039; świadoma decyzja użytkownika. |
| Tk 8.6 na macOS jest starszy niż Tk 9 (gorsza obsługa trybu ciemnego, starsze zachowanie widgetów). | Tryb ciemny poza v1 (DEC-VCS-028); inne różnice niezbadane. | Ręczna weryfikacja UI w Tk 8.6 w kroku 4 kolejności realizacji. |
| Hook `pre-commit` może działać długo albo czekać na wejście. | Operacja W TOKU przez dłuższy czas. | Limit czasu 30 s (DES-VCS-003) może być za krótki dla ciężkich hooków; do obserwacji w użyciu. |
| Wiele tysięcy plików nieśledzonych, np. niezignorowany `node_modules/`. | Długi status i duża lista. | Do obserwacji; v1 nie ogranicza listy. |

## Pytania projektowe

Rozstrzygnięte: Q-VCS-012b, 012c, 015–019, 024–028. Q-VCS-029 rozstrzygnięte (DEC-VCS-044). Brak otwartych pytań projektowych.
