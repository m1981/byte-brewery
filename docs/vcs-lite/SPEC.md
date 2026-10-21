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
- Repozytoria zagnieżdżone głębiej niż pierwszy poziom `rootdir`, DEC-VCS-007.
- Commit i push kilku repozytoriów jedną akcją, DEC-VCS-008.
- **Backlog v2**, DEC-VCS-011: amend, fetch, merge i rozwiązywanie konfliktów, tworzenie i przełączanie gałęzi, historia i log, stash, zarządzanie submodułami, zmiana `rootdir` z poziomu interfejsu, Windows i Linux. Pull w trybie innym niż fast-forward only (merge, rebase), DEC-VCS-014. Przycisk „Otwórz w PyCharm”: pytanie Q-VCS-012 wraca przy planowaniu v2, DEC-VCS-019.

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
| DEC-VCS-002 | Diff w v1 tylko do odczytu. | Użytkownik 2026-10-21: „2 diff tylko do odczytu w v1”. REQ-VCS-006. |
| DEC-VCS-003 | Lista wielu repozytoriów, wybieranych w Settings checkboxami spośród folderów w `rootdir = ~/PycharmProjects`. | Użytkownik 2026-10-21: „3 lista kilku repozytorow po wejsciu w sttings (wybieram z checkboxami foldery w rootdir= ~/PycharmProjects”. REQ-VCS-001–002; szczegóły skanu w Q-VCS-001. |
| DEC-VCS-004 | Odrzucone rozwiązania TUI, w tym lazygit z delta. Narzędzie ma okno graficzne. | Użytkownik 2026-10-21 o lazygit + delta: „probowalem i odrzucam”. |
| DEC-VCS-005 | Specyfikacja żyje w repo byte-brewery, w `docs/vcs-lite/`. | Użytkownik 2026-10-21: „zapisz wymagania ~/PycharmProjects/byte-brewery”. Wybór katalogu jest decyzją agenta: workspace uv obejmuje `packages/*` i odrzuca folder bez `pyproject.toml` (sprawdzone uv 0.8.13: „Workspace member … is missing a `pyproject.toml`”). Przeniesienie do `packages/vcs_lite/` wraz z kodem. |
| DEC-VCS-006 | Pliki nieśledzone pokazywać pojedynczo, także wewnątrz nowych katalogów (`--untracked-files=all`), tak jak PyCharm. | Wybór agenta wynikający z NEED-VCS-002; zatwierdzone DEC-VCS-017. |
| DEC-VCS-007 | Repozytoria szukane tylko na pierwszym poziomie `rootdir`, bez zagnieżdżonych. | Użytkownik 2026-10-21: „01 nit tylko piwerwsza poziom”. Q-VCS-001, REQ-VCS-001. Nie rozstrzyga pokazywania folderów niebędących repo, Q-VCS-001b. |
| DEC-VCS-008 | Commit i push dotyczą zawsze jednego repozytorium naraz. Interfejs wyboru repo do commita trzeba zaprojektować tak, żeby był wygodny. | Użytkownik 2026-10-21: „tak commit/push tylko dla jednego repo na raz (trzeba przmeyslec jak zrobic wygodne GUI do tego)”. Q-VCS-002, REQ-VCS-021; projekt interfejsu w Q-VCS-009. |
| DEC-VCS-009 | Odrzucony push zostawia commit; narzędzie pokazuje błąd i nie robi automatycznie pull ani rebase. Pull to osobny przycisk, uruchamiany wyłącznie przez użytkownika. | Użytkownik 2026-10-21: „03: tak. Pull jako osobny guzik”. Q-VCS-003, REQ-VCS-012, REQ-VCS-020. Termin i tryb pull w Q-VCS-010. |
| DEC-VCS-010 | Bez Discard. | Użytkownik 2026-10-21: „04: bez discard”. Q-VCS-004, OUT. |
| DEC-VCS-011 | Pozycje OUT zaproponowane przez agenta zostają poza v1 i trafiają do v2. | Użytkownik 2026-10-21: „08: zostaja i zorbimy w v2”. Q-VCS-008, OUT. |
| DEC-VCS-012 | Stos: Python 3.14 z uv (Tk 9.0.4), Tkinter/ttk, git przez CLI, bez zewnętrznych zależności. | Użytkownik 2026-10-21: „06: zatwierdzam”. Q-VCS-006, REQ-VCS-103. |
| DEC-VCS-013 | Próg pamięci 60 MB. | Użytkownik 2026-10-21: „07: tak 60MB jest super”. Q-VCS-007, REQ-VCS-100. |
| DEC-VCS-014 | Pull działa w trybie fast-forward only; bez merge i rebase. | Użytkownik 2026-10-21: „10 pull fast-forward”. Q-VCS-010, REQ-VCS-020, UC-VCS-07. Termin: v1, DEC-VCS-018. |
| DEC-VCS-015 | Interfejs jednego repo: wariant A, master–detail. | Użytkownik 2026-10-21: „09: A”. Q-VCS-009, REQ-VCS-021–022, E-01. |
| DEC-VCS-016 | Podfoldery `rootdir`, które nie są repo gita, są w Settings ukryte. | Użytkownik 2026-10-21: „01b: ukryc”. Q-VCS-001b, REQ-VCS-001, UC-VCS-01 2b. |
| DEC-VCS-018 | Pull fast-forward wchodzi do v1. | Użytkownik 2026-10-21: „10b: pull fast forward w v1”. Q-VCS-010b, REQ-VCS-020, UC-VCS-07. |
| DEC-VCS-019 | Bez przycisku „Otwórz w PyCharm” w v1. Pytanie wraca przy planowaniu v2. | Użytkownik 2026-10-21: „12: nie” oraz „690MB to wstrzymajmy do wersji v2 niech wroci to pytanie”. Q-VCS-012, OBS-VCS-001–004. |
| DEC-VCS-020 | Szkic wiadomości commita przetrwa przełączanie repo; nie musi przetrwać zamknięcia narzędzia. | Użytkownik 2026-10-21: „13: wystarczy ze przetrwa przelaczenie repo”. Q-VCS-013, REQ-VCS-022. |
| DEC-VCS-017 | Zatwierdzone wszystkie propozycje z Q-VCS-011: DEC-VCS-006, REQ-VCS-003, 004, 007, 008, 013, 019, 102 i UC-VCS-02 2b. | Użytkownik 2026-10-21: „11: tak”. |

## Wymagania funkcjonalne

| ID | Wymaganie | Status | Powiązania |
|---|---|---|---|
| REQ-VCS-001 | Settings pokazuje bezpośrednie podfoldery `rootdir` z checkboxem przy każdym; głębszych poziomów nie przeszukuje. Wybór przetrwa zamknięcie i ponowne uruchomienie narzędzia. | Potwierdzone; foldery niebędące repo są ukryte. | DEC-VCS-003, DEC-VCS-007, DEC-VCS-016, UC-VCS-01 |
| REQ-VCS-002 | Okno główne pokazuje listę repo obserwowanych z liczbą zmienionych plików i nazwą bieżącej gałęzi. Wybór repo pokazuje jego grupy plików. | Potwierdzone | NEED-VCS-004, UC-VCS-02 |
| REQ-VCS-003 | Pliki wybranego repo są pogrupowane w Staged, Changes, Unversioned i Conflicts według tabeli T-VCS-01. Pusta grupa jest ukryta lub oznaczona jako pusta. | Potwierdzone, DEC-VCS-017 | T-VCS-01 |
| REQ-VCS-004 | Pliki ignorowane przez `.gitignore` nie są pokazywane. | Potwierdzone, DEC-VCS-017 | T-VCS-01 |
| REQ-VCS-005 | Użytkownik może przenieść cały plik z Changes lub Unversioned do Staged (stage) i ze Staged z powrotem (unstage). Dotyczy to także usunięć i zmian nazwy. | Potwierdzone | DEC-VCS-001, T-VCS-01, UC-VCS-04 |
| REQ-VCS-006 | Wybór pliku pokazuje diff lewo–prawo, tylko do odczytu: numery linii, wyróżnienie linii dodanych, usuniętych i zmienionych, wyrównanie odpowiadających sobie linii, wspólne przewijanie obu stron. Strony diffu według T-VCS-01. | Potwierdzone | DEC-VCS-002, UC-VCS-03 |
| REQ-VCS-007 | Dla pliku binarnego lub przekraczającego limit rozmiaru narzędzie pokazuje komunikat zamiast diffu. Stage i unstage nadal działają. | Potwierdzone; limit 1 MB lub 20 000 linii, DEC-VCS-017. | UC-VCS-03 |
| REQ-VCS-008 | Tekst w kodowaniu innym niż UTF-8 jest pokazywany ze znakami zastępczymi. Narzędzie nigdy nie zmienia treści pliku. | Potwierdzone, DEC-VCS-017 | UC-VCS-03 |
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

## Wymagania jakościowe

| ID | Wymaganie | Miara i metoda | Status |
|---|---|---|---|
| REQ-VCS-100 | Niskie zużycie pamięci. | `Footprint` z `footprint <pid>` (to samo co kolumna Memory w Monitorze aktywności), po 5 s bezczynności. Warunki: 3 repo obserwowane, 300 zmienionych plików w jednym z nich, otwarty diff pliku 2000 linii. **Cel: ≤ 60 MB.** Punkt odniesienia: prototyp okna Tk o tym kształcie, zmierzony 2026-10-21, zajął 38 MB (Python 3.14.7, Tk 9.0.4). | Potwierdzone, DEC-VCS-013 |
| REQ-VCS-101 | Brak pracy w tle podczas bezczynności. | Brak cyklicznych wywołań `git` i timerów odpytujących, gdy okno nie ma fokusu i nic nie jest w trakcie. Sprawdzenie logiem wywołań `git`. | Potwierdzone |
| REQ-VCS-102 | Szybkie odświeżenie stanu. | Odświeżenie repo z 300 zmienionymi plikami trwa < 1 s na Apple Silicon. | Potwierdzone, DEC-VCS-017 |
| REQ-VCS-103 | Platforma i uruchomienie. | macOS na Apple Silicon, stos według DEC-VCS-012. Uruchomienie jedną komendą z terminala. | Potwierdzone |

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

E-01, okno główne (szkic, nie projekt graficzny):

```
┌ Repozytoria ──┬ Pliki ─────────────────┬ Diff (tylko do odczytu) ────────────────┐
│ ● byte-brew 4 │ ▾ Staged (1)           │  12 def foo(x):     │  12 def foo(x):    │
│   docs     12 │     src/app.py         │  13 -   return x*2  │  13 +   return x*3 │
│   kitchen   0 │ ▾ Changes (2)          │  14                 │  14                │
│               │     README.md          │                     │                    │
│               │     src/app.py         │                     │                    │
│               │ ▾ Unversioned (1)      │                     │                    │
│ [Settings]    │     notes.txt          │                     │                    │
├───────────────┴────────────────────────┴─────────────────────────────────────────┤
│ byte-brewery · main → origin/main  [ wiadomość ... ] [Commit] [Commit & Push] [Pull] [Refresh] │
└──────────────────────────────────────────────────────────────────────────────────┘
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

### UC-VCS-03 — Zobacz diff pliku

1. Użytkownik wybiera plik w jednej z grup.
2. System pokazuje diff lewo–prawo według T-VCS-01 i REQ-VCS-006.

| Krok | Warunek | Reakcja |
|---|---|---|
| 2a | Plik binarny lub ponad limit. | Komunikat zamiast diffu, REQ-VCS-007. |
| 2b | Kodowanie inne niż UTF-8. | Znaki zastępcze, REQ-VCS-008. |
| 2c | Plik zniknął z dysku między odświeżeniem a wyborem. | Komunikat i odświeżenie repo. |
| 2d | Plik w Staged i Changes. | Strony diffu wynikają z grupy, w której kliknięto. |

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

## Weryfikacja

| ID | Co weryfikuje | Metoda | Scenariusze |
|---|---|---|---|
| VER-VCS-001 | Grupowanie statusów i strony diffu | Testy jednostkowe warstwy gita na tymczasowym repo; po jednym przypadku na wiersz T-VCS-01. | AT-VCS-003–007 |
| VER-VCS-002 | Stage i unstage całych plików | Test na tymczasowym repo. | AT-VCS-008–009 |
| VER-VCS-003 | Commit i obsługa odrzucenia | Test na tymczasowym repo z hookiem `pre-commit`. | AT-VCS-010–012 |
| VER-VCS-004 | Push | Test z lokalnym bare repo jako `origin`. | AT-VCS-013–015 |
| VER-VCS-005 | Settings i trwałość wyboru | Test na tymczasowym `rootdir`. | AT-VCS-001–002 |
| VER-VCS-006 | REQ-VCS-100 | Pomiar `footprint` w opisanych warunkach. | AT-VCS-016 |
| VER-VCS-007 | REQ-VCS-017 | Porównanie stanu `.git` przed i po samym przeglądaniu. | AT-VCS-017 |
| VER-VCS-008 | REQ-VCS-001 (pierwszy poziom), REQ-VCS-021 | Test na tymczasowym `rootdir` z repo zagnieżdżonym i dwoma repo obserwowanymi. | AT-VCS-018–019 |
| VER-VCS-009 | REQ-VCS-020 | Test z lokalnym bare repo jako `origin`. | AT-VCS-020–021 |
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
| Q-VCS-012 | Czy dodać przycisk „Otwórz w PyCharm” (zewnętrzne narzędzie diffu z edycją kopii roboczej) obok wbudowanego diffu tylko do odczytu? Jeśli tak: v1 czy v2, i co robić, gdy PyCharm nie działa? Ustalenia z rozpoznania: OBS-VCS-001–004. | ODŁOŻONE DO v2 2026-10-21: nie w v1, pytanie wraca przy planowaniu v2, DEC-VCS-019. | DEC-VCS-002, backlog v2 |
| Q-VCS-013 | Czy szkic wiadomości commita (REQ-VCS-022) ma przetrwać zamknięcie narzędzia, czy wystarczy, że przetrwa przełączanie repo w trakcie pracy? | ROZSTRZYGNIĘTE 2026-10-21: wystarczy przełączanie repo, DEC-VCS-020. | REQ-VCS-022 |

### Q-VCS-009 — warianty interfejsu jednego repo

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

## Punkt wznowienia

2026-10-21: założono specyfikację (DEC-VCS-001–005), a następnie wpisano odpowiedzi na Q-VCS-001–004 i 006–008 (DEC-VCS-007–013). Potem wpisano odpowiedzi na Q-VCS-001b, 009, 010 i 011 (DEC-VCS-014–017) i rozpoznano diff PyCharma (OBS-VCS-001–004, w tym pomiar od zera). Na koniec wpisano DEC-VCS-018–020; użytkownik potwierdził okno i edycję w OBS-VCS-003. Rejestr nie ma pytań otwartych dla v1; Q-VCS-012 czeka na planowanie v2. Następny krok: projekt techniczny, po zgodzie użytkownika.
