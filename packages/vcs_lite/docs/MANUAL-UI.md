# vcs-lite — ręczna weryfikacja okna

Lista kontrolna dla VER-VCS-013 i części ręcznej DES-VCS-032. Wykonuje ją użytkownik na repozytoriach demonstracyjnych; agent przygotowuje repozytoria, uruchamia okno i odczytuje zrzuty. Odwołania do ID sprawdza `tests/test_traceability.py`.

## Przygotowanie (agent)

- `tools/make_demo.py <folder>` tworzy repozytoria demonstracyjne poza `~/PycharmProjects`:
  - `alpha`: plik zmieniony, plik w Staged, plik w obu grupach, nowy folder z dwoma plikami, plik ignorowany `.log`, zmiana nazwy;
  - `beta`: repo z lokalnym `origin` (push i pull);
  - `gamma`: konflikt po merge;
  - filtry: zwykły folder `zdjecia`, ukryte repo `.ukryte`, repo zagnieżdżone `alpha/nested`.
- Okno startuje z własnym plikiem ustawień w folderze demo, więc ustawienia użytkownika zostają nietknięte.
- Pamięć mierzy agent przez `footprint <pid>`.

## Zrzuty ekranu

- Zrzut jednego okna: ⌘⇧4, spacja, kliknięcie okna. Plik trafia na Biurko albo do folderu ustawionego w ⌘⇧5 → Opcje (np. `~/PycharmProjects/INBOX`).
- Po każdym kroku: „krok N: OK” albo „krok N: nie, <co widać>”, a przy zrzucie numer kroku.
- Dodatkowy zrzut zawsze, gdy coś wygląda źle: ucięty tekst, nachodzące elementy, komunikat błędu, zawieszone okno.

## Kroki

| Krok | Działanie | Oczekiwany wynik | Zrzut | Sprawdza |
|---|---|---|---|---|
| 1 | Okno startuje samo. | Wygląd zgodny ze wzorcem `ui-reference/E-01.png`: pasek narzędzi, pasek boczny repozytoriów, lista plików, panel commita, pasek stanu; lista repo pusta przed pierwszym wyborem w Settings. | tak, całe okno | DES-VCS-022, DES-VCS-042 |
| 2 | Kliknij **⚙ Repozytoria…**. | Lista zawiera `alpha`, `beta`, `gamma`; nie zawiera `zdjecia`, `.ukryte` ani `alpha/nested`. | tak, okno Settings | AT-VCS-018, AT-VCS-022 |
| 3 | Zaznacz `alpha`, `beta`, `gamma`; **Zapisz**. | Trzy repo z nazwą gałęzi i liczbą zmian; `gamma` oznaczone jako konflikt. | tak, lista repo | REQ-VCS-002, AT-VCS-001 |
| 4 | Kliknij `alpha`. | Grupy Staged, Changes, Unversioned; nazwy plików w kolorach z `ui-reference/UI-REFERENCE.md` §9, bez kwadratów, wiersze co 24 pt; plik zmieniony w obu miejscach w obu grupach; pliki z nowego folderu osobno, z szarym „new” za nazwą; brak pliku `.log`. | tak, lista plików | T-VCS-01, AT-VCS-003, AT-VCS-005, AT-VCS-006 |
| 5 | Zaznacz plik w Changes, naciśnij **spację**; potem spację na nim w Staged. | Plik przechodzi do Staged i z powrotem do Changes. | nie | AT-VCS-029 |
| 6 | **Dwuklik** na pliku `.py` w Changes. | W przeglądarce diff lewo–prawo jak `ui-reference/E-05-diff.html` z tytułami `plik (indeks)` i `plik (kopia robocza)`; lista się odświeża. | tak, strona diffu | AT-VCS-004, AT-VCS-027, AT-VCS-046 |
| 7 | Bez wiadomości spójrz na przycisk commita. | „Commit do alpha” nieaktywny, obok przyczyna „Wpisz wiadomość commita.”. | tak, pasek commita | AT-VCS-011 |
| 8 | Wpisz `wip alpha`; ⌘2; wpisz `wip beta`; ⌘1. | W `alpha` pole zawiera `wip alpha`, przycisk „Commit do alpha”. | tak, pasek commita | AT-VCS-023, REQ-VCS-022 |
| 9 | W `alpha` z plikiem w Staged wpisz wiadomość i naciśnij ⌘↩. | Commit wykonany, pole puste, Staged pusty, okno nie zamarza. | nie | AT-VCS-010 |
| 10 | Kliknij `gamma`. | Pliki w grupie Conflicts; Commit nieaktywny z przyczyną o konflikcie. | tak, całe okno | REQ-VCS-019 |
| 11 | W `beta`: plik do Staged spacją, wiadomość, ⌘⇧↩ (Commit & Push), potem **Pull**. | Push bez pytań; Pull bez błędu. | nie | REQ-VCS-011, REQ-VCS-020 |
| 12 | Napisz „gotowe do 12”; agent usuwa `beta` i zmienia plik w `alpha`; kliknij w okno vcs-lite. | `beta` wyszarzone („niedostępne”); `alpha` pokazuje nową zmianę bez Refresh. | tak, lista repo | AT-VCS-002, REQ-VCS-015 |
| 13 | Zostaw okno minutę bez ruchu; napisz „gotowe do 13”. | Agent mierzy pamięć (limit 60 MB) i brak wywołań gita w bezczynności. | nie | AT-VCS-016, REQ-VCS-101 |
| 14 | W `gamma` zaznacz `f.txt` (w konflikcie) i naciśnij **spację**. Napisz „gotowe do 14”; agent usuwa znaczniki z `f.txt`. Ponownie spacja na `f.txt`. | Za pierwszym razem pasek błędu: „f.txt: plik nadal zawiera znaczniki konfliktu (linia 1).”, plik zostaje w Conflicts. Za drugim razem plik wychodzi z Conflicts: z treścią różną od HEAD trafia do Staged; z treścią równą HEAD (np. strona „ours”) znika z listy, a repo pokazuje merge gotowy do commita (REQ-VCS-027). W obu przypadkach Commit staje się aktywny po wpisaniu wiadomości i kończy merge. | tak, po pierwszej spacji | AT-VCS-031, AT-VCS-030 |
| 15 | W `alpha` wybierz widok **Foldery**. Najedź na węzeł `new` w Unversioned i kliknij „+”. Zamknij i uruchom okno ponownie. | Węzeł `new` z „2 pliki”, pliki pod nim od 68 pt; „+” widoczny tylko pod kursorem; po kliknięciu oba pliki w Staged pod węzłem `new` z „−”; po restarcie pole nadal zaznaczone. | tak, z kursorem na węźle | AT-VCS-032, AT-VCS-033 |
| 16 | W `alpha` naciśnij i puść **Shift** dwa razy szybko; wpisz `w`, włącz **W** (⌥⌘W), w masce wpisz `md`; strzałką wybierz trafienie w pliku `.md` i naciśnij **↩**. Potem ⌘⇧F, trafienie w pliku innym niż `.md` i **↩**. | Okno „Szukaj w plikach — alpha” jak `ui-reference/E-04-szukaj.html` (P15a); trafienia z podświetlonym `w`, bez trafień wewnątrz słów; po ↩ przeglądarka pokazuje dokument przewinięty do linii z podświetlonym blokiem, a okno wyszukiwania się zamyka; plik inny niż `.md` otwiera się w domyślnej aplikacji. Shift przy pisaniu wielkich liter ani Shift-kliknięcie nie otwierają okna. | tak, okno wyszukiwania i strona | AT-VCS-041, AT-VCS-042, AT-VCS-044, REQ-VCS-033 |
| 17 | W `alpha` dwuklik na `logo.png` (Changes), na `ikona.png` (Staged) i na `opis.pdf` (Unversioned); w widoku **Projekt** dwuklik na `notatki.txt` i na `archiwum.zip`; prawy przycisk na `logo.png` → **Otwórz w aplikacji**. | Obrazki i PDF w kartach domyślnej przeglądarki; `ikona.png` w wersji z indeksu; `notatki.txt` jako strona z numerami linii; `archiwum.zip` i „Otwórz w aplikacji” w domyślnych aplikacjach. | tak, karty przeglądarki | AT-VCS-045, REQ-VCS-034 |

## Kolejne małe kroki budowy okna

| Etap | Co powstaje | Kroki ręczne |
|---|---|---|
| UI-1 | Szkielet okna: lista repo, pusty obszar plików, pasek commita; uruchamianie i odpytywanie `Worker` tylko w trakcie operacji. | 1 |
| UI-2 | Okno Settings z zapisem wyboru. | 2, 3 |
| UI-3 | Drzewo plików z grupami po wyborze repo, kolory PyCharma, widok folderów. | 4, 15 |
| UI-4 | Spacja (stage, unstage) i dwuklik (porównanie w przeglądarce). | 5, 6 |
| UI-5 | Pasek commita: przyczyna nieaktywności, szkice, skróty, commit. | 7, 8, 9 |
| UI-6 | Konflikty, Commit & Push, Pull. | 10, 11, 14 |
| UI-7 | Odświeżanie po fokusie, repo niedostępne, pomiar pamięci. | 12, 13 |
