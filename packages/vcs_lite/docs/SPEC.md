# vcs-lite — specyfikacja funkcjonalna v1

Lekkie okno na macOS (Apple Silicon) pokazujące zmiany w kilku repozytoriach gita, jak zakładka VCS w PyCharm/WebStorm: pliki zmienione, poza kontrolą i staged, diff lewo–prawo, pole commita, Commit oraz Commit & Push.

Nazwa `vcs-lite` jest robocza. Reżim: NEED → REQ → DEC → VER → DoD, z listą OUT i źródłem przy każdej decyzji. Scenariusze akceptacyjne: [ACCEPTANCE.feature](ACCEPTANCE.feature). Status `PROPOZYCJA` oznacza, że użytkownik jeszcze tego nie zatwierdził.

## Potrzeby

| ID | Potrzeba | Źródło |
|---|---|---|
| NEED-VCS-001 | Przeglądać i commitować zmiany bez uruchamiania PyCharm lub GitHub Desktop, bo zużywają za dużo RAM-u, a wolnej pamięci jest mało. Niskie zużycie RAM-u jest kryterium kluczowym. | Użytkownik 2026-10-21: „Male zuzycie ram jest kluczowe. Bo Pycharm i GitDesktop pozeraj mi za duzo ramu”. |
| NEED-VCS-002 | Graficznie zobaczyć w repozytorium pliki zmienione, poza kontrolą i staged; mieć pole commita oraz akcje Commit i Commit & Push. | Ta sama wypowiedź. |
| NEED-VCS-003 | Oglądać diff w układzie lewo–prawo. | Ta sama wypowiedź: „wraz z diffem left-right”. |
| NEED-VCS-004 | Pracować na kilku repozytoriach wybranych w Settings checkboxami spośród folderów w `~/PycharmProjects`. | Odpowiedź 3 z 2026-10-21. |

## Poza zakresem v1 (OUT)

Wszystkie pozycje są potwierdzone.

- Stage fragmentów (hunków) i pojedynczych linii, DEC-VCS-001.
- Edycja treści w widoku diffu, DEC-VCS-002.
- Interfejs terminalowy (TUI), DEC-VCS-004.
- Discard zmian w pliku, DEC-VCS-010.
- Poprawne kolory w trybie ciemnym macOS, DEC-VCS-028.
- Repozytoria zagnieżdżone głębiej niż pierwszy poziom `rootdir`, DEC-VCS-007.
- Commit i push kilku repozytoriów jedną akcją, DEC-VCS-008.
- **Backlog v2**, DEC-VCS-011: amend, fetch, merge i rozwiązywanie konfliktów, tworzenie i przełączanie gałęzi, historia i log, stash, zarządzanie submodułami, zmiana `rootdir` z poziomu interfejsu, Windows i Linux. Pull w trybie innym niż fast-forward only (merge, rebase), DEC-VCS-014. PyCharm jako narzędzie diffu (ok. 690 MB), DEC-VCS-019.

## Język domeny

| Termin | Znaczenie |
|---|---|
| **rootdir** | Katalog, w którym narzędzie szuka repozytoriów: `~/PycharmProjects`, DEC-VCS-003. |
| **Repo obserwowane** | Repozytorium zaznaczone checkboxem w Settings. |
| **HEAD** | Ostatni commit bieżącej gałęzi. W repo bez commitów HEAD nie istnieje. |
| **Indeks** | Stan przygotowany do następnego commita (staging area). |
| **Kopia robocza** | Pliki na dysku. |
| **Staged** | Plik, którego stan w indeksie różni się od HEAD. |
| **Changes** | Plik śledzony, którego kopia robocza różni się od indeksu. |
| **Unversioned** | Plik nieśledzony i nieignorowany. |
| **Conflicts** | Plik w stanie niescalonym po merge, rebase lub cherry-pick. |
| **Upstream** | Gałąź zdalna skonfigurowana do pusha bieżącej gałęzi. |

Jeden plik może jednocześnie należeć do grup Staged i Changes, np. kod `MM`.

## Decyzje

| ID | Decyzja | Źródło i powiązania |
|---|---|---|
| DEC-VCS-001 | Stage i unstage tylko całych plików. | Użytkownik 2026-10-21: „1 stage calych plikow”. REQ-VCS-005, OUT. |
| DEC-VCS-002 | Diff w v1 tylko do odczytu. | Użytkownik 2026-10-21: „2 diff tylko do odczytu w v1”. REQ-VCS-006. Wbudowany diff zastąpiony przez Beyond Compare, DEC-VCS-035. Zmienione przez DEC-VCS-039: edycja kopii roboczej w Beyond Compare jest dozwolona. |
| DEC-VCS-003 | Lista wielu repozytoriów, wybieranych w Settings checkboxami spośród folderów w `rootdir = ~/PycharmProjects`. | Użytkownik 2026-10-21: „3 lista kilku repozytorow po wejsciu w sttings (wybieram z checkboxami foldery w rootdir= ~/PycharmProjects”. REQ-VCS-001–002; szczegóły skanu w Q-VCS-001. |
| DEC-VCS-004 | Odrzucone rozwiązania TUI, w tym lazygit z delta. Narzędzie ma okno graficzne. | Użytkownik 2026-10-21 o lazygit + delta: „probowalem i odrzucam”. |
| DEC-VCS-005 | Specyfikacja żyje w repo byte-brewery, w `docs/vcs-lite/`. | Użytkownik 2026-10-21: „zapisz wymagania ~/PycharmProjects/byte-brewery”. Wybór katalogu jest decyzją agenta: workspace uv obejmuje `packages/*` i odrzuca folder bez `pyproject.toml` (sprawdzone uv 0.8.13: „Workspace member … is missing a `pyproject.toml`”). Przeniesione 2026-10-21 do `packages/vcs_lite/docs/`, DEC-VCS-038. |
| DEC-VCS-006 | Pliki nieśledzone pokazywać pojedynczo, także wewnątrz nowych katalogów (`--untracked-files=all`), tak jak PyCharm. | Wybór agenta wynikający z NEED-VCS-002; zatwierdzone DEC-VCS-017. |
| DEC-VCS-007 | Repozytoria szukane tylko na pierwszym poziomie `rootdir`, bez zagnieżdżonych. | Użytkownik 2026-10-21: „01 nit tylko piwerwsza poziom”. Q-VCS-001, REQ-VCS-001. Nie rozstrzyga pokazywania folderów niebędących repo, Q-VCS-001b. |
| DEC-VCS-008 | Commit i push dotyczą zawsze jednego repozytorium naraz. Interfejs wyboru repo do commita trzeba zaprojektować tak, żeby był wygodny. | Użytkownik 2026-10-21: „tak commit/push tylko dla jednego repo na raz (trzeba przmeyslec jak zrobic wygodne GUI do tego)”. Q-VCS-002, REQ-VCS-021; projekt interfejsu w Q-VCS-009. |
| DEC-VCS-009 | Odrzucony push zostawia commit; narzędzie pokazuje błąd i nie robi automatycznie pull ani rebase. Pull to osobny przycisk, uruchamiany wyłącznie przez użytkownika. | Użytkownik 2026-10-21: „03: tak. Pull jako osobny guzik”. Q-VCS-003, REQ-VCS-012, REQ-VCS-020. Termin i tryb pull w Q-VCS-010. |
| DEC-VCS-010 | Bez Discard. | Użytkownik 2026-10-21: „04: bez discard”. Q-VCS-004, OUT. |
| DEC-VCS-011 | Pozycje OUT zaproponowane przez agenta zostają poza v1 i trafiają do v2. | Użytkownik 2026-10-21: „08: zostaja i zorbimy w v2”. Q-VCS-008, OUT. |
| DEC-VCS-012 | Stos: Python 3.14 z uv (Tk 9.0.4), Tkinter/ttk, git przez CLI, bez zewnętrznych zależności. | Użytkownik 2026-10-21: „06: zatwierdzam”. Q-VCS-006, REQ-VCS-103. Wersję Pythona i Tk zmienia DEC-VCS-025. |
| DEC-VCS-013 | Próg pamięci 60 MB. | Użytkownik 2026-10-21: „07: tak 60MB jest super”. Q-VCS-007, REQ-VCS-100. |
| DEC-VCS-014 | Pull działa w trybie fast-forward only; bez merge i rebase. | Użytkownik 2026-10-21: „10 pull fast-forward”. Q-VCS-010, REQ-VCS-020, UC-VCS-07. Termin: v1, DEC-VCS-018. |
| DEC-VCS-015 | Interfejs jednego repo: wariant A, master–detail. | Użytkownik 2026-10-21: „09: A”. Q-VCS-009, REQ-VCS-021–022, E-01. |
| DEC-VCS-016 | Podfoldery `rootdir`, które nie są repo gita, są w Settings ukryte. | Użytkownik 2026-10-21: „01b: ukryc”. Q-VCS-001b, REQ-VCS-001, UC-VCS-01 2b. |
| DEC-VCS-018 | Pull fast-forward wchodzi do v1. | Użytkownik 2026-10-21: „10b: pull fast forward w v1”. Q-VCS-010b, REQ-VCS-020, UC-VCS-07. |
| DEC-VCS-019 | Bez przycisku „Otwórz w PyCharm” w v1. Pytanie wraca przy planowaniu v2. | Użytkownik 2026-10-21: „12: nie” oraz „690MB to wstrzymajmy do wersji v2 niech wroci to pytanie”. Q-VCS-012, OBS-VCS-001–004. |
| DEC-VCS-020 | Szkic wiadomości commita przetrwa przełączanie repo; nie musi przetrwać zamknięcia narzędzia. | Użytkownik 2026-10-21: „13: wystarczy ze przetrwa przelaczenie repo”. Q-VCS-013, REQ-VCS-022. |
| DEC-VCS-021 | WYCOFANA. Agent odczytał „3: nie” jako odpowiedź na dwa pytania z punktu 3. | Użytkownik 2026-10-21: „DEC-VCS-021: powtorz pytania bo sie zgubilem”. Pytania wracają jako Q-VCS-020. |
| DEC-VCS-022 | Zgoda na projekt techniczny v1. | Użytkownik 2026-10-21: „4: tak” w odpowiedzi na punkt 4. Termin commita specyfikacji z tego samego punktu nie został rozstrzygnięty, Q-VCS-014. Projekt: [DESIGN.md](DESIGN.md). |
| DEC-VCS-023 | Commit specyfikacji teraz. | Użytkownik 2026-10-21: „14: teraz”. Q-VCS-014. |
| DEC-VCS-024 | Beyond Compare jako zewnętrzne narzędzie diffu, podłączone przez wymienny adapter (odwrócenie zależności), żeby dało się je zastąpić innym narzędziem z CLI. | Użytkownik 2026-10-21: „12: beyond comampare jako diff jest super widzialem okno i dzialo (zrob tak zebysmy mogli podminiec na inne narzedzi CLI Dependency inversion)”. Q-VCS-012, OBS-VCS-005, REQ-VCS-023, DES-VCS-036. Nie rozstrzyga terminu ani relacji do wbudowanego diffu: Q-VCS-012b, Q-VCS-012c. |
| DEC-VCS-025 | Uruchamianie: `uv run vcs-lite` w środowisku workspace byte-brewery (obecnie Python 3.12.11, Tk 8.6) zamiast osobnej instalacji z Pythonem 3.14 i Tk 9. | Użytkownik 2026-10-21: „15: a”. Q-VCS-015, DES-VCS-029. Zmienia wersję z DEC-VCS-012. |
| DEC-VCS-026 | Bez własnej konfiguracji ssh użytkownika narzędzie wymusza `BatchMode=yes`. | Użytkownik 2026-10-21: „16: tak”. Q-VCS-016, DES-VCS-004. |
| DEC-VCS-027 | Ukryte podkatalogi `rootdir` (zaczynające się od kropki) są pomijane. | Użytkownik 2026-10-21: „17: tak”. Q-VCS-017, DES-VCS-020. |
| DEC-VCS-028 | Poprawne kolory w trybie ciemnym macOS nie są wymagane w v1. | Użytkownik 2026-10-21: „18: nie”. Q-VCS-018, DES-VCS-027, OUT. |
| DEC-VCS-029 | `ACCEPTANCE.feature` jako dokumentacja; wykonują go zwykłe testy pytest nazwane ID scenariuszy, bez nowej zależności. | Użytkownik 2026-10-21: „19: b”. Q-VCS-019, DES-VCS-033. |
| DEC-VCS-030 | Projekt techniczny zaakceptowany, z poprawkami z DEC-VCS-024–029. | Użytkownik 2026-10-21: „Akceptuje projekt”. DESIGN.md. |
| DEC-VCS-031 | Przed architekturą kodu i testami TDD trzeba zapewnić działające śledzenie powiązań w obie strony (bidirectional traceability). | Użytkownik 2026-10-21: „zanim przjedziesz do architektury i testow TDD zadbaj o to zeby dzialalo bidirectional tracibility”. Sekcja „Śledzenie powiązań” w tym pliku. |
| DEC-VCS-032 | Bez pomiarów RAM-u Sublime Merge, Kaleidoscope i Meld. | Użytkownik 2026-10-21: „1: nie” na powtórzone pytanie 1 z Q-VCS-020. |
| DEC-VCS-033 | Bez rozważania Sublime Merge zamiast budowy vcs-lite. | Użytkownik 2026-10-21: „2: nie” na powtórzone pytanie 2 z Q-VCS-020. |
| DEC-VCS-034 | Zewnętrzny diff przez adapter (Beyond Compare) wchodzi do v1. | Użytkownik 2026-10-21: „12b: v1”. Q-VCS-012b, REQ-VCS-023. Zastępuje część DEC-VCS-019 o odłożeniu do v2 (dla PyCharma DEC-VCS-019 obowiązuje). |
| DEC-VCS-035 | Beyond Compare zastępuje wbudowany diff. | Użytkownik 2026-10-21: „12c: BC zastepuje wbudowany”. Q-VCS-012c. REQ-VCS-006 zastąpione przez REQ-VCS-023; skutki dla REQ-VCS-007, REQ-VCS-008, REQ-VCS-100 i DEC-VCS-002 w Q-VCS-024–027. |
| DEC-VCS-036 | Linia `Trace:` tylko w docstringach modułów. | Użytkownik 2026-10-21: „21: tylko modulach”. Q-VCS-021, REQ-VCS-206. |
| DEC-VCS-037 | Brak testu dla AT `@confirmed` oblewa sprawdzenie od startu TDD; wcześniej tylko raport. | Użytkownik 2026-10-21: „22: od startu TDD”. Q-VCS-022, REQ-VCS-205. |
| DEC-VCS-038 | Utworzyć szkielet `packages/vcs_lite/` i przenieść tam dokumentację. Wykonane 2026-10-21: `pyproject.toml`, `src/vcs_lite/__init__.py`, `docs/`; pakiet dopisany do zależności i źródeł workspace w głównym `pyproject.toml`. | Użytkownik 2026-10-21: „23: tak”. Q-VCS-023, DEC-VCS-005, REQ-VCS-207. |
| DEC-VCS-039 | Edycja strony kopii roboczej w zewnętrznym narzędziu jest dozwolona; strony z HEAD i indeksu pozostają tylko do odczytu. | Użytkownik 2026-10-21: „24: a”. Q-VCS-024. Zmienia DEC-VCS-002. |
| DEC-VCS-040 | Dwuklik lub Enter na pliku otwiera porównanie; stage i unstage to spacja i menu kontekstowe. | Użytkownik 2026-10-21: „25: jak polecasz”. Q-VCS-025, DES-VCS-024. |
| DEC-VCS-041 | REQ-VCS-007 i REQ-VCS-008 zostają, bo Beyond Compare może zostać wycofany (np. gdy Rosetta przestanie działać). | Użytkownik 2026-10-21: „26: zostaw bo moze BC bedzie wycofany jak rozeta przestanie dzialac albo cos bedzie nie tak”. Q-VCS-026. Nie rozstrzyga, czy w v1 obejmują porównanie w BC: Q-VCS-029. |
| DEC-VCS-042 | Limit 60 MB dotyczy wyłącznie procesu vcs-lite; dodatkowa pamięć Beyond Compare jest akceptowana. | Użytkownik 2026-10-21: „27: tylko vcs-lite i kacjeptuje ekstra ram na BC”. Q-VCS-027, REQ-VCS-100. |
| DEC-VCS-043 | Reguły śledzenia powiązań REQ-VCS-200–207 zaakceptowane. | Użytkownik 2026-10-21: „28: akceptuje”. Q-VCS-028. |
| DEC-VCS-044 | REQ-VCS-007 i REQ-VCS-008 są w v1 uśpione: obowiązują dopiero, gdy wróci wbudowany lub inny diff; w v1 każdy plik, także binarny i duży, trafia do Beyond Compare. | Użytkownik 2026-10-21: „1: a” na Q-VCS-029. |
| DEC-VCS-017 | Zatwierdzone wszystkie propozycje z Q-VCS-011: DEC-VCS-006, REQ-VCS-003, REQ-VCS-004, REQ-VCS-007, REQ-VCS-008, REQ-VCS-013, REQ-VCS-019, REQ-VCS-102 i UC-VCS-02 2b. | Użytkownik 2026-10-21: „11: tak”. |

## Wymagania funkcjonalne

| ID | Wymaganie | Status | Powiązania |
|---|---|---|---|
| REQ-VCS-001 | Settings pokazuje bezpośrednie podfoldery `rootdir` z checkboxem przy każdym; głębszych poziomów nie przeszukuje. Wybór przetrwa zamknięcie i ponowne uruchomienie narzędzia. | Potwierdzone; foldery niebędące repo są ukryte. | DEC-VCS-003, DEC-VCS-007, DEC-VCS-016, UC-VCS-01 |
| REQ-VCS-002 | Okno główne pokazuje listę repo obserwowanych z liczbą zmienionych plików i nazwą bieżącej gałęzi. Wybór repo pokazuje jego grupy plików. | Potwierdzone | NEED-VCS-004, UC-VCS-02 |
| REQ-VCS-003 | Pliki wybranego repo są pogrupowane w Staged, Changes, Unversioned i Conflicts według tabeli T-VCS-01. Pusta grupa jest ukryta lub oznaczona jako pusta. | Potwierdzone, DEC-VCS-017 | T-VCS-01 |
| REQ-VCS-004 | Pliki ignorowane przez `.gitignore` nie są pokazywane. | Potwierdzone, DEC-VCS-017 | T-VCS-01 |
| REQ-VCS-005 | Użytkownik może przenieść cały plik z Changes lub Unversioned do Staged (stage) i ze Staged z powrotem (unstage). Dotyczy to także usunięć i zmian nazwy. | Potwierdzone | DEC-VCS-001, T-VCS-01, UC-VCS-04 |
| REQ-VCS-006 | ZASTĄPIONE przez REQ-VCS-023 (DEC-VCS-035). Pierwotna treść: wybór pliku pokazuje wbudowany diff lewo–prawo, tylko do odczytu, z numerami linii, wyróżnieniem zmian, wyrównaniem i wspólnym przewijaniem; strony według T-VCS-01. | Zastąpione | DEC-VCS-002, DEC-VCS-035 |
| REQ-VCS-007 | Dla pliku binarnego lub przekraczającego limit rozmiaru narzędzie pokazuje komunikat zamiast diffu. Stage i unstage nadal działają. | Uśpione w v1, DEC-VCS-044; zachowane, DEC-VCS-041; limit 1 MB lub 20 000 linii, DEC-VCS-017. | UC-VCS-03 |
| REQ-VCS-008 | Tekst w kodowaniu innym niż UTF-8 jest pokazywany ze znakami zastępczymi. Narzędzie nigdy nie zmienia treści pliku. | Uśpione w v1, DEC-VCS-044; zachowane, DEC-VCS-041. | UC-VCS-03 |
| REQ-VCS-009 | Commit zapisuje wyłącznie zawartość Staged z wiadomością z pola commita. Przycisk jest nieaktywny, gdy Staged jest puste lub wiadomość składa się tylko z białych znaków. Po sukcesie pole wiadomości jest czyszczone. | Potwierdzone | UC-VCS-05 |
| REQ-VCS-010 | Jeśli git lub hook odrzuci commit, narzędzie pokazuje pełny komunikat (stdout i stderr). Wiadomość commita i Staged pozostają nienaruszone. | Potwierdzone | UC-VCS-05 |
| REQ-VCS-011 | Commit & Push wykonuje commit według REQ-VCS-009, a po jego sukcesie push bieżącej gałęzi do upstreamu. | Potwierdzone | UC-VCS-06 |
| REQ-VCS-012 | Gdy push się nie powiedzie, commit zostaje, narzędzie pokazuje komunikat gita i nie wykonuje automatycznie pull ani rebase. | Potwierdzone | DEC-VCS-009, UC-VCS-06 |
| REQ-VCS-013 | Gdy bieżąca gałąź nie ma upstreamu, narzędzie pyta o push z ustawieniem upstreamu do `origin`. Bez zgody nie wykonuje pusha. | Potwierdzone, DEC-VCS-017 | UC-VCS-06 |
| REQ-VCS-014 | Narzędzie nie prosi o dane logowania w ukrytym terminalu. Korzysta z konfiguracji gita użytkownika (credential helper, SSH agent). Brak uwierzytelnienia kończy się komunikatem, a nie zawieszeniem. | Potwierdzone | UC-VCS-06 |
| REQ-VCS-015 | Stan repo odświeża się po każdej operacji, przy powrocie fokusu do okna i na żądanie (przycisk Refresh). | Potwierdzone | UC-VCS-02 |
| REQ-VCS-016 | Trwająca operacja nie blokuje interfejsu. W czasie operacji na danym repo jego akcje są nieaktywne, a druga operacja na tym samym repo nie może wystartować. | Potwierdzone | S-VCS-01 |
| REQ-VCS-017 | Narzędzie zmienia repozytorium wyłącznie przez operacje wywołane przez użytkownika: stage, unstage, commit, push, pull. Nie wykonuje fetch z własnej inicjatywy, nie zmienia konfiguracji gita i nie tworzy plików w repo. | Potwierdzone | Wszystkie UC |
| REQ-VCS-018 | Repo obserwowane, które zniknęło lub przestało być repozytorium, jest oznaczone jako niedostępne. Narzędzie działa dalej dla pozostałych. | Potwierdzone | S-VCS-01 |
| REQ-VCS-019 | Commit jest zablokowany, gdy repo ma pliki w Conflicts, a narzędzie podaje przyczynę. | Potwierdzone, DEC-VCS-017 | T-VCS-01, S-VCS-01 |
| REQ-VCS-020 | Przycisk Pull pobiera i włącza zmiany z upstreamu bieżącej gałęzi wybranego repo. Działa tylko na żądanie użytkownika; żadna inna akcja go nie wywołuje. | Potwierdzone: v1, fast-forward only. | DEC-VCS-009, DEC-VCS-014, DEC-VCS-018, UC-VCS-07 |
| REQ-VCS-021 | Stage, unstage, Commit, Commit & Push i Pull działają na jednym repo: tym, które jest aktualnie wybrane. Interfejs w każdej chwili jednoznacznie pokazuje, którego repo dotyczy akcja: przyciski noszą nazwę repo, np. „Commit do byte-brewery”. | Potwierdzone | DEC-VCS-008, DEC-VCS-015, E-01 |
| REQ-VCS-022 | Każde repo obserwowane ma własny szkic wiadomości commita, zachowany przy przełączaniu repo w czasie działania narzędzia; po zamknięciu narzędzia nie jest zachowywany. Skróty: ⌘1–⌘9 wybór repo z listy, ⌘↩ Commit, ⌘⇧↩ Commit & Push. | Potwierdzone | DEC-VCS-015, DEC-VCS-020, E-01 |
| REQ-VCS-023 | Porównanie pliku otwiera jego strony (według T-VCS-01) w zewnętrznym narzędziu diffu przez wymienny adapter. Pierwszy adapter to Beyond Compare (`bcomp`); inne narzędzie z CLI da się podłączyć bez zmian w pozostałym kodzie. Zastępuje wbudowany diff. | Potwierdzone: v1, zastępuje wbudowany diff; edycja kopii roboczej dozwolona, DEC-VCS-039; wyzwalacz: dwuklik lub Enter, DEC-VCS-040. | DEC-VCS-024, DEC-VCS-034, DEC-VCS-035, DES-VCS-036, UC-VCS-03 |

## Wymagania jakościowe

| ID | Wymaganie | Miara i metoda | Status |
|---|---|---|---|
| REQ-VCS-100 | Niskie zużycie pamięci. | `Footprint` z `footprint <pid>` (to samo co kolumna Memory w Monitorze aktywności), po 5 s bezczynności. Warunki: 3 repo obserwowane, 300 zmienionych plików w jednym z nich, otwarte porównanie pliku 2000 linii w zewnętrznym narzędziu. Mierzony jest wyłącznie proces vcs-lite; pamięć Beyond Compare (ok. 235 MB, OBS-VCS-005) jest akceptowana osobno, DEC-VCS-042. **Cel: ≤ 60 MB.** Punkt odniesienia: prototyp okna Tk o tym kształcie, zmierzony 2026-10-21, zajął 38 MB (Python 3.14.7, Tk 9.0.4). | Potwierdzone, DEC-VCS-013 |
| REQ-VCS-101 | Brak pracy w tle podczas bezczynności. | Brak cyklicznych wywołań `git` i timerów odpytujących, gdy okno nie ma fokusu i nic nie jest w trakcie. Sprawdzenie logiem wywołań `git`. | Potwierdzone |
| REQ-VCS-102 | Szybkie odświeżenie stanu. | Odświeżenie repo z 300 zmienionymi plikami trwa < 1 s na Apple Silicon. | Potwierdzone, DEC-VCS-017 |
| REQ-VCS-103 | Platforma i uruchomienie. | macOS na Apple Silicon, stos według DEC-VCS-012 i DEC-VCS-025. Uruchomienie jedną komendą z terminala. | Potwierdzone |

## T-VCS-01 — tabela decyzyjna statusów

Wejście: `git status --porcelain=v2 -z --untracked-files=all`. `X` to stan indeksu względem HEAD, `Y` to stan kopii roboczej względem indeksu, `.` oznacza brak zmiany. Wpis z `X ≠ .` trafia do Staged, a wpis z `Y ≠ .` do Changes; oba warunki naraz dają plik w obu grupach.

| Typ wpisu i kod | Grupa | Akcja | Diff: lewa ↔ prawa |
|---|---|---|---|
| `1` z `X ∈ {M, T}` | Staged | Unstage | HEAD ↔ indeks |
| `1` z `X = A` | Staged | Unstage | pusta ↔ indeks |
| `1` z `X = D` | Staged | Unstage | HEAD ↔ pusta |
| `2` z `X ∈ {R, C}` | Staged; pokazuje `stara → nowa` | Unstage obu ścieżek | HEAD(stara) ↔ indeks(nowa) |
| `1`/`2` z `Y ∈ {M, T}` | Changes | Stage | indeks ↔ kopia robocza |
| `1`/`2` z `Y = D` | Changes | Stage (zapisuje usunięcie) | indeks ↔ pusta |
| `?` | Unversioned | Stage | pusta ↔ kopia robocza |
| `u` | Conflicts | brak w v1 | brak w v1, komunikat o konflikcie |
| `!` | niepokazywany | — | — |
| Repo bez commitów, dowolny `X ≠ .` | Staged | Unstage | pusta ↔ indeks |

## S-VCS-01 — stany repo obserwowanego

| Stan | Warunek | Dostępne akcje |
|---|---|---|
| NIEDOSTĘPNE | Folder nie istnieje albo nie jest repo. | Brak; Refresh sprawdza ponownie. |
| CZYSTE | Brak wpisów w T-VCS-01. | Refresh. |
| ZMIANY | Są wpisy, brak Conflicts. | Stage, unstage, diff; commit i Commit & Push, gdy Staged niepuste i wiadomość niepusta. |
| KONFLIKT | Są wpisy `u`. | Stage, unstage i diff innych plików; commit zablokowany, REQ-VCS-019. |
| W TOKU | Trwa stage, unstage, commit lub push. | Brak akcji na tym repo; inne repo dostępne. |

Po operacji zawsze następuje odświeżenie i przejście do stanu wynikającego z warunków. Błąd operacji jest komunikatem przy repo, a nie osobnym stanem.

## Ekrany

E-01, okno główne (szkic, nie projekt graficzny). Diff otwiera się w Beyond Compare (DEC-VCS-035), więc okno nie ma panelu diffu:

```
┌ Repozytoria ──┬ Pliki ─────────────────────────────────────┐
│ ● byte-brew 4 │ ▾ Staged (1)                               │
│   docs     12 │     src/app.py                             │
│   kitchen   0 │ ▾ Changes (2)                              │
│               │     README.md                              │
│               │     src/app.py                             │
│               │ ▾ Unversioned (1)                          │
│ [Settings]    │     notes.txt                              │
├───────────────┴────────────────────────────────────────────┤
│ byte-brewery · main → origin/main   [ wiadomość ...       ] │
│ [Commit do byte-brewery] [Commit & Push] [Pull] [Refresh]   │
└─────────────────────────────────────────────────────────────┘
```

E-02, Settings: lista folderów z `rootdir` z checkboxami, oznaczenie folderów niebędących repo (zależnie od Q-VCS-001), przyciski Zapisz i Anuluj.

## Przypadki użycia

Wspólne dla wszystkich UC. **Aktor podstawowy:** programista pracujący na Macu z małą ilością wolnej pamięci. **Granica:** narzędzie vcs-lite wraz z wywoływanym przez nie gitem. **Gwarancja minimalna:** narzędzie nie zmienia repo poza operacją wywołaną przez użytkownika (REQ-VCS-017), a każdy błąd gita jest pokazany użytkownikowi.

### UC-VCS-01 — Wybierz repozytoria do obserwowania

**Wyzwalacz:** użytkownik otwiera Settings. **Sukces:** lista repo obserwowanych odpowiada zaznaczeniom i przetrwa restart.

1. Użytkownik otwiera Settings.
2. System pokazuje bezpośrednie podfoldery `rootdir` z checkboxami; zaznaczone są obecne repo obserwowane.
3. Użytkownik zaznacza i odznacza foldery, po czym zapisuje.
4. System zapisuje wybór i aktualizuje listę w E-01.

| Krok | Warunek | Reakcja |
|---|---|---|
| 2a | `rootdir` nie istnieje. | Komunikat z ścieżką; lista pusta; zakończenie bez zmian. |
| 2b | Folder nie jest repo gita. | Ukryty, DEC-VCS-016. |
| 2c | Podfolder zawiera repo zagnieżdżone głębiej. | Niepokazywane, DEC-VCS-007. |
| 3a | Użytkownik anuluje. | Wybór bez zmian. |
| 4a | Zapis ustawień się nie udał. | Komunikat; poprzedni wybór obowiązuje. |

### UC-VCS-02 — Przejrzyj zmiany w repozytorium

**Wyzwalacz:** wybór repo w E-01, powrót fokusu do okna albo Refresh. **Sukces:** grupy plików odpowiadają `git status` w chwili odświeżenia.

1. Użytkownik wybiera repo z listy.
2. System odczytuje stan repo i pokazuje gałąź, upstream oraz grupy według T-VCS-01.

| Krok | Warunek | Reakcja |
|---|---|---|
| 2a | Repo niedostępne. | Stan NIEDOSTĘPNE, REQ-VCS-018. |
| 2b | Detached HEAD. | Zamiast nazwy gałęzi pokazany skrót commita; Commit dostępny, Commit & Push i Pull nieaktywne. DEC-VCS-017. |
| 2c | Wpisy `u`. | Stan KONFLIKT, REQ-VCS-019. |
| 2d | `git` zwraca błąd. | Komunikat z stderr; poprzednia lista oznaczona jako nieaktualna. |

### UC-VCS-03 — Porównaj plik w zewnętrznym narzędziu

1. Użytkownik otwiera porównanie pliku w jednej z grup dwuklikiem lub klawiszem Enter, DEC-VCS-040.
2. System przygotowuje strony według T-VCS-01 i otwiera je w zewnętrznym narzędziu przez adapter, REQ-VCS-023.
3. Po zamknięciu okna narzędzia system usuwa pliki tymczasowe i odświeża repo.

| Krok | Warunek | Reakcja |
|---|---|---|
| 2a | Plik binarny lub bardzo duży. | Trafia do zewnętrznego narzędzia jak każdy inny; REQ-VCS-007 uśpione w v1, DEC-VCS-044. |
| 2b | Narzędzie z ustawień nie istnieje albo kończy się błędem. | Komunikat ze ścieżką polecenia i stderr, DES-VCS-039. Wbudowanego diffu nie ma (DEC-VCS-035). |
| 2c | Plik zniknął z dysku między odświeżeniem a wyborem. | Komunikat i odświeżenie repo. |
| 2d | Plik w Staged i Changes. | Strony wynikają z grupy, z której wybrano porównanie. |
| 2e | Użytkownik edytuje stronę kopii roboczej w narzędziu. | Dozwolone, DEC-VCS-039; zapis trafia do pliku na dysku i jest widoczny po odświeżeniu w kroku 3. |

### UC-VCS-04 — Stage lub unstage pliku

1. Użytkownik wybiera akcję Stage lub Unstage przy pliku (przycisk, menu kontekstowe lub dwuklik).
2. System wykonuje operację dla całego pliku i odświeża repo.

| Krok | Warunek | Reakcja |
|---|---|---|
| 2a | Operacja gita się nie udała, np. blokada `index.lock`. | Komunikat z stderr; stan po odświeżeniu. |
| 2b | Zmiana nazwy. | Unstage obejmuje obie ścieżki, T-VCS-01. |

### UC-VCS-05 — Commit

**Warunki wstępne:** Staged niepuste, wiadomość niepusta, brak Conflicts. **Sukces:** nowy commit zawiera dokładnie zawartość Staged, a pole wiadomości jest puste.

1. Użytkownik wpisuje wiadomość i wybiera Commit.
2. System wykonuje commit, w tym hooki repo.
3. System czyści wiadomość i odświeża repo.

| Krok | Warunek | Reakcja |
|---|---|---|
| 2a | Hook lub git odrzuca commit. | Pełny komunikat; wiadomość i Staged bez zmian, REQ-VCS-010. |
| 2b | Hook modyfikuje pliki (np. formatter). | Komunikat gita; po odświeżeniu zmiany hooka widoczne w Changes. |
| 2c | Brak `user.name` lub `user.email`. | Komunikat gita; narzędzie nie ustawia ich samo, REQ-VCS-017. |

### UC-VCS-06 — Commit & Push

1. Użytkownik wpisuje wiadomość i wybiera Commit & Push.
2. System wykonuje UC-VCS-05 kroki 2–3.
3. System wykonuje push bieżącej gałęzi do upstreamu w tle.
4. System pokazuje wynik i odświeża repo.

| Krok | Warunek | Reakcja |
|---|---|---|
| 2a | Commit się nie udał. | Jak UC-VCS-05 2a; push nie startuje. |
| 3a | Brak upstreamu. | REQ-VCS-013. |
| 3b | Push odrzucony (non-fast-forward, brak uprawnień, sieć). | REQ-VCS-012; zależy od Q-VCS-003. |
| 3c | Wymagane uwierzytelnienie, którego git nie ma. | Komunikat zamiast zawieszenia, REQ-VCS-014. |
| 3d | Detached HEAD. | Push nieaktywny, UC-VCS-02 2b. |

### UC-VCS-07 — Pull

v1, tryb fast-forward only, DEC-VCS-014 i DEC-VCS-018.

1. Użytkownik wybiera Pull dla wybranego repo.
2. System pobiera zmiany z upstreamu bieżącej gałęzi w tle i przesuwa gałąź lokalną.
3. System pokazuje wynik i odświeża repo.

| Krok | Warunek | Reakcja |
|---|---|---|
| 1a | Brak upstreamu lub detached HEAD. | Pull nieaktywny, z podaną przyczyną. |
| 2a | Gałęzie się rozjechały (fast-forward niemożliwy). | Komunikat gita; repo bez zmian; v1 nie robi merge ani rebase. |
| 2b | Lokalne niecommitowane zmiany kolidują z pobieranymi. | Git odmawia; komunikat; kopia robocza bez zmian. |
| 2c | Brak uwierzytelnienia lub sieci. | Komunikat zamiast zawieszenia, jak REQ-VCS-014. |

## Śledzenie powiązań (DEC-VCS-031)

Cel: z każdego wymagania da się dojść do projektu, testów i kodu (kierunek w przód), a z każdego testu i modułu kodu z powrotem do wymagania (kierunek wstecz). Program sprawdzający pilnuje tego automatycznie, a niezgodność oblewa testy.

```
NEED ─► REQ ─► DES ─► kod (moduł)
         │      ▲         ▲
         ├─► AT ┼─► test ─┘
         └─► VER┘
```

### Stan 2026-10-21 przed wprowadzeniem reguł (OBS-VCS-006)

| ID | Obserwacja | Dowód |
|---|---|---|
| OBS-VCS-006 | Wszystkie odwołania zapisane pełnym ID wskazują istniejące definicje. 44 odwołania używają jednak skrótów (`REQ-VCS-005–008`, `REQ-VCS-003, REQ-VCS-004, REQ-VCS-007`), których program nie rozwinie bez reguł; przez to np. REQ-VCS-004 wygląda na nieobecny w DESIGN.md, choć jest tam jako `REQ-VCS-003–004`. 10 wymagań nie ma żadnego scenariusza AT: REQ-VCS-002, REQ-VCS-008, REQ-VCS-013, REQ-VCS-015, REQ-VCS-016, REQ-VCS-019, REQ-VCS-023, REQ-VCS-101, REQ-VCS-102, REQ-VCS-103. VER-VCS-001–005 opisują temat słowami zamiast ID wymagań. DES-VCS-030 odwołuje się do sekcji, a nie do ID. Kierunek wstecz (test → AT/REQ, kod → DES/REQ) jeszcze nie istnieje, bo nie ma testów ani kodu. | Doraźny skrypt agenta poza repo, uruchomiony na SPEC.md, DESIGN.md i ACCEPTANCE.feature. |
| OBS-VCS-007 | Stan 2026-10-21 po wdrożeniu programu sprawdzającego (DES-VCS-040): 20 testów przechodzi (8 reguł na prawdziwych dokumentach i 12 testów samego programu). Program znalazł i agent naprawił: podwójną definicję Q-VCS-009 (nagłówek i wiersz rejestru); 23 niedozwolone skróty, przepisane automatycznie na pełne ID; odwołanie do niezdefiniowanego DES-VCS-040; wymagania bez AT, VER lub DES; wiersze DES-VCS-006, DES-VCS-007, DES-VCS-031 i DES-VCS-032 bez REQ ani DEC. Agent dodał: ID wymagań w VER-VCS-001–006, wiersze VER-VCS-012–014 i DES-VCS-040, powiązania REQ w DES-VCS-006, DES-VCS-007 i DES-VCS-034. Przy okazji wyszły dwa błędy samego programu (status i wyjątek „bez DES:” rozpoznawane w dowolnym miejscu tekstu), poprawione i pokryte testem. Przed startem TDD 28 scenariuszy `@confirmed` bez testów jest tylko ostrzeżeniem w TRACE.md. | `.venv/bin/python -m pytest packages/vcs_lite/tests` w byte-brewery, Python 3.12.11, pytest 9.0.2. |
| OBS-VCS-008 | Ręczne próby 2026-10-21 prawdziwego `bcomp` (BC4 4.4.7) przez `CommandTemplateDiffTool` z domyślnym poleceniem DES-VCS-037: lewa strona z bajtów (plik tymczasowy `0o444`), prawa to plik na dysku. Trzy próby: okno otwarte 179 s, 29 s i 8 s; kody wyjścia 111, 13 i 1; stderr zawsze pusty, więc `failed=False` (DES-VCS-039). Pliki tymczasowe za każdym razem usunięte. Użytkownik potwierdził, że tytuły `-title1=`/`-title2=` są widoczne i że lewa strona jest zablokowana. W trzeciej próbie zapis prawej strony zmienił plik na dysku; jego treść stała się równa lewej stronie, bo użytkownik skopiował lewą stronę na prawą (potwierdzone: „skopiowalem lewa na prawa i zamknalem okno”). Kod wyjścia nie odróżnia błędu od wyniku porównania. | Skrypt agenta w scratchpadzie, `vcs_lite.core.difftool.compare`; odpowiedzi użytkownika „1: tak 2: tak”. |

### Reguły (zaakceptowane, DEC-VCS-043)

| ID | Reguła | Status |
|---|---|---|
| REQ-VCS-200 | Każde ID ma dokładnie jedną definicję: wiersz tabeli zaczynający się od ID, nagłówek UC albo tag `@AT_VCS_nnn` w `ACCEPTANCE.feature`. | Potwierdzone, DEC-VCS-043 |
| REQ-VCS-201 | Odwołania zapisuje się pełnym ID. Dopuszczalny jest tylko zakres z półpauzą między dwoma pełnymi numerami tego samego typu (`REQ-VCS-005–008`); listy samych numerów (`003, 004`) są zabronione. Istniejące 44 skróty zostaną przepisane. | Potwierdzone, DEC-VCS-043 |
| REQ-VCS-202 | W przód: każde REQ ma co najmniej jeden AT albo VER oraz co najmniej jeden DES. Wyjątki są jawnie wpisane w wierszu wymagania jako „bez DES: <powód>”. | Potwierdzone, DEC-VCS-043 |
| REQ-VCS-203 | Wstecz z dokumentów: każdy AT ma tag REQ, każdy VER i DES wskazuje co najmniej jedno REQ lub DEC. | Potwierdzone, DEC-VCS-043 |
| REQ-VCS-204 | Wstecz z testów: nazwa każdego testu zaczyna się od ID, które pokrywa, np. `test_at_vcs_010_…`, `test_req_vcs_005_…`, `test_t_vcs_01_…`. Test bez ID albo z nieistniejącym ID oblewa sprawdzenie. Zgodne z DEC-VCS-029. | Potwierdzone, DEC-VCS-043 |
| REQ-VCS-205 | W przód do testów: każdy AT ze statusem `@confirmed` ma test o swojej nazwie. Do czasu napisania testu AT jest raportowany jako „bez testu”, a sprawdzenie nie oblewa; po wejściu w TDD brak testu oblewa. | Potwierdzone, DEC-VCS-043; szczegół: oblewa od startu TDD, DEC-VCS-037 |
| REQ-VCS-206 | Wstecz z kodu: docstring każdego modułu w `src/vcs_lite/` zawiera linię `Trace: DES-VCS-…, REQ-VCS-…`. Moduł bez niej albo z nieistniejącym ID oblewa sprawdzenie. | Potwierdzone, DEC-VCS-043; szczegół: tylko moduły, DEC-VCS-036 |
| REQ-VCS-207 | Program sprawdzający działa jako test pytest (`tests/test_traceability.py`) i generuje `TRACE.md`: macierz REQ → DES, AT, VER, testy, moduły oraz listę odwrotną. `TRACE.md` jest generowany, nie edytowany ręcznie. | Potwierdzone, DEC-VCS-043; miejsce: `packages/vcs_lite/tests/`, DEC-VCS-038 |

## Weryfikacja

| ID | Co weryfikuje | Metoda | Scenariusze |
|---|---|---|---|
| VER-VCS-001 | REQ-VCS-003, REQ-VCS-004, REQ-VCS-007, REQ-VCS-008, REQ-VCS-019: grupowanie statusów (T-VCS-01), pliki binarne i kodowanie | Testy jednostkowe warstwy gita na tymczasowym repo; po jednym przypadku na wiersz T-VCS-01. | AT-VCS-003–007 |
| VER-VCS-002 | REQ-VCS-005: stage i unstage całych plików | Test na tymczasowym repo. | AT-VCS-008–009 |
| VER-VCS-003 | REQ-VCS-009, REQ-VCS-010: commit i obsługa odrzucenia | Test na tymczasowym repo z hookiem `pre-commit`. | AT-VCS-010–012 |
| VER-VCS-004 | REQ-VCS-011, REQ-VCS-012, REQ-VCS-013, REQ-VCS-014: push | Test z lokalnym bare repo jako `origin`. | AT-VCS-013–015 |
| VER-VCS-005 | REQ-VCS-001, REQ-VCS-018: Settings, trwałość wyboru, repo niedostępne | Test na tymczasowym `rootdir`. | AT-VCS-001–002 |
| VER-VCS-006 | REQ-VCS-100, REQ-VCS-101, REQ-VCS-102: pamięć, brak pracy w tle, czas odświeżenia | Pomiar `footprint` i czasu odświeżenia (DES-VCS-034); licznik wywołań `git` w bezczynności (DES-VCS-035). | AT-VCS-016 |
| VER-VCS-007 | REQ-VCS-017 | Porównanie stanu `.git` przed i po samym przeglądaniu. | AT-VCS-017 |
| VER-VCS-008 | REQ-VCS-001 (pierwszy poziom), REQ-VCS-021 | Test na tymczasowym `rootdir` z repo zagnieżdżonym i dwoma repo obserwowanymi. | AT-VCS-018–019 |
| VER-VCS-009 | REQ-VCS-020 | Test z lokalnym bare repo jako `origin`. | AT-VCS-020–021 |
| VER-VCS-011 | REQ-VCS-023 | Test z adapterem testowym w miejscu Beyond Compare: zapisuje otrzymane polecenie i ścieżki, a test sprawdza treść stron i sprzątanie. Ręcznie: jedno porównanie w prawdziwym `bcomp`. | AT-VCS-004, AT-VCS-025–027 |
| VER-VCS-012 | REQ-VCS-002, REQ-VCS-015, REQ-VCS-016, REQ-VCS-021: lista repo, odświeżanie, blokada równoległych operacji, akcje na wybranym repo | Testy `AppModel` bez Tk (DES-VCS-032) na tymczasowych repo. | AT-VCS-019, AT-VCS-023 |
| VER-VCS-013 | REQ-VCS-103: uruchomienie | Ręcznie: `uv run vcs-lite` w katalogu byte-brewery otwiera okno E-01 na macOS z Apple Silicon. | — |
| VER-VCS-014 | REQ-VCS-200–207: śledzenie powiązań w obie strony | `tests/test_traceability.py`: reguły na prawdziwych dokumentach i testy samego programu sprawdzającego na małych przykładach. | — |
| VER-VCS-010 | REQ-VCS-001 (ukrywanie), REQ-VCS-022 | Test na tymczasowym `rootdir`; test przełączania repo. | AT-VCS-022–023 |

Testy noszą w nazwie identyfikator REQ, np. `test_req_vcs_005_stage_whole_file`.

## Definition of Done v1

- Wszystkie scenariusze AT oznaczone `@confirmed` przechodzą automatycznie, a wymagania `PROPOZYCJA` są potwierdzone albo skreślone.
- Pomiar VER-VCS-006 spełnia REQ-VCS-100 i jest zapisany z datą, wersją Pythona i Tk.
- Narzędzie uruchamia się jedną komendą i przez tydzień zastępuje PyCharm w przeglądaniu i commitowaniu zmian w repo obserwowanych.
- Rejestr pytań nie ma pytań blokujących v1.

## Rejestr pytań

| ID | Pytanie | Status | Co od niego zależy |
|---|---|---|---|
| Q-VCS-001 | Jak głęboko skanować `rootdir`: tylko bezpośrednie podfoldery czy też repo zagnieżdżone (np. `docs` i `docs/sessions`)? | ROZSTRZYGNIĘTE 2026-10-21: tylko pierwszy poziom, DEC-VCS-007. | REQ-VCS-001 |
| Q-VCS-001b | Czy w Settings pokazywać podfoldery `rootdir`, które nie są repo gita (oznaczone i niezaznaczalne), czy je ukrywać? Propozycja agenta: ukrywać. | ROZSTRZYGNIĘTE 2026-10-21: ukryć, DEC-VCS-016. | UC-VCS-01 2b |
| Q-VCS-002 | Czy commit i push dotyczą zawsze jednego, aktualnie wybranego repo? | ROZSTRZYGNIĘTE 2026-10-21: tak, DEC-VCS-008. | REQ-VCS-021 |
| Q-VCS-003 | Czy przy odrzuconym pushu commit zostaje, a narzędzie tylko pokazuje błąd, bez automatycznego pull i rebase? | ROZSTRZYGNIĘTE 2026-10-21: tak, plus osobny przycisk Pull, DEC-VCS-009. | REQ-VCS-012, REQ-VCS-020 |
| Q-VCS-004 | Czy Discard wchodzi do v1? | ROZSTRZYGNIĘTE 2026-10-21: bez Discard, DEC-VCS-010. | OUT |
| Q-VCS-005 | Gdzie zapisać specyfikację? | ROZSTRZYGNIĘTE 2026-10-21: byte-brewery, DEC-VCS-005. | — |
| Q-VCS-006 | Czy zatwierdzasz stos: Python 3.14 z uv (Tk 9.0.4) + Tkinter/ttk, git przez CLI, bez zewnętrznych zależności? | ROZSTRZYGNIĘTE 2026-10-21: zatwierdzony, DEC-VCS-012. | REQ-VCS-103 |
| Q-VCS-007 | Czy próg 60 MB dla REQ-VCS-100 jest właściwy? | ROZSTRZYGNIĘTE 2026-10-21: tak, DEC-VCS-013. | REQ-VCS-100 |
| Q-VCS-008 | Czy pozycje OUT zaproponowane przez agenta zostają poza v1? | ROZSTRZYGNIĘTE 2026-10-21: tak, v2, DEC-VCS-011. | OUT |
| Q-VCS-009 | Jak ma wyglądać wygodny interfejs pracy na jednym repo naraz? Warianty A, B i C poniżej; rekomendacja agenta: A. | ROZSTRZYGNIĘTE 2026-10-21: A, DEC-VCS-015. | REQ-VCS-021–022, E-01 |
| Q-VCS-010 | Pull: v1 czy v2? Odpowiedź na Q-VCS-003 dodaje przycisk Pull, a odpowiedź na Q-VCS-008 przenosi pull/fetch do v2. Jeśli v1: w jakim trybie? Propozycja agenta: fast-forward only (`git pull --ff-only`), bez merge i rebase. | ROZSTRZYGNIĘTE 2026-10-21: tryb fast-forward only, DEC-VCS-014; termin w Q-VCS-010b. | REQ-VCS-020, UC-VCS-07 |
| Q-VCS-010b | Czy Pull fast-forward wchodzi do v1, czy do v2? Odpowiedź „10 pull fast-forward” podała tryb, bez terminu; odpowiedź 08 przenosi pull/fetch do v2. | ROZSTRZYGNIĘTE 2026-10-21: v1, DEC-VCS-018. Wcześniej agent przedwcześnie przyjął v1 i wycofał to. | REQ-VCS-020, UC-VCS-07, AT-VCS-020–021 |
| Q-VCS-011 | Czy zatwierdzasz pozostałe propozycje agenta: DEC-VCS-006 (nieśledzone pliki pojedynczo), REQ-VCS-003 (grupa Conflicts), REQ-VCS-004 (ukrywanie ignorowanych), REQ-VCS-007 (limit 1 MB lub 20 000 linii), REQ-VCS-008 (znaki zastępcze), REQ-VCS-013 (pytanie o upstream), REQ-VCS-019 (blokada commita przy konflikcie), REQ-VCS-102 (odświeżenie < 1 s), UC-VCS-02 2b (detached HEAD)? | ROZSTRZYGNIĘTE 2026-10-21: tak, DEC-VCS-017. | DoD |
| Q-VCS-012 | Czy dodać przycisk „Otwórz w PyCharm” (zewnętrzne narzędzie diffu z edycją kopii roboczej) obok wbudowanego diffu tylko do odczytu? Jeśli tak: v1 czy v2, i co robić, gdy PyCharm nie działa? Ustalenia z rozpoznania: OBS-VCS-001–004. | ODŁOŻONE DO v2 2026-10-21: nie w v1, pytanie wraca przy planowaniu v2, DEC-VCS-019. Następnie 2026-10-21 CZĘŚCIOWO ROZSTRZYGNIĘTE dla Beyond Compare: DEC-VCS-024. Dane: OBS-VCS-003 (PyCharm ok. 690 MB), OBS-VCS-005 (BC4 ok. 235 MB). | DEC-VCS-002, REQ-VCS-023 |
| Q-VCS-012b | Czy zewnętrzny diff (Beyond Compare przez adapter) wchodzi do v1, czy do v2? | ROZSTRZYGNIĘTE 2026-10-21: v1, DEC-VCS-034. | REQ-VCS-023, DES-VCS-036 |
| Q-VCS-012c | Jaka relacja do wbudowanego diffu: (a) wbudowany diff zostaje, a zewnętrzny otwiera się przyciskiem lub dwuklikiem; (b) zewnętrzny zastępuje wbudowany? Rekomendacja agenta: (a), bo wbudowany kosztuje mało i nie wymaga Rosetty. | ROZSTRZYGNIĘTE 2026-10-21: (b), BC zastępuje wbudowany, DEC-VCS-035. | REQ-VCS-006, REQ-VCS-023 |
| Q-VCS-014 | Commit specyfikacji w byte-brewery: teraz czy później razem z kodem? | ROZSTRZYGNIĘTE 2026-10-21: teraz, DEC-VCS-023. | — |
| Q-VCS-015 | Wariant uruchomienia: (a) `uv run vcs-lite` w środowisku workspace (obecnie Python 3.12.11, Tk 8.6) czy (b) `uv tool install --python 3.14` (Python 3.14.7, Tk 9.0.4, zgodnie z DEC-VCS-012)? Rekomendacja agenta: (b), bo Tk 9 lepiej obsługuje macOS, a workspace zostaje bez zmian. | ROZSTRZYGNIĘTE 2026-10-21: (a), DEC-VCS-025. | DES-VCS-029, REQ-VCS-103, DEC-VCS-012 |
| Q-VCS-016 | Czy przy braku własnej konfiguracji ssh wymuszać `BatchMode=yes`, żeby ssh nie czekał na hasło do klucza? Rekomendacja agenta: tak. | ROZSTRZYGNIĘTE 2026-10-21: tak, DEC-VCS-026. | DES-VCS-004, REQ-VCS-014 |
| Q-VCS-017 | Czy pomijać ukryte podkatalogi `rootdir` (zaczynające się od kropki)? Rekomendacja agenta: tak. | ROZSTRZYGNIĘTE 2026-10-21: tak, DEC-VCS-027. | DES-VCS-020, REQ-VCS-001 |
| Q-VCS-018 | Czy poprawne kolory w trybie ciemnym macOS są wymagane w v1? | ROZSTRZYGNIĘTE 2026-10-21: nie, DEC-VCS-028. | DES-VCS-027 |
| Q-VCS-019 | Jak wykonywać `ACCEPTANCE.feature`: (a) `pytest-bdd` jako zależność deweloperska, która uruchamia plik `.feature` bezpośrednio, czy (b) zwykłe testy pytest nazwane ID scenariuszy, a plik `.feature` jako dokumentacja? Rekomendacja agenta: (b), bez nowej zależności; (a) daje pewność, że plik i testy się nie rozjadą. | ROZSTRZYGNIĘTE 2026-10-21: (b), DEC-VCS-029. | DES-VCS-033 |
| Q-VCS-020 | Powtórzenie pytań z punktu 3, na które odpowiedź „3: nie” była niejednoznaczna: (1) czy zmierzyć RAM Sublime Merge, Kaleidoscope i Meld (wymaga instalacji przez `brew install --cask`)? (2) czy rozważyć Sublime Merge zamiast budowy vcs-lite? | ROZSTRZYGNIĘTE 2026-10-21: (1) nie, DEC-VCS-032; (2) nie, DEC-VCS-033. | — |
| Q-VCS-021 | Granularność śledzenia w kodzie (REQ-VCS-206): docstring modułu wystarcza, czy także funkcje i klasy? Rekomendacja agenta: moduł, bo funkcje szybko się zmieniają, a moduły w DESIGN.md mają jasne odpowiedzialności. | ROZSTRZYGNIĘTE 2026-10-21: tylko moduły, DEC-VCS-036. | REQ-VCS-206 |
| Q-VCS-022 | Czy brak testu dla AT `@confirmed` ma oblewać sprawdzenie od razu, czy dopiero od wejścia w TDD (REQ-VCS-205)? Rekomendacja agenta: od wejścia w TDD; wcześniej tylko raport. | ROZSTRZYGNIĘTE 2026-10-21: od startu TDD, DEC-VCS-037. | REQ-VCS-205 |
| Q-VCS-023 | Gdzie ma żyć program sprawdzający i dokumenty? Program wymaga pakietu z `pyproject.toml`, więc rekomendacja agenta: utworzyć teraz szkielet `packages/vcs_lite/` (tylko `pyproject.toml`, `tests/test_traceability.py`, pusty `src/vcs_lite/__init__.py`) i przenieść tam `docs/vcs-lite/` jako `packages/vcs_lite/docs/`, zgodnie z zapowiedzią w DEC-VCS-005. | ROZSTRZYGNIĘTE 2026-10-21: tak, wykonane, DEC-VCS-038. | REQ-VCS-207, DEC-VCS-005 |
| Q-VCS-024 | DEC-VCS-002 mówi „diff tylko do odczytu w v1”, a Beyond Compare pozwala edytować stronę kopii roboczej i zapisać plik. Co obowiązuje: (a) edycja kopii roboczej dozwolona (zmienia DEC-VCS-002), (b) tylko do odczytu: obie strony jako pliki tymczasowe `0o444`? Rekomendacja agenta: (a), bo edycję w diffie oceniłeś pozytywnie przy PyCharmie. | ROZSTRZYGNIĘTE 2026-10-21: (a), DEC-VCS-039. | DEC-VCS-002, DES-VCS-038, UC-VCS-03 2e |
| Q-VCS-025 | Co otwiera porównanie w Beyond Compare? DES-VCS-024 przypisał dwuklik do stage/unstage. Rekomendacja agenta: dwuklik lub Enter otwiera porównanie (jak w PyCharmie), a stage/unstage to spacja i menu kontekstowe. | ROZSTRZYGNIĘTE 2026-10-21: jak w rekomendacji, DEC-VCS-040. | DES-VCS-024, UC-VCS-03 |
| Q-VCS-026 | Co z REQ-VCS-007 (binarne i duże pliki) i REQ-VCS-008 (kodowanie), które dotyczyły wbudowanego diffu? Rekomendacja agenta: wycofać oba i przekazywać każdy plik do Beyond Compare, które samo porównuje pliki binarne i różne kodowania. | ROZSTRZYGNIĘTE 2026-10-21: zostawić, DEC-VCS-041; zakres w v1 w Q-VCS-029. | REQ-VCS-007, REQ-VCS-008, DES-VCS-008 |
| Q-VCS-027 | REQ-VCS-100 mierzy pamięć „z otwartym diffem pliku 2000 linii”. Czy limit 60 MB dotyczy teraz tylko procesu vcs-lite, a Beyond Compare (ok. 235 MB, OBS-VCS-005) liczy się osobno? Rekomendacja agenta: tak. | ROZSTRZYGNIĘTE 2026-10-21: tak, DEC-VCS-042. | REQ-VCS-100, DES-VCS-034, AT-VCS-016 |
| Q-VCS-028 | Czy akceptujesz reguły śledzenia powiązań REQ-VCS-200–207 jako całość? Odpowiedzi na Q-VCS-021–023 dotyczyły szczegółów, a pytanie o całość zostało bez odpowiedzi. | ROZSTRZYGNIĘTE 2026-10-21: tak, DEC-VCS-043. | REQ-VCS-200–207 |
| Q-VCS-029 | REQ-VCS-007 i REQ-VCS-008 zostają (DEC-VCS-041). Co oznaczają w v1, gdy diff robi Beyond Compare? (a) Uśpione: obowiązują dopiero, gdy wróci wbudowany lub inny diff; w v1 każdy plik trafia do BC. (b) Obowiązują od razu: vcs-lite nie otwiera BC dla plików binarnych i ponad 1 MB lub 20 000 linii, tylko pokazuje komunikat. Rekomendacja agenta: (a), bo BC dobrze porównuje pliki binarne i duże, a wymagania czekają gotowe na wypadek jego wycofania. | ROZSTRZYGNIĘTE 2026-10-21: (a), DEC-VCS-044. | REQ-VCS-007, REQ-VCS-008, DES-VCS-008, AT-VCS-007 |
| Q-VCS-013 | Czy szkic wiadomości commita (REQ-VCS-022) ma przetrwać zamknięcie narzędzia, czy wystarczy, że przetrwa przełączanie repo w trakcie pracy? | ROZSTRZYGNIĘTE 2026-10-21: wystarczy przełączanie repo, DEC-VCS-020. | REQ-VCS-022 |

### Warianty interfejsu jednego repo (Q-VCS-009)

| Wariant | Opis | Za | Przeciw |
|---|---|---|---|
| **A. Master–detail** (rekomendacja) | Lista repo po lewej z licznikami zmian; po prawej pliki, diff i panel commita wyłącznie wybranego repo. Przycisk pokazuje cel: „Commit do byte-brewery”. Każde repo ma własny szkic wiadomości, zachowany przy przełączaniu. Skróty: ⌘1–⌘9 wybór repo, ⌘↩ Commit, ⌘⇧↩ Commit & Push. | Zgodny ze szkicem E-01; nie da się pomylić repo; najmniej kodu. | Pliki widać tylko z jednego repo naraz. |
| B. Zakładki | Każde repo obserwowane to zakładka u góry okna; reszta jak w A. | Znany wzorzec. | Przy wielu repo zakładki się ścieśniają; liczniki zmian mniej widoczne. |
| C. Jedno drzewo | Drzewo repo → grupy → pliki dla wszystkich repo, jak PyCharm przy wielu rootach. Panel commita działa na repo zaznaczonego węzła; pliki innych repo są wtedy wyszarzone. | Wszystkie zmiany widać naraz. | Łatwo pomylić docelowe repo; więcej stanów do obsłużenia i przetestowania. |

## Obserwacje: diff PyCharma z CLI

Rozpoznanie z 2026-10-21 na tym Macu, PyCharm 2025.3.4 (build 253.32098.74).

| ID | Obserwacja | Dowód |
|---|---|---|
| OBS-VCS-001 | Polecenie `/Applications/PyCharm.app/Contents/MacOS/pycharm diff <lewy> <prawy>` działa. Przy uruchomionym PyCharmie przekazuje porównanie do działającej instancji, która otwiera okno diffu. W PATH nie ma polecenia `pycharm`; trzeba podać pełną ścieżkę albo utworzyć dowiązanie. | `idea.log`: „External command line: diff …” i „Processing command with com.intellij.diff.applications.DiffApplication”. |
| OBS-VCS-002 | Proces uruchamiający czeka, aż użytkownik zamknie okno diffu, i w tym czasie sam jest maszyną JVM zajmującą ok. 113 MB. Działający PyCharm zajmował ok. 1,8 GB razem z procesami pomocniczymi. | `footprint` procesów 47555 (1569 MB) i 49149 (113 MB) oraz procesy `cef_server`. |
| OBS-VCS-003 | Bez działającego PyCharma polecenie uruchamia jeden proces IDE z pełnym zestawem wtyczek (m.in. Augment, Docker, Mermaid), bez otwierania projektu. Pamięć: ok. 520 MB po 2 s, ok. 690 MB po 5 s, potem stabilnie 690–700 MB przez 65 s pomiaru. To ok. 12 razy więcej niż próg REQ-VCS-100. Okno diffu się otwiera, a prawą stronę (plik z dysku) można edytować; potwierdził użytkownik. | Pomiar 2026-10-21 21:57, `footprint` co 2 s; użytkownik potwierdził 690 MB w Monitorze aktywności. `idea.log`: „AppStarter - args: diff …”, „Loaded custom plugins: … Augment …”. |
| OBS-VCS-004 | Pliki otwarte w diffie PyCharma widzi wtyczka Augment, zgłaszając je jako otwarte pliki edytora. FileMerge (`opendiff`) jest niedostępny, bo zainstalowane są tylko Command Line Tools, bez Xcode. | `idea.log`: „Augment … No root found for file: /private/tmp/…”; brak `/Applications/Xcode*.app`. |
| OBS-VCS-005 | Beyond Compare 4.4.7.28397 (licencja użytkownika: BC4 Standard, Multi Platform). Serwer Scooter Software był 2026-10-21 w konserwacji: wszystkie pliki przekierowywały na `maintenance.html`. Instalator pobrany z Wayback Machine (zrzut 2026-01-11 oficjalnego `scootersoftware.com/files/BCompareOSX-4.4.7.28397.zip`); SHA-256 `a9ba4cea125bbfe00fa3e79de39937197ae5d479d94710f5b93da5bda377a0ce`. Podpis `Developer ID Application: Scooter Software Inc. (BS29TEJF86)`, notaryzowany, Gatekeeper `accepted`. Binarka tylko x86_64, czyli działa przez Rosettę. Osobny program porównania: `Contents/MacOS/bcomp`, czeka na zamknięcie okna. Pamięć przy `bcomp` na dwóch plikach po 2000 linii: ok. 13 s do stabilizacji, potem 231–236 MB (`BCompare` ok. 231 MB + `bcomp` 4 MB) przez 30 s pomiaru. Wersja Standard nie ma merge 3-stronnego. | `codesign`, `spctl`, `stapler`, `lipo -archs`; `footprint` co 2 s, 2026-10-21 ok. 22:20. Użytkownik potwierdził 2026-10-21, że okno diffu się otworzyło i działało. |

## Punkt wznowienia

2026-10-21: specyfikacja, projekt i reguły śledzenia zaakceptowane (DEC-VCS-001–044); rejestr pytań bez otwartych pozycji. TDD rozpoczęte (`TDD_STARTED = True`): gotowa warstwa `core`: `status.py`, `difftool.py`, `gitcli.py`, `repo.py`, `settings.py` (89 testów). Test REQ-VCS-205 oblewa celowo: potwierdzone AT bez testów są na poziomie `AppModel` (DEC-VCS-037). Następny krok według DESIGN.md: `app/model.py` i `app/worker.py`.
