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
- **Backlog v2**, DEC-VCS-011: amend, fetch, merge i rozwiązywanie konfliktów, tworzenie i przełączanie gałęzi, historia i log, stash, zarządzanie submodułami, zmiana `rootdir` z poziomu interfejsu, Windows i Linux. Pull w trybie innym niż fast-forward only (merge, rebase), DEC-VCS-014. PyCharm jako narzędzie diffu (ok. 690 MB), DEC-VCS-019. Wykrywanie i kończenie trwającego rebase i cherry-pick, DEC-VCS-065.

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
| DEC-VCS-045 | Wygląd okna według makiety A („pasek boczny macOS”) jako wzorca: `docs/ui-reference/E-01.html`, zrzut `E-01.png` i `UI-REFERENCE.md` ze wszystkimi wartościami (kolory, czcionki, rozmiary, odstępy, stany, teksty). Zastępuje szkic ASCII E-01. Makiety B i C w `docs/ui-mockups/` zostają jako odrzucone alternatywy. | Użytkownik 2026-10-21: „1 A jest cudowny zapisz html i wszystkie elementy jako referecnyjne, nie pomin niczego wlacznie z czcionka, kolorami, odstepami itp.”; zrzut makiety od użytkownika. DES-VCS-042. |
| DEC-VCS-046 | Bez licznika linii „+12 −3” (`git diff --numstat`) zaproponowanego w makiecie C. | Użytkownik 2026-10-21: „2: pomijamy”. |
| DEC-VCS-047 | Podejście mieszane: pasek boczny, chipy, liczniki, kwadraty statusu i lista plików rysowane wiernie wzorcowi (`tk.Canvas`, `PhotoImage`); przyciski natywne `ttk` w motywie aqua (przycisk główny jako przycisk domyślny). | Użytkownik 2026-10-22: „1: C” na Q-VCS-030. DES-VCS-042. |
| DEC-VCS-048 | Bez wykrywania trwającego merge, rebase ani cherry-pick w v1: repo w konflikcie ma w drugiej linii samą gałąź, a konflikt sygnalizuje czerwony znacznik „konflikt”. Zmienione przez DEC-VCS-065 (wykrywanie merge) i DEC-VCS-069 (druga linia „main · merge”). | Użytkownik 2026-10-22: „2: B” na Q-VCS-031. Zmienia wzorzec „main · merge” w UI-REFERENCE.md. |
| DEC-VCS-049 | Zaakceptowane propozycje stanów okna P2–P10 z makiety `a-states.html`: chip konfliktu, pasek błędu, wskaźnik operacji w toku, cztery puste stany, repo czyste bez licznika, podpowiedź UNVERSIONED, okno „Repozytoria do obserwowania” (E-02), natywne pytanie o upstream z nową treścią, odłączony HEAD. Wartości w `ui-reference/UI-REFERENCE.md`, sekcja 8. | Użytkownik 2026-10-22: „P2: ok P3: super P4: super P5: super wszystkie P6: super P7: super P8: super P9: super P10: super”. Q-VCS-032. P1 nierozstrzygnięte: Q-VCS-033. |
| DEC-VCS-050 | Plik w konflikcie można oznaczyć jako rozwiązany spacją, ale tylko gdy nie zawiera już znaczników konfliktu (wariant b). Dotyczy też wyglądu z P1: grupa CONFLICTS na górze listy, kwadrat „!” w `conf`, nagłówek grupy w `conf`. | Użytkownik 2026-10-22: „P1: b wykonaj rzetelnie” na Q-VCS-033. REQ-VCS-024, DES-VCS-044, T-VCS-01. |
| DEC-VCS-051 | Podpowiedź przy plikach w STAGED: „spacja unstage · dwuklik porównaj”, bo dwuklik porównuje tam HEAD z indeksem (T-VCS-01). Zmienia wzorzec E-01, który miał samo „spacja unstage”. | Użytkownik 2026-10-22: „dodaj dwuklik”. |
| DEC-VCS-052 | Kolory statusu plików jak w PyCharmie, odczytane ze zrzutów użytkownika: zmieniony `#002daa`, dodany `#0c7216`, poza kontrolą `#a92c3e`; dobrane przez agenta: przeniesiony `#002daa`, usunięty `#6e6e73` z przekreśleniem; konflikt bez zmian `#c2302a`. Kropka „zmiany” w pasku bocznym bez zmian. | Użytkownik 2026-10-22: „K1 ok” (makieta `ui-mockups/a-pycharm-colors.html`). |
| DEC-VCS-053 | Lista plików bez kwadratów statusu, sam kolor nazwy jak w PyCharmie; zwięźlejsze wiersze (mniejsza wysokość linii). | Użytkownik 2026-10-22: „K2 bez kwadratow jak w Pycharm (…) musze to miec zwiezle i czytelnie (…) Zmniejsz odstep miedzy liniami tekstu/ line height”. Zastępuje kwadraty z §4 wzorca i P1 („!”). |
| DEC-VCS-054 | Nazwa pliku zwykłą czcionką w kolorze statusu; najpierw nazwa, za nią szary folder; zmiana nazwy jako „nowa ← stara”. | Użytkownik 2026-10-22: „K3: tak K4: tak”. |
| DEC-VCS-055 | Widok folderów (jeden węzeł na katalog z pełną ścieżką, liczba plików, zwijanie) włączany natywnym polem „Pokaż foldery” w pasku narzędzi; stan zapamiętany w ustawieniach, wspólny dla repo. | Użytkownik 2026-10-22: „F1: tak F2: tak”. REQ-VCS-025. |
| DEC-VCS-056 | Stage całego folderu: przycisk „+” pojawiający się przy węźle folderu pod kursorem, jak w PyCharmie. | Użytkownik 2026-10-22: „Dodaj funckje stageowania calych folderow (+) na zrzucie on sie pojawia jak onHover jak przejzdzam prze linie nazwy folderu”; „F3: dodaj stage folderow jak pisalem wczesniej”. REQ-VCS-026. Szczegóły: DEC-VCS-057. |
| DEC-VCS-057 | Szczegóły listy plików z Q-VCS-034: wiersze i nagłówki grup po 24 pt; najpierw foldery, potem pliki z katalogu głównego; „+” w Changes i Unversioned, „−” w Staged, bez przycisku w Conflicts; spacja na węźle folderu działa jak przycisk, dwuklik zwija i rozwija; wiersze plików z podpowiedzią zamiast „+”. Wzorzec: `ui-reference/E-01-lista.html`, UI-REFERENCE.md §9. | Użytkownik 2026-10-22: „q34 wszystko tak”. |
| DEC-VCS-058 | W oknie Repozytoria repo wybrane wcześniej, a nieobecne na dysku, są na końcu listy: zaznaczone, wyszarzone, z dopiskiem „niedostępne”; odznaczenie usuwa je z listy. Zapisz nie usuwa ich po cichu. | Użytkownik 2026-10-22: „1: akceptuje kontunuuj” na propozycję agenta. REQ-VCS-018, E-02. |
| DEC-VCS-059 | Odświeżanie po fokusie tylko po powrocie z innej aplikacji: `<FocusIn>` okna planuje odświeżenie (opóźnienie 300 ms) wyłącznie wtedy, gdy wcześniej fokus opuścił aplikację. Przenoszenie fokusu między elementami okna nie odświeża. | Użytkownik 2026-10-22: „Q3: a” na Q-VCS-036. DES-VCS-018, REQ-VCS-015. |
| DEC-VCS-060 | Test AT-VCS-016 działa w zwykłym przebiegu testów: osobny proces z prawdziwym, widocznym oknem; 3 repo, jedno z 300 zmianami; porównanie pliku 2000 linii otwarte w atrapie narzędzia diffu; `footprint` po 5 s bezczynności. Skrypt da się też uruchomić ręcznie z prawdziwym `bcomp`. | Użytkownik 2026-10-22: „Q4: ok” na Q-VCS-037. DES-VCS-034, REQ-VCS-100. |
| DEC-VCS-061 | REQ-VCS-102 ma własny test z progiem 1 s: mediana kilku odświeżeń po odrzuceniu pierwszego (zimnego). | Użytkownik 2026-10-22: „Q5: propozycja ok” na Q-VCS-038. DES-VCS-034. |
| DEC-VCS-062 | Wynik pomiaru VER-VCS-006 (data, wersje Pythona, Tk, macOS i gita) trafia do SPEC.md jako obserwacja OBS po kroku 13 `MANUAL-UI.md`. Test niczego nie zapisuje w repo. | Użytkownik 2026-10-22: „Q6: ok” na Q-VCS-039. DES-VCS-034, REQ-VCS-100. |
| DEC-VCS-063 | Wywołania gita obserwowane z zewnątrz procesu: zmienna środowiskowa `VCS_LITE_GIT_LOG=<plik>` włącza dziennik (jedna linia JSON na wywołanie); bez niej nic nie jest zapisywane. Testy procesowe i pomiary według praktyk z refleksji agenta: sygnał gotowości zamiast `sleep`, limity czasu, sprzątanie grupy procesów, dane maszynowe z `footprint -j`, pomiar oddzielony od oceny. Tekst projektu do akceptacji: Q-VCS-044. | Użytkownik 2026-10-22: „Q7: a (zrob refleksje jako senior SW developer i tester rozwiazan dzilajacych na procesach i pomiarach …)” na Q-VCS-040. REQ-VCS-101, DES-VCS-035. |
| DEC-VCS-064 | Pasek błędu P3 z zaokrągleniem 8 rysowany na `tk.Canvas`; wykonanie po UI-7. | Użytkownik 2026-10-22: „Q8: tak i po” na Q-VCS-041. UI-REFERENCE.md §8 P3, DES-VCS-042. |
| DEC-VCS-065 | Wykrywanie trwającego merge (`MERGE_HEAD`). Gdy merge trwa, a żaden plik nie jest w konflikcie, Commit jest możliwy także przy pustym Staged i kończy merge; repo nie jest pokazywane jako czyste. Rebase i cherry-pick bez zmian, backlog v2. Wygląd nowego stanu: makieta P11 do akceptacji, Q-VCS-043. Zmienia częściowo DEC-VCS-048. | Użytkownik 2026-10-22: „Q9: a” na Q-VCS-042; OBS-VCS-010. REQ-VCS-027, DES-VCS-046. |
| DEC-VCS-066 | Krok 11 `MANUAL-UI.md`: Commit & Push i Pull z przesunięciem gałęzi na repo demo `beta` (agent dodaje commit do `remotes/beta.git` po pushu, przed Pull); dodatkowo sam Pull w prawdziwym, czystym repo `kuchnie2` w drugim oknie z osobnym plikiem ustawień w scratchpadzie. Bez Commit & Push na prawdziwych repo. | Użytkownik 2026-10-22: „35: ok” na Q-VCS-035. REQ-VCS-020, REQ-VCS-014. |
| DEC-VCS-067 | Tekst projektu pomiaru i dziennika gita zaakceptowany: DES-VCS-034 (zmieniony) i DES-VCS-047. | Użytkownik 2026-10-22: „44: akceptuje” na Q-VCS-044. DEC-VCS-063. |
| DEC-VCS-068 | Wygląd stanu „merge gotowy do commita” według makiety `ui-reference/E-01-scalanie.html` (P11a, P11b): niebieski chip „merge gotowy do commita” w pasku narzędzi zamiast chipa P2, kropka „zmiany”, pusty stan „Merge gotowy do commita”, Commit aktywny po wpisaniu wiadomości. | Użytkownik 2026-10-22: „P11a i P11b tak” na Q-VCS-043. REQ-VCS-027, UI-REFERENCE.md §8 P11. |
| DEC-VCS-069 | W trakcie merge druga linia repo w pasku bocznym to „main · merge”, także przy konfliktach, jak na pierwotnym wzorcu `E-01.png` (P11c). Konflikty bez merge pokazują samą gałąź. Zmienia DEC-VCS-048. | Użytkownik 2026-10-22: „11c tak” na Q-VCS-043. REQ-VCS-027, UI-REFERENCE.md §4. |
| DEC-VCS-070 | Repo bez zdalnego `origin`: Commit & Push zostaje aktywny jak dotąd; po zgodzie z pytania P9 push kończy się komunikatem gita w pasku błędu P3. Bez dodatkowego sprawdzania `origin`. | Użytkownik 2026-10-22: „D1 nie zostanie jak jest” na Q-VCS-045. REQ-VCS-013. |
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
| REQ-VCS-024 | Spacja na pliku w grupie Conflicts oznacza go jako rozwiązany: `git add`, a gdy pliku nie ma w kopii roboczej, `git rm`. Warunek: plik nie zawiera linii zaczynającej się od `<<<<<<<`, `>>>>>>>` ani `|||||||`. Jeśli zawiera, narzędzie pokazuje komunikat z nazwą pliku i numerem pierwszej takiej linii i nie zmienia repozytorium. Commit pozostaje zablokowany, dopóki jakikolwiek plik jest w konflikcie (REQ-VCS-019). | Potwierdzone, DEC-VCS-050 | T-VCS-01, UC-VCS-04, DES-VCS-044 |
| REQ-VCS-025 | Pole „Pokaż foldery” przełącza listę plików między widokiem płaskim a widokiem folderów. W widoku folderów każda grupa zbiera pliki pod węzłami katalogów (pełna ścieżka katalogu, liczba plików); węzeł można zwinąć i rozwinąć. Stan pola przetrwa ponowne uruchomienie. | Potwierdzone, DEC-VCS-055 | DES-VCS-045, UI-REFERENCE.md §9 |
| REQ-VCS-026 | Węzeł folderu pod kursorem pokazuje przycisk, który wykonuje operację na wszystkich plikach folderu w tej grupie naraz: stage w Changes i Unversioned. Dotyczy całych plików (DEC-VCS-001). | Potwierdzone, DEC-VCS-056, DEC-VCS-057 | DES-VCS-045, UI-REFERENCE.md §9 |
| REQ-VCS-027 | Gdy w repo trwa merge (istnieje `MERGE_HEAD`), a żaden plik nie jest w Conflicts, Commit jest aktywny po wpisaniu wiadomości także przy pustym Staged i tworzy commit scalający. Repo w tym stanie nie jest pokazywane jako czyste ani jako „Brak zmian”. | Potwierdzone, DEC-VCS-065; wygląd P11, DEC-VCS-068, DEC-VCS-069. | UC-VCS-05, S-VCS-01, DES-VCS-046 |

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
| `u` | Conflicts | Oznacz jako rozwiązany (REQ-VCS-024) | brak w v1, komunikat o konflikcie |
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
| SCALANIE | Trwa merge (`MERGE_HEAD`), brak wpisów `u`. | Jak ZMIANY; commit także przy pustym Staged, kończy merge, REQ-VCS-027. |

Po operacji zawsze następuje odświeżenie i przejście do stanu wynikającego z warunków. Błąd operacji jest komunikatem przy repo, a nie osobnym stanem.

## Ekrany

E-01, okno główne. **Wzorcem wyglądu jest `docs/ui-reference/` (DEC-VCS-045); poniższy szkic ASCII pokazuje tylko pierwotny podział i nie jest już wiążący.** Diff otwiera się w Beyond Compare (DEC-VCS-035), więc okno nie ma panelu diffu:

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
| 2c | Plik w grupie Conflicts. | Oznaczenie jako rozwiązany według REQ-VCS-024; przy znacznikach konfliktu komunikat z numerem linii, repo bez zmian. |

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
| OBS-VCS-009 | W środowisku `.venv` byte-brewery (Python 3.12.11 z uv, python-build-standalone) `import tkinter` działa, ale `tkinter.Tk()` kończy się błędem „Can't find a usable init.tcl”. Biblioteki Tcl/Tk są w Pythonie bazowym (`lib/tcl8.6`, `lib/tk8.6`). Z ustawionymi `TCL_LIBRARY` i `TK_LIBRARY` Tk 8.6.14 startuje; ten sam Python poza venv działa bez nich. Rozwiązanie: DES-VCS-041. | Sprawdzone 2026-10-21 poleceniami `.venv/bin/python -c "tkinter.Tk()"` z i bez zmiennych. |
| OBS-VCS-010 | Krok 14 `MANUAL-UI.md` 2026-10-22 na repo demo `gamma`: po usunięciu znaczników z `f.txt` (zostawiona strona „ours”, czyli treść równa HEAD) spacja wykonała `git add` zgodnie z REQ-VCS-024. Indeks stał się równy HEAD, więc `git status --porcelain=v2` nie zgłosił żadnego wpisu: vcs-lite pokazał `gamma` jako czyste („Brak zmian”), a Commit był nieaktywny („Brak plików w Staged.”). Git w tym czasie: „All conflicts fixed but you are still merging”, `MERGE_HEAD` obecny. Merge nie dawał się zakończyć z vcs-lite. Przy treści różnej od HEAD plik trafia do Staged i commit kończy merge. Rozwiązanie: DEC-VCS-065. | Zrzut użytkownika po spacji; `git status` w `gamma`. |
| OBS-VCS-011 | Pomiar automatyczny VER-VCS-006 2026-10-22 16:31 (`tests/measure_footprint.py`, atrapa narzędzia diffu): 3 repo, 300 zmian, otwarte porównanie pliku 2000 linii. Footprint procesu vcs-lite w 5 s bezczynności: 45,7–45,9 MB (maksimum 45,9; limit 60, REQ-VCS-100). Odświeżenie repo z 300 zmianami: mediana 0,064 s z 5 pomiarów (limit 1 s, REQ-VCS-102). Wywołania gita w bezczynności: 0, przed gotowością 11 (REQ-VCS-101). Python 3.12.11, Tk 8.6.14, macOS 26.2, git 2.47.1, kod `c41a1ab-dirty`. Pomiar z prawdziwym Beyond Compare: krok 13. | Wynik JSON skryptu; testy `tests/test_footprint.py` przechodzą. |
| OBS-VCS-012 | Krok 13 `MANUAL-UI.md` 2026-10-22 na żywym oknie (repo demo, dziennik `VCS_LITE_GIT_LOG`, DES-VCS-047): porównanie `README.md` z `alpha` otwarte w prawdziwym Beyond Compare, okno bez fokusu. Footprint vcs-lite 40,1 MB (limit 60, REQ-VCS-100); Beyond Compare osobno 127 MB (DEC-VCS-042). W dzienniku 5 wywołań gita: 3 × `status` przy starcie, `status` i `cat-file` przy wyborze `alpha` i otwarciu porównania; potem 106 s bez żadnego wywołania (REQ-VCS-101). Python 3.12.11, Tk 8.6.14, macOS 26.2. | `footprint -j`, dziennik gita, `pgrep -lP` (dziecko `bcomp`). |

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
| VER-VCS-002 | REQ-VCS-005, REQ-VCS-024: stage i unstage całych plików, oznaczanie konfliktu jako rozwiązanego | Test na tymczasowym repo, w tym konflikty ze znacznikami, bez znaczników, z nagłówkiem Markdown `=======` i rozwiązane przez usunięcie. | AT-VCS-008–009, AT-VCS-030–031 |
| VER-VCS-003 | REQ-VCS-009, REQ-VCS-010, REQ-VCS-027: commit, obsługa odrzucenia i zakończenie merge | Test na tymczasowym repo z hookiem `pre-commit` oraz z merge rozwiązanym do treści HEAD. | AT-VCS-010–012 |
| VER-VCS-004 | REQ-VCS-011, REQ-VCS-012, REQ-VCS-013, REQ-VCS-014: push | Test z lokalnym bare repo jako `origin`. | AT-VCS-013–015 |
| VER-VCS-005 | REQ-VCS-001, REQ-VCS-018: Settings, trwałość wyboru, repo niedostępne | Test na tymczasowym `rootdir`. | AT-VCS-001–002 |
| VER-VCS-006 | REQ-VCS-100, REQ-VCS-101, REQ-VCS-102: pamięć, brak pracy w tle, czas odświeżenia | Pomiar `footprint` i czasu odświeżenia (DES-VCS-034); licznik wywołań `git` w bezczynności (DES-VCS-035). | AT-VCS-016 |
| VER-VCS-007 | REQ-VCS-017 | Porównanie stanu `.git` przed i po samym przeglądaniu. | AT-VCS-017 |
| VER-VCS-008 | REQ-VCS-001 (pierwszy poziom), REQ-VCS-021 | Test na tymczasowym `rootdir` z repo zagnieżdżonym i dwoma repo obserwowanymi. | AT-VCS-018–019 |
| VER-VCS-009 | REQ-VCS-020 | Test z lokalnym bare repo jako `origin`. | AT-VCS-020–021 |
| VER-VCS-011 | REQ-VCS-023 | Test z adapterem testowym w miejscu Beyond Compare: zapisuje otrzymane polecenie i ścieżki, a test sprawdza treść stron i sprzątanie. Ręcznie: jedno porównanie w prawdziwym `bcomp`. | AT-VCS-004, AT-VCS-025–027 |
| VER-VCS-012 | REQ-VCS-002, REQ-VCS-015, REQ-VCS-016, REQ-VCS-021: lista repo, odświeżanie, blokada równoległych operacji, akcje na wybranym repo | Testy `AppModel` bez Tk (DES-VCS-032) na tymczasowych repo. | AT-VCS-019, AT-VCS-023 |
| VER-VCS-013 | REQ-VCS-103: uruchomienie i wygląd okna | Ręcznie według `docs/MANUAL-UI.md` (13 kroków z punktami zrzutów ekranu); w tym `uv run vcs-lite` w katalogu byte-brewery otwiera okno E-01 na macOS z Apple Silicon. | — |
| VER-VCS-014 | REQ-VCS-200–207: śledzenie powiązań w obie strony | `tests/test_traceability.py`: reguły na prawdziwych dokumentach i testy samego programu sprawdzającego na małych przykładach. | — |
| VER-VCS-015 | REQ-VCS-025, REQ-VCS-026: widok folderów, stage i unstage folderu | Testy `AppModel` i okna na tymczasowych repo; ręcznie według `MANUAL-UI.md`. | AT-VCS-032–033 |
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
| Q-VCS-030 | Wierność wzorcowi czy natywne widżety? (a) Pełna wierność: przyciski i lista plików rysowane na `tk.Canvas` z kolorami, promieniami i odstępami z `UI-REFERENCE.md`. (b) Natywne: `ttk` w motywie aqua dla przycisków i listy; wygląd macOS, ale kolory przycisków i zaokrąglenia wierszy nie będą zgodne z wzorcem. (c) Mieszane: pasek boczny, chipy, liczniki i kwadraty statusu wierne (Canvas, obrazki), przyciski natywne aqua. Rekomendacja agenta: (c), bo największy efekt daje pasek boczny i lista, a natywne przyciski zachowują fokus, skróty i dostępność bez pisania ich od nowa. | ROZSTRZYGNIĘTE 2026-10-22: (c), DEC-VCS-047. | DES-VCS-042, UI-REFERENCE.md §5 |
| Q-VCS-031 | Na wzorcu repo w konflikcie ma drugą linię „main · merge”. Obecny model wie tylko, że są konflikty, nie że trwa merge (wymaga sprawdzenia `MERGE_HEAD`, `REBASE_HEAD` itp.). (a) Dodać wykrywanie trwającej operacji i pokazywać „merge”, „rebase”, „cherry-pick”. (b) Pokazywać tylko gałąź, a konflikt sygnalizować znacznikiem. Rekomendacja agenta: (b) w v1. | ROZSTRZYGNIĘTE 2026-10-22: (b), DEC-VCS-048. | UI-REFERENCE.md §4 |
| Q-VCS-032 | Elementy nieobecne na wzorcu i drobne rozbieżności: wiersze konfliktu (litera, kolor), komunikat błędu gita (miejsce i wygląd), wskaźnik operacji w toku, puste stany, licznik repo czystego, podpowiedź dla UNVERSIONED (porównanie też działa według T-VCS-01), okno Settings (E-02), okno pytania o upstream. Propozycja agenta: zaprojektować je w stylu wzorca jako dodatek do makiety `E-01.html` do akceptacji przed wdrożeniem. | ROZSTRZYGNIĘTE 2026-10-22 dla P2–P10 (DEC-VCS-049); P1 przeniesione do Q-VCS-033. | UI-REFERENCE.md §7 |
| Q-VCS-033 | P1: co można zrobić z plikiem w konflikcie? (a) Nic, jak dziś w T-VCS-01; podpowiedź „rozwiąż w edytorze, potem `git add <plik>` w terminalu”. (b) Spacja robi `git add`, czyli oznacza plik jako rozwiązany, ale tylko gdy w pliku nie ma już znaczników konfliktu (`<<<<<<<`, `=======`, `>>>>>>>`); w przeciwnym razie komunikat z numerem linii i nic się nie zmienia. (c) Spacja robi `git add` bez sprawdzania. Rekomendacja agenta: (b). | ROZSTRZYGNIĘTE 2026-10-22: (b), DEC-VCS-050. Doprecyzowanie agenta: sama linia `=======` nie jest znacznikiem, bo jest też podkreśleniem nagłówka w Markdownie (DES-VCS-044). | T-VCS-01, REQ-VCS-019 |
| Q-VCS-034 | Szczegóły widoku listy ustalone przez agenta do potwierdzenia (makieta `ui-mockups/a-list-final.html`): (1) wiersz 24 pt, zmierzony na zrzucie PyCharma użytkownika; nagłówek grupy też 24 pt; (2) węzły folderów przed plikami z katalogu głównego, jak na zrzucie; (3) w grupie Staged przycisk „−” (unstage całego folderu), w Changes i Unversioned „+”; w Conflicts bez przycisku; (4) spacja na węźle folderu działa jak przycisk; dwuklik zwija i rozwija; (5) wiersze plików bez przycisku „+”, z podpowiedzią klawiszy jak dotąd. | ROZSTRZYGNIĘTE 2026-10-22: wszystko tak, DEC-VCS-057. | REQ-VCS-025, REQ-VCS-026 |
| Q-VCS-035 | Krok 11 `MANUAL-UI.md`: jak sprawdzić Pull, skoro po samym pushu `origin` repo demo `beta` nie ma nic nowego? Odpowiedź „wybierz konkretne repo z ~/PycharmProjects/” jest niejednoznaczna wobec ryzyka pusha do prawdziwego serwera. Propozycja agenta do potwierdzenia: Commit & Push i Pull z przesunięciem gałęzi na demo `beta` (agent dodaje commit do `remotes/beta.git` przed Pull); dodatkowo sam Pull w czystym prawdziwym repo `kuchnie2` (bez zmian lokalnych, `origin` na GitHubie), w drugim oknie z osobnym plikiem ustawień w scratchpadzie. | ROZSTRZYGNIĘTE 2026-10-22: propozycja przyjęta, DEC-VCS-066. | MANUAL-UI.md krok 11, REQ-VCS-020 |
| Q-VCS-036 | Kiedy fokus ma odświeżać: (a) tylko po powrocie z innej aplikacji, (b) po każdym `<FocusIn>` z opóźnieniem 300 ms? | ROZSTRZYGNIĘTE 2026-10-22: (a), DEC-VCS-059. | DES-VCS-018, REQ-VCS-015 |
| Q-VCS-037 | Forma testu AT-VCS-016: osobny proces z prawdziwym oknem i atrapą narzędzia diffu w zwykłym przebiegu testów? | ROZSTRZYGNIĘTE 2026-10-22: tak, DEC-VCS-060. | DES-VCS-034 |
| Q-VCS-038 | Czy REQ-VCS-102 dostaje własny test z progiem 1 s? | ROZSTRZYGNIĘTE 2026-10-22: tak, DEC-VCS-061. | DES-VCS-034 |
| Q-VCS-039 | Gdzie zapisać wynik pomiaru z datą i wersjami? | ROZSTRZYGNIĘTE 2026-10-22: OBS w SPEC.md, DEC-VCS-062. | DES-VCS-034 |
| Q-VCS-040 | Jak w kroku 13 sprawdzić brak wywołań gita w bezczynności na żywym oknie: (a) dziennik włączany zmienną środowiskową, (b) podglądanie procesów potomnych? | ROZSTRZYGNIĘTE 2026-10-22: (a), DEC-VCS-063. | REQ-VCS-101 |
| Q-VCS-041 | Czy pasek błędu P3 rysować z zaokrągleniem 8 na `tk.Canvas`, i kiedy? | ROZSTRZYGNIĘTE 2026-10-22: tak, po UI-7, DEC-VCS-064. | UI-REFERENCE.md §8 P3 |
| Q-VCS-042 | Merge z wynikiem równym HEAD nie daje się zakończyć z vcs-lite (OBS-VCS-010): (a) wykrywać `MERGE_HEAD` i pozwolić na commit scalający, (b) jak (a) i wstawiać `MERGE_MSG`, (c) tylko opis ograniczenia? | ROZSTRZYGNIĘTE 2026-10-22: (a), DEC-VCS-065. | REQ-VCS-027 |
| Q-VCS-043 | Wygląd stanu „merge gotowy do commita” (P11): tekst pustego stanu, kropka i druga linia w pasku bocznym, przyczyna przy przycisku; przy okazji powrót do drugiej linii „main · merge” z oryginalnego wzorca (DEC-VCS-048). Agent przygotuje makietę w stylu `E-01-stany.html`. | ROZSTRZYGNIĘTE 2026-10-22: makieta `ui-reference/E-01-scalanie.html` przyjęta, DEC-VCS-068 i DEC-VCS-069. | REQ-VCS-027, UI-REFERENCE.md §8 |
| Q-VCS-044 | Akceptacja tekstu projektu dla DEC-VCS-063: rozszerzenie DES-VCS-034 (sygnał gotowości, limity czasu, `footprint -j`, próbki i maksimum, sprzątanie grupy procesów, mediana czasu) i nowy DES dziennika `VCS_LITE_GIT_LOG`. | ROZSTRZYGNIĘTE 2026-10-22: zaakceptowany, DEC-VCS-067. | DES-VCS-034, REQ-VCS-101 |
| Q-VCS-045 | Repo bez zdalnego `origin` (repo demo `epsilon`, 2026-10-22): Commit & Push pyta o push do `origin`, a push kończy się błędem „'origin' does not appear to be a git repository”. Czy Commit & Push i Pull mają być wtedy nieaktywne z przyczyną? | ROZSTRZYGNIĘTE 2026-10-22: nie, zostaje jak jest, DEC-VCS-070. | REQ-VCS-013 |
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

2026-10-22: specyfikacja, projekt, wzorzec wyglądu (`ui-reference/`, §1–§9) i reguły śledzenia zaakceptowane (DEC-VCS-001–065). Gotowe i przetestowane: `core`, `app`, UI-1 (szkielet), UI-2 (okno Repozytoria), UI-3 (pasek boczny, lista plików w stylu PyCharma, widok folderów), UI-4 (spacja, dwuklik, Beyond Compare), UI-5 (skróty ⌘↩, ⌘⇧↩, ⌘1–⌘9), UI-6 (pasek błędu P3, wskaźnik operacji P4, pytanie o upstream P9). 263 testy przechodzą (stan 2026-10-22 po UI-7).

Kroki `MANUAL-UI.md` potwierdzone przez użytkownika: 1–4, 10, 11 (Commit & Push i Pull w demo `beta`, Pull w `kuchnie2`), 14a, 15 oraz próby Beyond Compare (OBS-VCS-008). Krok 14b ujawnił OBS-VCS-010 (DEC-VCS-065); po wykonaniu REQ-VCS-027 powtórzony 2026-10-22: merge zakończony commitem scalającym. Przy powtórce wyszły dwa błędy, naprawione metodą TDD: pole wiadomości nie było czyszczone po commicie (REQ-VCS-009) i opis pustego stanu nie był zawijany do 46 znaków (P5). Obie poprawki potwierdzone zrzutem 2026-10-22 (repo demo `epsilon`). Krok 12 potwierdzony 2026-10-22 (odświeżanie po powrocie z innej aplikacji, DEC-VCS-059). Krok 13: OBS-VCS-012. Niepotwierdzone: 5–9.

Do oceny przy kroku 9: w czasie pytania P9 pole wiadomości jeszcze pokazuje treść zapisanego commita (model czyści szkic przed pytaniem, ale okno odrysowuje się dopiero po jego zamknięciu; zrzut 2026-10-22).

Chip P2 „N plików w konflikcie” dopisany 2026-10-22 (brakował od UI-6) i potwierdzony zrzutem; UI-6 zamknięte.

Następne kroki, w kolejności zaproponowanej przez agenta:
1. Wykonane: krok 11 według DEC-VCS-066.
2. Wykonane: chip P2.
3. DEC-VCS-065: makieta P11 `ui-reference/E-01-scalanie.html` przyjęta (DEC-VCS-068, DEC-VCS-069), po akceptacji REQ-VCS-027 metodą TDD i krok 14 jeszcze raz (repo demo `gamma` pozostawione w stanie OBS-VCS-010).
4. Wykonane: odświeżanie po fokusie (DEC-VCS-059), krok 12.
5. Wykonane poza krokiem 13 (OBS-VCS-011); wszystkie testy przechodzą, także REQ-VCS-205. UI-7: pomiar według DES-VCS-034 i DES-VCS-047: `tests/measure_footprint.py`, testy AT-VCS-016 i REQ-VCS-102, dziennik `VCS_LITE_GIT_LOG`; krok 13 i wynik jako OBS (DEC-VCS-062).
6. Pasek błędu z zaokrągleniem (DEC-VCS-064): wykonany metodą TDD 2026-10-22, czeka na zrzut.
7. VER-VCS-013: `uv run vcs-lite` (zainstaluje pakiet w `.venv` byte-brewery; zapytać użytkownika przed uruchomieniem).
8. Ręczne kroki 5–9 (UI-4, UI-5), dotąd niepotwierdzone.
