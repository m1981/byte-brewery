# Pomysły do analizy: menu kontekstowe PyCharma

Zrzuty użytkownika z 2026-11-11 jako materiał do przyszłych funkcji („dodaj zrzuty jako do analizy nowych fukcji jakie mam w glowie”). To nie są wymagania: każda funkcja przechodzi zwykłą drogę (pytanie Q-VCS-068 → decyzja z cytatem → REQ/DES/AT → test → kod). Kolumna „vcs-lite dziś” to stan w chwili zapisu; operacje zmieniające historię są w backlogu v2 (DEC-VCS-011, DEC-VCS-116, REQ-VCS-017).

## 1. Lista zmian (okno Commit) — [pycharm-menu-zmiany.png](pycharm-menu-zmiany.png)

| Pozycja PyCharma | vcs-lite dziś |
|---|---|
| Stage / Unstage | jest (spacja, menu) |
| Stash Files | brak (stash: backlog v2) |
| Rollback | brak (discard: poza v1, DEC-VCS-010) |
| Delete… | brak |
| Show Diff / Show Diff in a New Window | jest: „Porównaj” w przeglądarce |
| Compare HEAD, Staged and Local Versions | brak (trzy wersje naraz) |
| Jump to Source | częściowo: „Otwórz w aplikacji” |
| Create Patch… / Copy as Patch to Clipboard | brak |
| Show History | jest: „Pokaż historię” (DEC-VCS-124) |

## 2. Commit w historii (karta Log) — [pycharm-menu-commit.png](pycharm-menu-commit.png)

| Pozycja PyCharma | vcs-lite dziś |
|---|---|
| Copy Revision Number | jest: „Kopiuj hash” |
| View in browser | jest: „Otwórz w przeglądarce” |
| Create Patch… | brak |
| Cherry-Pick, Checkout Revision, Reset Current Branch to Here…, Revert Commit, Undo Commit… | brak (zmiana repo: backlog v2) |
| Show Repository at Revision, Compare with Local | brak |
| Edit Commit Message…, Fixup…, Squash Into…, Drop Commit, Interactively Rebase from Here… | brak (przepisywanie historii: backlog v2) |
| Push All up to Here… | brak |
| New Branch…, New Tag… | brak (gałęzie i tagi: backlog v2) |
| Go to Child Commit / Go to Parent Commit | częściowo: kliknięcie rodzica w szczegółach |

## 3. Pliki zaznaczonego commita — [pycharm-menu-pliki-commita.png](pycharm-menu-pliki-commita.png)

| Pozycja PyCharma | vcs-lite dziś |
|---|---|
| Show Diff / Show Diff in a New Window | jest: dwuklik i „Porównaj” |
| Compare with Local, Compare Before with Local | brak |
| Edit Source | brak w plikach commita („Otwórz w aplikacji” jest w liście zmian i drzewie PROJEKT) |
| Open Repository Version | brak (wersja pliku z commita w przeglądarce) |
| Revert Selected Changes, Cherry-Pick Selected Changes, Extract Selected Changes to Separate Commit…, Drop Selected Changes | brak (zmiana repo) |
| Create Patch…, Get from Revision | brak |
| History Up to Here | częściowo: „Pokaż historię” bez ograniczenia do commita |
| Show Changes to Parents | brak (merge względem każdego rodzica) |
