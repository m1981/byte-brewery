# vcs-lite — propozycja: „Szukaj w plikach” (podwójny Shift)

Status: analiza agenta z 2026-10-23 do decyzji użytkownika (rejestr pytań w `SPEC.md`). Pomysł użytkownika: okno modalne otwierane podwójnym naciśnięciem Shift; wpisana fraza jest szukana w plikach śledzonych przez git, z opcjami „całe słowo”, „wielkość liter” i filtrem rozszerzeń.

## Fakty sprawdzone na tym Macu (git 2.47.1, 2026-10-23)

| Sprawdzenie | Wynik |
|---|---|
| `git grep -w -F w` w pliku z „żółw idzie” | **trafia** w „żółw”: git uznaje polskie litery za separatory słów, więc `-w` jest błędne dla polskiego tekstu |
| `git grep -i -F łódź` w pliku z samym „ŁÓDŹ” | trafia: wielkość liter z polskimi znakami działa |
| `git grep -I` na pliku z bajtem NUL | plik binarny pominięty |
| `git grep -z -n --column` | ścieżka, numer linii i kolumna oddzielone NUL: nazwy z `:` i spacją są bezpieczne |
| czas `git grep -I -n -i -F` na całym byte-brewery | 0,02 s |
| największe repo użytkownika (`docs`) | ok. 1000 śledzonych plików |

## Najtrudniejsze miejsca

1. **„Całe słowo” w polskim tekście.** `git grep -w` jest niepoprawne (wyżej). Rozwiązanie: git tylko wstępnie wybiera linie (`-F`, opcjonalnie `-i`), a o trafieniu decyduje Python: wyrażenie z `re.escape(fraza)` i granicami słowa świadomymi Unicode (`(?<!\w)…(?!\w)` na `str`). Ta sama funkcja wyznacza zakresy do podświetlenia, więc filtr i podświetlenie nie mogą się rozjechać.
2. **Podwójny Shift.** Shift jest też w wielkich literach i w zaznaczaniu Shift-kliknięciem (REQ-VCS-029). Liczą się tylko dwa samodzielne naciśnięcia (puszczenie, puszczenie) w czasie do 350 ms, bez żadnego innego klawisza ani kliknięcia pomiędzy. Lewy i prawy Shift liczą się tak samo. Automat stanów z wstrzykiwanym zegarem testuje się bez okna (Tk nie dostarcza zdarzeń do ukrytego okna testowego).
3. **Responsywność i anulowanie.** Wyszukiwanie po każdym wpisanym znaku zaleje Worker. Potrzebne jest opóźnienie (debounce) 250 ms, numer zapytania (wynik starszego zapytania jest wyrzucany) oraz przerwanie procesu `git grep`, gdy przyjdzie nowe zapytanie. Wynik obcięty do 500 trafień z dopiskiem „pokazano pierwsze 500”.
4. **Granica „tylko git”.** DES-VCS-001 mówi, że git uruchamia wyłącznie `gitcli`. Strumieniowe czytanie z możliwością przerwania to nowa metoda `GitCli.stream`, a nie osobny `subprocess` w module wyszukiwania.
5. **Filtr rozszerzeń.** Użytkownik wpisze „md, py”, „*.md;*.py” albo „.md”. Normalizacja do pathspec gita `:(glob,icase)**/*.md`, żeby `README.MD` też się liczył; puste pole oznacza wszystkie pliki.
6. **Treść, a nie indeks.** `git grep` czyta kopię roboczą plików śledzonych (zmienione pliki są przeszukiwane w obecnej postaci); pliki usunięte z dysku są pomijane. Bardzo długie linie (np. zminifikowane) są skracane w podglądzie do okolic trafienia.
7. **Otwieranie trafienia.** macOS `open` nie umie skoczyć do linii. Dla `.md` strona w trybie czytania może przewinąć do trafienia (kotwica). Inne pliki: domyślna aplikacja bez skoku do linii, albo edytor przez schemat URL (do decyzji).

### Dlaczego bez własnego indeksu (KISS, YAGNI)

Indeks odwrócony albo trigramowy daje zysk dopiero przy dziesiątkach tysięcy plików. Tu `git grep` przeszukuje największe repo w setnych częściach sekundy, korzysta z pamięci podręcznej systemu i sam wie, co jest śledzone. Indeks w procesie vcs-lite zjadłby limit 60 MB (REQ-VCS-100) i wymagałby unieważniania po każdej zmianie pliku (także spoza vcs-lite). Wracamy do tematu tylko wtedy, gdy pomiar pokaże czas powyżej 200 ms.

## Diagram klas

```
 ui/                               app/                                core/
 ┌─────────────────────────┐      ┌───────────────────────────┐      ┌──────────────────────────────┐
 │ DoubleShift             │      │ SearchSession             │      │ «Protocol» TextSearcher       │
 │  press(keysym, t)       │─────▶│  query: SearchQuery       │─────▶│  search(repo, query, limit,  │
 │  release(keysym, t)     │ open │  results: SearchResult    │ uses │         cancel) → SearchResult│
 │  other()                │      │  set_query(query)         │      └──────────────▲───────────────┘
 │  → on_double()          │      │    debounce, generation   │                     │ implements
 └─────────────────────────┘      │  open(match) ─────────────┼──▶ AppModel   ┌──────┴───────────────┐
 ┌─────────────────────────┐      │  subscribe(listener)      │   .read()      │ GitGrepSearcher       │
 │ SearchDialog (Toplevel) │◀─────│                           │   .open_file() │  argv(query) → git    │
 │  pole frazy, 2 pola     │render└───────────────────────────┘               │  parse(stream) → linie│
 │  wyboru, filtr, wyniki  │                                                   │  verify(line) → Match │
 │  ResultList (Canvas)    │                                                   └──────┬───────────────┘
 └─────────────────────────┘                                                          │ runs git only via
                                                                                      ▼
 Wartości (core/search.py, bez logiki I/O):                                    GitCli.stream()
   SearchQuery(text, whole_word, case_sensitive, extensions)  — normalizuje filtr, buduje wzorzec
   Match(path, line, column, text, spans)                     — spans do podświetlenia
   SearchResult(matches, truncated, generation)
   match_spans(text, query) → list[(start, end)]              — jedno źródło prawdy dla filtra i podświetlenia
```

| Klasa | Jedna odpowiedzialność (SRP) | Zależy od |
|---|---|---|
| `SearchQuery` | poprawne zapytanie: tekst, opcje, znormalizowane rozszerzenia, wzorzec | nic |
| `match_spans` | czy linia pasuje i gdzie (Unicode, całe słowo, wielkość liter) | `SearchQuery` |
| `TextSearcher` (port) | kontrakt wyszukiwania, który można podmienić (np. na indeks), DIP | — |
| `GitGrepSearcher` | argumenty `git grep`, czytanie wyniku `-z`, weryfikacja przez `match_spans`, limit | `GitCli.stream`, `match_spans` |
| `GitCli.stream` | jedyne miejsce uruchamiania gita także dla wyniku strumieniowego, z przerwaniem | — |
| `SearchSession` (app, bez Tk) | stan okna: zapytanie, opóźnienie, numer zapytania, wynik, otwieranie trafień przez `AppModel` | `TextSearcher`, Worker, `AppModel` |
| `DoubleShift` (ui, bez Tk w logice) | rozpoznanie podwójnego Shift z wstrzykiwanym zegarem | zegar |
| `SearchDialog`, `ResultList` | rysowanie i zdarzenia Tk; żadnej logiki wyszukiwania | `SearchSession` |

DRY: otwieranie trafień używa istniejących `AppModel.read` i `open_file`; lista wyników korzysta z `fit_pieces`, `elide` i `theme`. Open/closed: nowy sposób wyszukiwania to nowa implementacja `TextSearcher`, bez zmian w oknie.

## Pytania do decyzji (wstępne)

1. Silnik: `git grep` jako wstępny filtr i weryfikacja w Pythonie (rekomendacja) czy własne przeszukiwanie plików w Pythonie.
2. Zakres: wybrane repo (rekomendacja) czy wszystkie obserwowane.
3. Enter na trafieniu: `.md` w trybie czytania przewinięte do trafienia, inne pliki w domyślnej aplikacji (rekomendacja), czy w edytorze przez schemat URL.
