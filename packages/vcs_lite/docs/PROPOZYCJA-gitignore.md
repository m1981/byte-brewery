# vcs-lite — propozycja: menu kontekstowe i „Dodaj do .gitignore”

Status: propozycja agenta z 2026-10-22 do decyzji użytkownika (rejestr pytań w `SPEC.md`). Pomysł użytkownika: „menu kontekstowe: Dodaj do .gitignore, zarówno dla plików zaznaczonych z CTRL czy SHIFT, oraz folderów i ich kombinacji”. Przypadki testowe mają tu etykiety S-nn (zaznaczanie) i G-nn (menu i `.gitignore`); po akceptacji dostaną ID scenariuszy i wymagań.

## Stan wyjściowy

- Menu kontekstowego nie ma, choć obiecuje je zaakceptowana decyzja o stage i unstage przez „spację i menu kontekstowe” (DEC-VCS-040, DES-VCS-024). To luka niezależna od `.gitignore`.
- Lista ma jedno zaznaczenie naraz; nie ma zaznaczania wielu wierszy, więc to etap 1.
- REQ-VCS-017 zamyka listę operacji zmieniających repo (stage, unstage, commit, push, pull) i mówi, że narzędzie „nie tworzy plików w repo”. Zapis do `.gitignore` wymaga zmiany tego wymagania.

## Kolejność (uwaga użytkownika 2026-10-22: „To by wymagało najpierw napisania funkcjonalności zaznaczania elementów z SHIFT i CTRL i kombinacji zaznaczeń jak w Windows Explorer”)

1. Etap 1: zaznaczanie wielu wierszy jak w Eksploratorze Windows (poniżej, przypadki S-01–S-20).
2. Etap 2: menu kontekstowe z Stage, Unstage, Porównaj (domyka DEC-VCS-040).
3. Etap 3: „Dodaj do .gitignore” (przypadki G-01–G-19).

## Etap 1: zaznaczanie wielu wierszy (semantyka Eksploratora Windows)

Pojęcia: **zaznaczenie** (zbiór wierszy z tłem `accent-soft`), **kotwica** (początek zakresu dla Shift), **bieżący wiersz** (ten, na którym działają strzałki). Klawisz „Ctrl” poniżej oznacza w propozycji agenta zarówno Ctrl, jak i ⌘ (decyzja do potwierdzenia: na macOS Ctrl-kliknięcie zwykle otwiera menu kontekstowe, więc menu będzie wtedy tylko pod prawym przyciskiem i kliknięciem dwoma palcami).

| Działanie | Zaznaczenie | Kotwica | Bieżący |
|---|---|---|---|
| Kliknięcie | tylko ten wiersz | ten wiersz | ten wiersz |
| Ctrl-kliknięcie | przełącza ten wiersz, reszta bez zmian | ten wiersz | ten wiersz |
| Shift-kliknięcie | zakres kotwica–wiersz, poprzednie zaznaczenie znika | bez zmian | ten wiersz |
| Ctrl+Shift-kliknięcie | poprzednie zaznaczenie **plus** zakres kotwica–wiersz | bez zmian | ten wiersz |
| ↑ / ↓ | tylko następny/poprzedni wiersz | nowy wiersz | nowy wiersz |
| Shift+↑ / Shift+↓ | zakres kotwica–nowy bieżący | bez zmian | o jeden w górę/dół |
| Ctrl+↑ / Ctrl+↓ | bez zmian (przesuwa tylko bieżący, z ramką) | bez zmian | o jeden w górę/dół |
| Ctrl+spacja | przełącza bieżący wiersz | bieżący | bez zmian |
| Ctrl+A | wszystkie widoczne wiersze plików i folderów | bez zmian | bez zmian |
| Kliknięcie w puste miejsce listy | puste | brak | brak |

Dodatkowo:

- Zakres liczony w kolejności wyświetlania, także przez granice grup i przez węzły folderów; pliki zwiniętych folderów nie wchodzą do zakresu (są niewidoczne), węzeł folderu tak.
- Bieżący wiersz bez zaznaczenia (po Ctrl+↑/↓) ma ramkę 1 pt w `accent` zamiast tła.
- Spacja przy wielu zaznaczonych: gdy wszystkie są w jednej grupie, jedna operacja na wszystkich (jedno `git add` albo `git restore --staged`), potem zaznaczenie według REQ-VCS-028 za ostatnim z zaznaczonych; gdy w różnych grupach, nic.
- Dwuklik i Enter otwierają porównanie tylko klikniętego (bieżącego) pliku, nie całego zaznaczenia.
- Po odświeżeniu zaznaczenie zawiera tylko istniejące wiersze; gdy zniknęła kotwica, kotwicą zostaje bieżący wiersz.
- Przełączenie repo kasuje zaznaczenie.
- W trakcie operacji na repo zaznaczanie działa, akcje nie (REQ-VCS-016).

### Przypadki testowe etapu 1

| ID | Przypadek | Oczekiwany wynik |
|---|---|---|
| S-01 | Kliknięcie B po zaznaczeniu A i C | tylko B |
| S-02 | Ctrl-kliknięcie A, potem C | A i C |
| S-03 | Ctrl-kliknięcie na zaznaczonym A | A odznaczony, reszta zostaje |
| S-04 | Kliknięcie B, Shift-kliknięcie E | B–E |
| S-05 | Kliknięcie B, Shift-kliknięcie E, Shift-kliknięcie C | B–C (zakres od tej samej kotwicy B) |
| S-06 | Kliknięcie B, Shift-kliknięcie D, Ctrl-kliknięcie G, Ctrl+Shift-kliknięcie I | B–D oraz G–I |
| S-07 | Kliknięcie E, Shift-kliknięcie B (w górę) | B–E |
| S-08 | Zakres przez granicę Changes i Unversioned | wiersze obu grup, w kolejności wyświetlania |
| S-09 | Zakres przez zwinięty folder w widoku folderów | węzeł folderu tak, jego pliki nie |
| S-10 | Kliknięcie C, Shift+↓ dwa razy, Shift+↑ raz | C–D |
| S-11 | Ctrl+↓ dwa razy z C, potem Ctrl+spacja | zaznaczone C i E; bieżący E |
| S-12 | Ctrl+A | wszystkie widoczne wiersze |
| S-13 | Kliknięcie w puste miejsce pod listą | nic nie jest zaznaczone |
| S-14 | Spacja przy 3 zaznaczonych plikach z Unversioned | jedno `git add` z 3 plikami; zaznaczenie przechodzi za ostatni z nich |
| S-15 | Spacja przy zaznaczonych z Changes i Staged | nic się nie dzieje |
| S-16 | Dwuklik na jednym z kilku zaznaczonych | porównanie tylko tego pliku; zaznaczenie bez zmian |
| S-17 | Odświeżenie usuwa dwa z czterech zaznaczonych | zaznaczone dwa pozostałe |
| S-18 | Odświeżenie usuwa kotwicę, potem Shift-kliknięcie | zakres od bieżącego wiersza |
| S-19 | Przełączenie repo ⌘2 i powrót ⌘1 | nic nie jest zaznaczone |
| S-20 | Wiele zaznaczonych i kursor nad innym wierszem | tło `accent-soft` na wszystkich zaznaczonych, podpowiedź tylko pod kursorem (P12) |

## Etapy 2 i 3: menu kontekstowe i .gitignore

### Otwieranie menu

- Prawy przycisk albo kliknięcie dwoma palcami na gładziku (Ctrl-kliknięcie według decyzji o klawiszu Ctrl w etapie 1).
- Na wierszu spoza zaznaczenia: najpierw zaznacza tylko ten wiersz, potem otwiera menu dla niego (jak Eksplorator i Finder).
- Na wierszu z zaznaczenia: menu działa na całe zaznaczenie.

### Pozycje menu

| Pozycja | Kiedy aktywna |
|---|---|
| Stage (N) | wszystkie zaznaczone wiersze są w Changes albo Unversioned |
| Unstage (N) | wszystkie w Staged |
| Oznacz jako rozwiązany | jeden plik w Conflicts |
| Porównaj | dokładnie jeden plik, nie w Conflicts |
| — | |
| Dodaj do .gitignore (N) | wszystkie zaznaczone wiersze są w Unversioned (pliki albo węzły folderów); w pozostałych przypadkach pozycja jest widoczna i nieaktywna |

N to liczba wpisów, które powstaną (nie liczba wierszy), np. „Dodaj do .gitignore (3)”.

### Co jest zapisywane

- Zawsze do `.gitignore` w katalogu głównym repo; plik powstaje, gdy go nie ma.
- Wzorce zakotwiczone od katalogu głównego: plik `/ścieżka/plik.txt`, folder `/ścieżka/folder/`. Zakotwiczenie sprawia, że ignorowany jest dokładnie wskazany plik, a nie wszystkie o tej nazwie.
- Znaki specjalne gita są poprzedzane „\”: `*`, `?`, `[`, `]`, `\` oraz spacja na końcu. `#` i `!` nie potrzebują „\”, bo wzorzec zaczyna się od `/` (doprecyzowanie agenta przy wykonaniu, DES-VCS-048).
- Folder i plik w tym folderze zaznaczone razem: zapisywany jest tylko folder.
- Węzeł folderu, w którym są też pliki śledzone: zamiast `/folder/` zapisywane są wzorce samych plików nieśledzonych, żeby nie zmieniać zachowania nowych plików obok śledzonych.
- Wpis już obecny w `.gitignore` (ta sama linia) nie jest dopisywany drugi raz.
- Dopisywanie na końcu pliku; gdy plik nie kończy się znakiem nowej linii, najpierw jest on dodawany. Zakończenia linii CRLF zostają CRLF.
- Bez okna potwierdzenia; po zapisie lista się odświeża: wskazane pliki znikają z Unversioned, a `.gitignore` pojawia się w Changes (albo w Unversioned, gdy jest nowy).
- Błąd zapisu (np. plik tylko do odczytu): pasek błędu P3 „Dodanie do .gitignore nie powiodło się” z treścią błędu; `.gitignore` bez zmian.
- Operacja przez Worker jak stage (repo zajęte w trakcie, REQ-VCS-016); po niej zaznaczenie według REQ-VCS-028.

### Poza zakresem (propozycja)

- Pliki śledzone (Staged, Changes, Conflicts): `.gitignore` ich nie ukrywa, bo git dalej je śledzi. Opcja „przestań śledzić i ignoruj” (`git rm --cached`) do backlogu v2.
- Wybór innego pliku niż główny `.gitignore` (`.git/info/exclude`, `.gitignore` w podfolderze) i wzorce z gwiazdką („wszystkie *.log”): backlog v2.
- Cofnięcie: brak; użytkownik edytuje `.gitignore` sam.

## Przypadki testowe

### Zapis wzorców (`core`, na tymczasowym repo)

| ID | Przypadek | Oczekiwany wynik |
|---|---|---|
| G-01 | Jeden plik w Unversioned, brak `.gitignore` | powstaje `.gitignore` z `/a.log`; `a.log` znika ze statusu |
| G-02 | `.gitignore` bez nowej linii na końcu | dopisane `\n`, potem wzorzec w osobnej linii |
| G-03 | Wzorzec już jest w `.gitignore` | plik bez zmian |
| G-04 | Znaki specjalne: `#notatka.txt`, `!wazne.txt`, `plik[1].txt`, `a*b.txt`, `x ` (spacja na końcu) | `/#notatka.txt`, `/!wazne.txt`, `/plik\[1\].txt`, `/a\*b.txt`, `/x\ `; każdy plik znika ze statusu |
| G-05 | Polskie litery i spacje: `zdjęcie z wakacji.png` | zapis UTF-8, plik znika ze statusu |
| G-06 | Węzeł folderu `new/` (tylko nieśledzone) | `/new/`; wszystkie pliki folderu znikają |
| G-07 | Folder `new/` i plik `new/a.txt` razem | tylko `/new/` |
| G-08 | Folder z plikiem śledzonym i dwoma nieśledzonymi | dwa wzorce plików, nie `/folder/`; plik śledzony nadal śledzony |
| G-09 | `.gitignore` z końcami linii CRLF | dopisane linie z CRLF |
| G-10 | `.gitignore` tylko do odczytu | błąd z treścią; plik bez zmian |
| G-11 | Wcześniejsza reguła `!keep.log`, dodawany `/keep.log` | dopisany na końcu, więc wygrywa; plik znika |
| G-12 | Plik w podfolderze `a/b/c.tmp` | `/a/b/c.tmp` w głównym `.gitignore` |

### Model i menu (`app`, bez Tk)

| ID | Przypadek | Oczekiwany wynik |
|---|---|---|
| G-13 | Zaznaczenie tylko z Unversioned (pliki i foldery) | „Dodaj do .gitignore (N)” aktywne, N = liczba wpisów po scaleniu (G-07) |
| G-14 | Zaznaczenie zawiera plik ze Staged, Changes albo Conflicts | pozycja nieaktywna |
| G-15 | Po zapisie | odświeżenie; pliki znikają, `.gitignore` widoczny w Changes albo Unversioned |
| G-16 | Błąd zapisu | pasek błędu „Dodanie do .gitignore nie powiodło się”, repo bez zmian |
| G-17 | Repo zajęte inną operacją | pozycja nieaktywna (REQ-VCS-016) |
| G-18 | Stage (N) dla 3 plików z Changes i Unversioned | jedno `git add -- <3 pliki>`; zaznaczenie według REQ-VCS-028 za ostatnim z zaznaczonych |
| G-19 | Porównaj przy 2 zaznaczonych plikach | pozycja nieaktywna |

### Menu (`ui`)

| ID | Przypadek | Oczekiwany wynik |
|---|---|---|
| G-20 | Prawy przycisk na wierszu spoza zaznaczenia | zaznaczony tylko ten wiersz, menu dla niego |
| G-21 | Prawy przycisk na wierszu z zaznaczenia | menu dla całego zaznaczenia |
