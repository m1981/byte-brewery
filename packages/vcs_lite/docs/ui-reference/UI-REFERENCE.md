# vcs-lite — wzorzec wyglądu okna E-01 (wariant A)

Wzorzec wybrany przez użytkownika 2026-10-21 (DEC-VCS-045). Obowiązuje zamiast szkicu ASCII E-01 w SPEC.md. Źródła, w kolejności ważności:

1. `E-01.html`: makieta, z której pochodzą wszystkie wartości poniżej (CSS w nagłówku pliku). `E-01-stany.html`: stany spoza makiety, zaakceptowane P2–P10 (DEC-VCS-049), źródło sekcji 8.
2. `E-01.png`: zrzut makiety wykonany przez użytkownika (1135 × 712 px); pokazuje, jak wartości wyglądają razem.
3. Ten dokument: każda wartość wypisana jawnie, z odwzorowaniem w Tk 8.6 i listą przybliżeń.

Zasada: nic z makiety nie jest pomijane. Każde odstępstwo w implementacji ma wpis w sekcji „Przybliżenia w Tk” albo „Do ustalenia”. Jednostki: piksele CSS (1 px CSS = 1 punkt ekranu macOS, czyli tyle samo, co jednostka w Tk na macOS).

## 1. Kolory

### Tokeny

| Token | Wartość | Użycie |
|---|---|---|
| `bg` | `#ffffff` | tło okna, obszaru plików, przycisków drugiego planu, pola wiadomości |
| `chrome` | `#ececee` | pasek tytułu, pasek stanu |
| `sidebar` | `#f2f2f5` | tło paska bocznego repozytoriów |
| `line` | `#dedee3` | wszystkie linie podziału (1 px) |
| `ink` | `#1d1d1f` | tekst podstawowy |
| `dim` | `#6e6e73` | tekst drugoplanowy: gałąź w pasku bocznym, nagłówki sekcji, katalog pliku, podpowiedzi, przyczyna, pasek stanu |
| `accent` | `#0a66d8` | zaznaczone repo, przycisk główny |
| `accent-soft` | `#e3eefc` | zaznaczony wiersz pliku |
| `mod` | `#b4690e` | status M (zmieniony); kropka stanu „zmiany” |
| `add` | `#1f7a3a` | status A (dodany) |
| `del` | `#c2302a` | status D (usunięty) |
| `ren` | `#2a5fb0` | status R (przeniesiony) |
| `unv` | `#7a7a80` | status ? (poza kontrolą) |
| `conf` | `#c2302a` | konflikt: kropka stanu, tekst znacznika „konflikt” |

### Kolory pojedyncze

| Wartość | Gdzie |
|---|---|
| `#fafafb` | tło paska narzędzi i panelu commita |
| `#eef0f3` | tło chipa gałęzi |
| `#3a3a40` | tekst chipa gałęzi; tekst licznika w pasku bocznym |
| `#4a4a50` | tytuł okna |
| `#c9c9cf` | obramowanie przycisków i pola wiadomości |
| `#dfe1e6` | tło licznika zmian (niezaznaczone repo) |
| `#dbe8fb` | tekst gałęzi w zaznaczonym repo |
| `#9fd3ad` | kropka stanu „czyste” |
| `#c7c7cc` | kropka stanu „niedostępne” |
| `#8e8e93` | nazwa repo niedostępnego |
| `#fbe3e1` | tło znacznika „konflikt” |
| `#f5f7fb` | wiersz pliku pod kursorem |
| `#f0f0f3` / `#d5d5da` | tło / obramowanie klawisza (`kbd`) |
| `#ffffff` | tekst na `accent`, tekst w kwadratach statusu |
| `rgba(255,255,255,.25)` na `accent` = `#478ce2` | tło licznika w zaznaczonym repo (wyliczone) |
| `#ff5f57`, `#febc2e`, `#28c840` | przyciski okna macOS; rysuje je system, nie aplikacja |

### Stany nieaktywne (`opacity: .45`, wartości wyliczone na tle `#fafafb`)

| Element | Tło | Obramowanie | Tekst |
|---|---|---|---|
| przycisk główny | `#8eb7eb` | `#8eb7eb` | `#ffffff` |
| przycisk drugiego planu | `#ffffff` z przezroczystością → `#fcfcfc` | `#e4e4e7` | `#979798` |

## 2. Typografia

Rodzina: systemowa macOS (`-apple-system`, SF Pro Text). Monospace: `ui-monospace`, SF Mono, Menlo. Wysokość linii bazowa 1.4.

| Element | Rozmiar | Grubość | Kolor | Uwagi |
|---|---|---|---|---|
| tekst bazowy | 13 | 400 | `ink` | |
| tytuł okna | 13 | 600 | `#4a4a50` | „vcs-lite — <repo>” |
| nazwa repo w pasku narzędzi | 15 | 650 | `ink` | |
| chip gałęzi | 12 | 400 | `#3a3a40` | strzałka `→` w `dim` |
| przyciski | 13 | 400 | `ink` | przycisk główny 600, biały |
| nagłówek „REPOZYTORIA” | 11 | 600 | `dim` | wersaliki, odstęp liter 0.06 em |
| nazwa repo w pasku bocznym | 13 | 600 | `ink` | biała na zaznaczeniu |
| gałąź w pasku bocznym | 11.5 | 400 | `dim` | `#dbe8fb` na zaznaczeniu |
| licznik / znacznik | 11.5 | 600 | `#3a3a40` | cyfry tabelaryczne |
| nagłówek grupy („STAGED”) | 11 | 650 | `dim` | wersaliki, odstęp liter 0.06 em |
| liczba w nagłówku grupy | 11 | 500 | `dim` | bez odstępu liter |
| kwadrat statusu | 11 (mono) | 600 | `#ffffff` | jedna litera |
| nazwa pliku | 13 | 550 | `ink` | |
| katalog pliku i „stara → ” | 13 | 400 | `dim` | |
| podpowiedź przy wierszu | 11.5 | 400 | `dim` | |
| klawisz (`kbd`) | 11 (mono) | 400 | `ink` | |
| pole wiadomości | 13 | 400 | `ink` | |
| przyczyna nieaktywności | 12 | 400 | `dim` | poprzedzona „ⓘ” |
| pasek stanu | 11.5 | 400 | `dim` | |

## 3. Wymiary i odstępy

| Element | Wartości |
|---|---|
| okno | narożniki 12 (systemowe); szerokość makiety min. 860 |
| pasek tytułu | wysokość 38; poziomo 14; linia dolna 1 `line`; kropki 12 × 12 co 8 (systemowe) |
| pasek narzędzi | padding 10 × 14; odstęp 10; linia dolna 1 `line` |
| chip gałęzi | padding 2 × 9; promień pełny (999); odstęp wewnętrzny 6 |
| przycisk | padding 4 × 12; promień 6; obramowanie 1 |
| obszar główny | kolumny: pasek boczny 230, pliki reszta; wysokość min. 470 |
| pasek boczny | padding 10 × 8; odstęp między repo 2; linia prawa 1 `line` |
| nagłówek „REPOZYTORIA” | padding 6 × 8 |
| element repo | siatka: kropka 10 / tekst / licznik; odstęp 8; padding 7 × 8; promień 7; nazwa i gałąź w dwóch liniach |
| kropka stanu | 9 × 9, okrąg |
| licznik | min. szerokość 22; padding 1 × 7; promień pełny |
| stopka paska bocznego | przyklejona do dołu; padding 8 |
| obszar plików | padding górny 6 |
| nagłówek grupy | padding 10 (góra) × 16 (boki) × 4 (dół); odstęp do liczby 8 |
| wiersz pliku | siatka: kwadrat 22 / nazwa / podpowiedź; odstęp 10; padding 5 × 16 |
| kwadrat statusu | 18 × 18; promień 4 |
| panel commita | padding 12 × 14; siatka: pole / przyciski; odstęp 8 (pion) × 12 (poziom); linia górna 1 `line` |
| pole wiadomości | wysokość 64; padding 8 × 10; promień 8; obramowanie 1 `#c9c9cf` |
| przyciski commita | kolumna, odstęp 6; równa szerokość |
| linia przyczyny | pod polem i przyciskami, na całą szerokość; odstęp 6 po „ⓘ” |
| pasek stanu | padding 6 × 14; odstęp między pozycjami 14; linia górna 1 `line` |
| klawisz (`kbd`) | padding 0 × 4; promień 4; obramowanie 1, dolne 2 |

## 4. Elementy i ich stany

### Pasek tytułu
Tytuł „vcs-lite — <wybrane repo>”, wyśrodkowany. Bez wybranego repo: „vcs-lite”.

### Pasek narzędzi
Od lewej: nazwa wybranego repo; chip „⎇ <gałąź> → <upstream>”, a bez upstreamu „→ brak upstreamu”. Z prawej: „⇣ Pull” i „⟳ Odśwież”. Pull nieaktywny, gdy nie ma upstreamu; podpowiedź po najechaniu: „Gałąź nie ma upstreamu”.

### Pasek boczny repozytoriów
Nagłówek „REPOZYTORIA”. Element repo: kropka stanu, nazwa (pogrubiona), druga linia z gałęzią, licznik zmian po prawej.

| Stan repo (S-VCS-01) | Kropka | Druga linia | Prawa strona |
|---|---|---|---|
| ZMIANY | `mod` | „main”; z upstreamem „main · ↑<ahead> ↓<behind>” | licznik na `#dfe1e6` |
| CZYSTE | `#9fd3ad` | jak wyżej | brak licznika (P6) |
| KONFLIKT | `conf` | sama gałąź, np. „main” (DEC-VCS-048; makieta pokazuje „main · merge”) | znacznik „konflikt”: tło `#fbe3e1`, tekst `conf` |
| NIEDOSTĘPNE | `#c7c7cc` | „niedostępne” | brak; nazwa w `#8e8e93` |
| zaznaczone | — | tło `accent`, nazwa biała, gałąź `#dbe8fb` | licznik `#478ce2`, biały |

Stopka: przycisk „⚙ Repozytoria…” otwiera Settings (E-02).

### Lista plików
Grupy w kolejności: CONFLICTS (gdy są), STAGED, CHANGES, UNVERSIONED (P1, DEC-VCS-050). Nagłówek: nazwa wersalikami i liczba plików. Wiersz: kwadrat statusu, ścieżka (katalog w `dim`, nazwa pliku pogrubiona), podpowiedź po prawej.

| Kod | Litera | Kolor kwadratu |
|---|---|---|
| zmieniony | M | `mod` |
| dodany | A | `add` |
| usunięty | D | `del` |
| przeniesiony | R | `ren`; ścieżka „stara → **nowa**” |
| poza kontrolą | ? | `unv` |
| konflikt | „!” (P1) | `conf` |

| Stan wiersza | Tło | Podpowiedź |
|---|---|---|
| zwykły | `bg` | ukryta |
| pod kursorem | `#f5f7fb` | widoczna |
| zaznaczony | `accent-soft` | widoczna |

Teksty podpowiedzi: CONFLICTS „rozwiąż w edytorze · spacja oznacz jako rozwiązany” (P1); STAGED „spacja unstage”; CHANGES „spacja stage · dwuklik porównaj”; UNVERSIONED „spacja stage · dwuklik porównaj” (P7; makieta E-01 miała samo „spacja stage”). Słowa „spacja” i „dwuklik” w stylu `kbd`.

### Panel commita
Pole wiadomości z tekstem zastępczym „Opis zmian…   ⌘↩ commit · ⌘⇧↩ commit i push”. Obok, w kolumnie: przycisk główny „Commit do <repo>” i pod nim „Commit & Push”. Pod spodem linia przyczyny „ⓘ <commit_disabled_reason>”; ukryta, gdy commit jest możliwy.

### Pasek stanu
„Odświeżono HH:MM” (czas ostatniego odświeżenia wybranego repo) · „Dwuklik: porównanie w Beyond Compare” · „⌘1–⌘9 wybór repo” (klawisze w stylu `kbd`).

## 5. Odwzorowanie w Tk 8.6

| Element | Widżet | Jak |
|---|---|---|
| kolory i czcionki | `tkinter.font.Font`, słownik tokenów w jednym module | czcionka `TkDefaultFont` (systemowa SF) w rozmiarach z tabeli; monospace `Menlo` |
| pasek narzędzi, panel commita, pasek stanu | `tk.Frame` z `bg` z tokenów | ramki `tk`, nie `ttk`, żeby kolory tła były dokładne |
| chip gałęzi, licznik, znacznik „konflikt”, `kbd` | `tk.Canvas` | prostokąt z zaokrąglonymi rogami i tekst |
| pasek boczny | `tk.Canvas` | elementy repo rysowane w całości: zaokrąglone zaznaczenie, kropka, dwie linie tekstu, licznik |
| lista plików | `tk.Canvas` | wiersze rysowane według §3 i §4, z obsługą zaznaczenia, kursora, spacji, Enter i dwukliku (DEC-VCS-047) |
| kwadrat statusu | `PhotoImage` 18 × 18 | generowany raz na literę i kolor |
| przyciski | `ttk.Button` w motywie aqua | przycisk główny jako przycisk domyślny (`default="active"`); kolory i promienie systemowe, nie z §1 i §3 (DEC-VCS-047) |
| pole wiadomości | `tk.Text` | obramowanie przez otaczającą ramkę; tekst zastępczy przez `FocusIn`/`FocusOut` |
| podpowiedź Pull | mała ramka `tk.Toplevel` po najechaniu | |

## 6. Przybliżenia w Tk

| Wartość z makiety | Ograniczenie Tk | Przybliżenie |
|---|---|---|
| grubości 550, 600, 650 | Tk ma tylko `normal` i `bold` | 600 i 650 → `bold`; 550 → `bold` (do oceny na zrzucie) |
| rozmiary 11.5 | Tk przyjmuje całe punkty | 11.5 → 12 (do oceny na zrzucie) |
| odstęp liter 0.06 em | brak w Tk | pominięty; wersaliki zostają |
| `rgba` i `opacity` | brak przezroczystości widżetów | kolory wyliczone (sekcja 1) |
| cienie okna, narożniki 12 | rysuje system | bez zmian |
| kolory, promienie i padding przycisków | przyciski natywne aqua (DEC-VCS-047) | wygląd systemowy zamiast `#0a66d8` i promienia 6 |
| zaokrąglenie pola wiadomości (8) | `tk.Text` nie zaokrągla | prostokątne obramowanie 1 px `#c9c9cf` |

## 8. Stany spoza makiety E-01 (P1 DEC-VCS-050, P2–P10 DEC-VCS-049)

Źródło: `E-01-stany.html`. Nowe wartości: kropka „w toku”, pasek postępu, znak pustego stanu `#b9bac0`; reszta to tokeny z sekcji 1.

### P1 Pliki w konflikcie
Grupa CONFLICTS jako pierwsza na liście; nagłówek grupy w `conf` (reszta jak nagłówek grupy). Wiersz: kwadrat „!” w `conf`, nazwa pliku jak w innych grupach, podpowiedź „rozwiąż w edytorze · spacja oznacz jako rozwiązany” („spacja” w stylu `kbd`). Spacja z plikiem zawierającym znaczniki: pasek błędu P3 z tytułem „Oznaczenie jako rozwiązany nie powiodło się” i treścią „<plik>: plik nadal zawiera znaczniki konfliktu (linia N).” (REQ-VCS-024).

### P2 Konflikt w pasku narzędzi
Chip „N plik(i/ów) w konflikcie”: tło `#fbe3e1`, tekst `conf`, grubość 600, wymiary jak chip gałęzi. Zaznaczone repo w konflikcie: kropka `conf` z białą obwódką 2, znacznik „konflikt” na białym tle z tekstem `conf`. Przycisk commita nieaktywny z przyczyną „Rozwiąż konflikty przed commitem.”.

### P3 Komunikat błędu
Pasek na górze listy plików: margines 8 (góra) × 12 (boki) × 4 (dół); promień 8; tło `#fbe3e1`; lewa krawędź 3 `conf`; padding 8 × 10 × 8 × 12; siatka: znak / treść / zamknięcie, odstęp 4 × 10.
- znak „⚠”: `conf`, pogrubiony;
- tytuł „<Operacja> nie powiodła się”: 13, 600, `conf` (np. „Commit nie powiódł się”);
- treść od gita: monospace 12, wysokość linii 1.45, `ink`, zawijana, najwyżej 4 linie (dłuższa przewijana w pasku);
- „×”: 15, `dim`; zamyka pasek. Pasek znika też po następnej udanej operacji.
- Folder repozytoriów nie istnieje (E-02): ten sam pasek z tekstem „Katalog z repozytoriami nie istnieje: <ścieżka>”.

### P4 Operacja w toku
- pasek postępu: wysokość 2 przy dolnej krawędzi paska narzędzi; odcinek 30% szerokości w `accent`, przesuwany od lewej do prawej w 1.2 s, tylko w trakcie operacji; przy ograniczeniu ruchu pełna szerokość, bez animacji;
- napis w pasku narzędzi po chipie: 12, `dim`, np. „Wypychanie do origin…”;
- druga linia repo w pasku bocznym „w toku…”; kropka na zaznaczonym repo biała z obwódką 2 w kolorze `#84b2eb` (biel 50% na `accent`, wyliczone);
- Commit, Commit & Push i Pull nieaktywne z przyczyną „Trwa operacja na tym repozytorium.”; lista plików pozostaje widoczna.

### P5 Puste stany
Wyśrodkowane w obszarze plików: padding 40 × 24; odstęp 6; znak 26 w `#b9bac0`; nagłówek 15, 600; opis `dim`, szerokość do 46 znaków; ścieżka monospace 12 `dim`; przycisk z marginesem górnym 6.

| Sytuacja | Znak | Nagłówek | Opis | Akcja |
|---|---|---|---|---|
| nic nie wybrano | ▣ | Wybierz repozytoria | vcs-lite pokazuje repozytoria z folderu `<rootdir>` | „⚙ Wybierz repozytoria…” (przycisk domyślny) |
| repo są, brak wyboru | ← | Wybierz repozytorium | Kliknij je po lewej albo naciśnij ⌘1. | — |
| brak zmian | ✓ w `add` | Brak zmian | Kopia robocza <repo> jest zgodna z ostatnim commitem. | — |
| repo niedostępne | ⊘ | Repozytorium niedostępne | `<ścieżka>`; Folder nie istnieje albo nie jest repozytorium gita. | „⟳ Sprawdź ponownie” |

Pasek boczny bez repozytoriów: pod nagłówkiem „Brak” w `dim`, padding 4 × 8.

### P6 Repo czyste
Zielona kropka `#9fd3ad`, bez licznika.

### P7 Podpowiedź UNVERSIONED
„spacja stage · dwuklik porównaj”, jak w CHANGES.

### P8 Okno „Repozytoria do obserwowania” (E-02)
Okno modalne nad oknem głównym (`tk.Toplevel`, `transient`, `grab_set`): szerokość 420; promień 12 (systemowy).
- nagłówek „Repozytoria do obserwowania”: 15, 650; padding 16 × 18 × 4;
- podtytuł „z folderu `<rootdir>`”: `dim`, padding 0 × 18 × 10; ścieżka jako chip monospace 12 na `#eef0f3`, promień 5, padding 1 × 6; nieedytowalna w v1;
- lista: linie 1 `line` u góry i u dołu; wysokość do 220 z przewijaniem; padding 4 × 0; wiersz: pole wyboru natywne / nazwa / miejsce na dodatek, odstęp 10, padding 6 × 18; kolejność alfabetyczna;
- notka „Pokazane są repozytoria z pierwszego poziomu folderu. Zwykłe i ukryte foldery są pominięte.”: 12, `dim`, padding 8 × 18;
- stopka: tło `#fafafb`, linia górna 1 `line`, padding 12 × 18, odstęp 8; po lewej „Zaznaczono N z M” (12, `dim`); po prawej „Anuluj” i „Zapisz” (przycisk domyślny).

### P9 Pytanie o upstream
Natywne `tkinter.messagebox.askyesno`. Tytuł: „Gałąź <gałąź> nie ma upstreamu”. Treść: „Commit został zapisany. Wypchnąć gałąź do origin i ustawić upstream?”. Przyciski systemowe Tak / Nie.

### P10 Odłączony HEAD
Chip „⎇ odłączony HEAD · <7 znaków commita>”. Pull nieaktywny, podpowiedź „Odłączony HEAD: brak gałęzi do pull”. Commit & Push nieaktywny, podpowiedź „Odłączony HEAD: brak gałęzi do wypchnięcia”. Commit aktywny.

### Odwzorowanie w Tk
- pasek błędu i puste stany: `tk.Frame` i `tk.Label` z tokenami; treść błędu w `tk.Text` tylko do odczytu, wysokość 4 linie;
- pasek postępu: `tk.Canvas` wysokości 2 z prostokątem przesuwanym przez `after()` wyłącznie w trakcie operacji (REQ-VCS-101);
- podpowiedzi po najechaniu: mała `tk.Toplevel` bez ramki.

## 7. Do ustalenia (rejestr w SPEC.md)

- Q-VCS-030 i Q-VCS-031 rozstrzygnięte: DEC-VCS-047, DEC-VCS-048.
- Q-VCS-032 rozstrzygnięte dla P2–P10 (DEC-VCS-049, sekcja 8).
- Q-VCS-033 rozstrzygnięte: DEC-VCS-050 (P1).
