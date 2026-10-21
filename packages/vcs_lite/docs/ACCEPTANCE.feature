# language: en
# Specyfikacja wykonywalna po dodaniu adaptera testowego; obecnie bez definicji kroków.
# Status @confirmed oznacza potwierdzoną potrzebę, a nie przejście testu.
# Statusy @proposal i @decision_pending nie stanowią decyzji użytkownika.
# Status @dormant oznacza potwierdzoną potrzebę, która w v1 nie obowiązuje.
@vcs_lite
Feature: Lekki panel VCS dla kilku repozytoriów
  Programista z małą ilością wolnej pamięci przegląda zmiany w wybranych repozytoriach,
  ogląda diff lewo–prawo i commituje bez uruchamiania ciężkiego IDE.

  Background:
    Given rootdir "~/PycharmProjects" jest zastąpiony tymczasowym katalogiem testowym

  @AT_VCS_001 @confirmed @UC_VCS_01 @REQ_VCS_001 @VER_VCS_005
  Scenario: Wybór repozytoriów w Settings przetrwa restart
    Given rootdir zawiera repozytoria "alpha", "beta" i "gamma"
    When użytkownik zaznacza w Settings "alpha" i "gamma" i zapisuje
    And narzędzie zostaje zamknięte i uruchomione ponownie
    Then lista repozytoriów zawiera dokładnie "alpha" i "gamma"

  @AT_VCS_002 @confirmed @UC_VCS_02 @REQ_VCS_018 @VER_VCS_005
  Scenario: Usunięte repozytorium jest oznaczone jako niedostępne
    Given repozytoria "alpha" i "beta" są obserwowane
    When folder "beta" zostaje usunięty z dysku
    And użytkownik wybiera Refresh
    Then "beta" ma stan NIEDOSTĘPNE
    And "alpha" pokazuje swoje zmiany bez błędu

  @AT_VCS_003 @confirmed @UC_VCS_02 @REQ_VCS_003 @VER_VCS_001
  Scenario: Plik zmieniony i niestage'owany trafia do Changes
    Given śledzony plik "app.py" został zmieniony na dysku
    When użytkownik wybiera repozytorium
    Then "app.py" jest w grupie Changes
    And grupa Staged nie zawiera "app.py"

  @AT_VCS_004 @confirmed @UC_VCS_03 @REQ_VCS_003 @REQ_VCS_023 @DEC_VCS_035 @VER_VCS_011
  Scenario: Zewnętrzne narzędzie dostaje strony zgodne z grupą pliku
    Given "app.py" ma w indeksie linię "return x * 3" zamiast "return x * 2" z HEAD
    And kopia robocza "app.py" ma dodatkowo linię "# todo"
    When użytkownik otwiera porównanie "app.py" z grupy Staged
    Then narzędzie diffu dostaje po lewej treść z HEAD, a po prawej treść z indeksu
    When użytkownik otwiera porównanie "app.py" z grupy Changes
    Then narzędzie diffu dostaje po lewej treść z indeksu, a po prawej plik z kopii roboczej

  @AT_VCS_005 @confirmed @UC_VCS_02 @REQ_VCS_003 @DEC_VCS_006 @VER_VCS_001
  Scenario: Pliki w nowym katalogu są pokazane pojedynczo
    Given nieśledzony katalog "new/" zawiera pliki "a.txt" i "b.txt"
    When użytkownik wybiera repozytorium
    Then grupa Unversioned zawiera "new/a.txt" i "new/b.txt"

  @AT_VCS_006 @confirmed @UC_VCS_02 @REQ_VCS_004 @VER_VCS_001
  Scenario: Pliki ignorowane nie są pokazywane
    Given ".gitignore" zawiera "*.log"
    And na dysku istnieje nieśledzony plik "debug.log"
    When użytkownik wybiera repozytorium
    Then żadna grupa nie zawiera "debug.log"

  # Uśpione w v1: DEC-VCS-044.
  @AT_VCS_007 @dormant @UC_VCS_03 @REQ_VCS_007 @VER_VCS_001
  Scenario: Plik binarny nie ma diffu, ale można go stage'ować
    Given nieśledzony plik "logo.png" ma zawartość binarną
    When użytkownik wybiera "logo.png"
    Then zamiast diffu widoczny jest komunikat o pliku binarnym
    And akcja Stage dla "logo.png" jest dostępna

  @AT_VCS_008 @confirmed @UC_VCS_04 @REQ_VCS_005 @VER_VCS_002
  Scenario: Stage zapisuje w indeksie cały plik
    Given śledzony plik "app.py" ma na dysku zmiany w dwóch odległych miejscach
    When użytkownik wybiera Stage dla "app.py"
    Then "app.py" jest w grupie Staged
    And grupa Changes nie zawiera "app.py"
    And indeks zawiera obie zmiany

  @AT_VCS_009 @confirmed @UC_VCS_04 @REQ_VCS_005 @VER_VCS_002
  Scenario: Unstage zmiany nazwy przywraca obie ścieżki
    Given plik "old.py" został przemianowany na "new.py" i zmiana jest w indeksie
    When użytkownik wybiera Unstage dla "old.py → new.py"
    Then indeks nie zawiera zmiany nazwy
    And "new.py" jest w grupie Unversioned
    And usunięcie "old.py" jest w grupie Changes

  @AT_VCS_010 @confirmed @UC_VCS_05 @REQ_VCS_009 @VER_VCS_003
  Scenario: Commit obejmuje tylko zawartość Staged
    Given "a.py" jest w grupie Staged
    And "b.py" jest w grupie Changes
    When użytkownik wpisuje wiadomość "fix a" i wybiera Commit
    Then ostatni commit zawiera zmianę "a.py" i wiadomość "fix a"
    And ostatni commit nie zawiera zmiany "b.py"
    And pole wiadomości jest puste

  @AT_VCS_011 @confirmed @UC_VCS_05 @REQ_VCS_009 @VER_VCS_003
  Scenario Outline: Commit jest nieaktywny bez wymaganych danych
    Given grupa Staged jest <staged>
    And pole wiadomości zawiera <wiadomość>
    Then przycisk Commit jest nieaktywny

    Examples:
      | staged    | wiadomość          |
      | pusta     | tekst "fix"        |
      | niepusta  | pusty tekst        |
      | niepusta  | wyłącznie spacje   |

  @AT_VCS_012 @confirmed @UC_VCS_05 @REQ_VCS_010 @VER_VCS_003
  Scenario: Odrzucenie commita przez hook zachowuje wiadomość i Staged
    Given repozytorium ma hook "pre-commit", który kończy się błędem z komunikatem "lint failed"
    And "a.py" jest w grupie Staged
    When użytkownik wpisuje wiadomość "fix a" i wybiera Commit
    Then widoczny jest komunikat zawierający "lint failed"
    And pole wiadomości zawiera "fix a"
    And "a.py" jest w grupie Staged
    And liczba commitów się nie zmieniła

  @AT_VCS_013 @confirmed @UC_VCS_06 @REQ_VCS_011 @VER_VCS_004
  Scenario: Commit & Push wysyła commit do upstreamu
    Given gałąź "main" śledzi "origin/main" w lokalnym bare repo
    And "a.py" jest w grupie Staged
    When użytkownik wpisuje wiadomość "fix a" i wybiera Commit & Push
    Then "origin/main" wskazuje nowy commit "fix a"

  @AT_VCS_014 @confirmed @UC_VCS_06 @REQ_VCS_012 @DEC_VCS_009 @VER_VCS_004
  Scenario: Odrzucony push nie cofa commita
    Given "origin/main" ma commit, którego brakuje lokalnie
    And "a.py" jest w grupie Staged
    When użytkownik wybiera Commit & Push z wiadomością "fix a"
    Then lokalna gałąź zawiera commit "fix a"
    And widoczny jest komunikat gita o odrzuceniu pusha
    And narzędzie nie wykonało pull ani rebase

  @AT_VCS_015 @confirmed @UC_VCS_06 @REQ_VCS_014 @VER_VCS_004
  Scenario: Brak danych logowania kończy się komunikatem, a nie zawieszeniem
    Given push wymaga uwierzytelnienia, którego git nie ma
    When użytkownik wybiera Commit & Push
    Then w ciągu 30 sekund widoczny jest komunikat o błędzie uwierzytelnienia
    And interfejs reaguje na działania użytkownika przez cały czas

  @AT_VCS_016 @confirmed @REQ_VCS_100 @DEC_VCS_013 @DEC_VCS_042 @VER_VCS_006
  Scenario: Zużycie pamięci mieści się w progu
    Given 3 repozytoria są obserwowane, a jedno ma 300 zmienionych plików
    And otwarte jest porównanie pliku o długości 2000 linii w zewnętrznym narzędziu
    When narzędzie pozostaje bezczynne przez 5 sekund
    Then "footprint" procesu vcs-lite wynosi najwyżej 60 MB

  @AT_VCS_017 @confirmed @REQ_VCS_017 @VER_VCS_007
  Scenario: Samo przeglądanie nie zmienia repozytorium
    Given migawka katalogu ".git" i kopii roboczej
    When użytkownik wybiera repozytorium, ogląda diffy kilku plików i wybiera Refresh
    Then katalog ".git" poza plikiem "index" i kopia robocza są identyczne z migawką
    And zawartość indeksu jest identyczna z migawką

  @AT_VCS_018 @confirmed @UC_VCS_01 @REQ_VCS_001 @DEC_VCS_007 @VER_VCS_008
  Scenario: Settings pokazuje tylko repozytoria z pierwszego poziomu
    Given rootdir zawiera repozytorium "docs"
    And "docs" zawiera zagnieżdżone repozytorium "docs/sessions"
    When użytkownik otwiera Settings
    Then lista zawiera "docs"
    And lista nie zawiera "docs/sessions"

  @AT_VCS_019 @confirmed @UC_VCS_05 @REQ_VCS_021 @DEC_VCS_008 @VER_VCS_008
  Scenario: Commit dotyczy tylko wybranego repozytorium
    Given repozytoria "alpha" i "beta" są obserwowane
    And oba mają pliki w grupie Staged
    When użytkownik wybiera "alpha", wpisuje wiadomość "fix" i wybiera Commit
    Then "alpha" ma nowy commit "fix"
    And liczba commitów w "beta" się nie zmieniła
    And pliki "beta" pozostają w grupie Staged

  @AT_VCS_020 @confirmed @UC_VCS_07 @REQ_VCS_020 @DEC_VCS_014 @DEC_VCS_018 @VER_VCS_009
  Scenario: Pull przesuwa gałąź do upstreamu
    Given "origin/main" ma commit "remote fix", którego brakuje lokalnie
    And lokalna gałąź "main" nie ma własnych commitów ponad "origin/main"
    When użytkownik wybiera Pull
    Then lokalna gałąź "main" zawiera commit "remote fix"

  @AT_VCS_021 @confirmed @UC_VCS_07 @REQ_VCS_020 @DEC_VCS_014 @DEC_VCS_018 @VER_VCS_009
  Scenario: Pull przy rozjechanych gałęziach nie zmienia repozytorium
    Given "origin/main" i lokalna "main" mają różne nowe commity
    When użytkownik wybiera Pull
    Then widoczny jest komunikat gita o niemożliwym fast-forward
    And lokalna gałąź "main" wskazuje ten sam commit co przed Pull
    And nie powstał commit scalający

  @AT_VCS_022 @confirmed @UC_VCS_01 @REQ_VCS_001 @DEC_VCS_016 @VER_VCS_010
  Scenario: Foldery niebędące repozytorium są w Settings ukryte
    Given rootdir zawiera repozytorium "alpha" i zwykły folder "zdjecia"
    When użytkownik otwiera Settings
    Then lista zawiera "alpha"
    And lista nie zawiera "zdjecia"

  @AT_VCS_023 @confirmed @REQ_VCS_022 @DEC_VCS_015 @VER_VCS_010
  Scenario: Szkic wiadomości commita jest osobny dla każdego repozytorium
    Given repozytoria "alpha" i "beta" są obserwowane
    When użytkownik wpisuje w "alpha" wiadomość "wip alpha"
    And przełącza się na "beta" i wpisuje wiadomość "wip beta"
    And wraca do "alpha"
    Then pole wiadomości zawiera "wip alpha"
    And przycisk commita nosi nazwę "Commit do alpha"

  @AT_VCS_024 @confirmed @REQ_VCS_022 @DEC_VCS_020 @VER_VCS_010
  Scenario: Szkic wiadomości nie jest zachowywany po zamknięciu narzędzia
    Given w repozytorium "alpha" pole wiadomości zawiera "wip alpha"
    When narzędzie zostaje zamknięte i uruchomione ponownie
    And użytkownik wybiera "alpha"
    Then pole wiadomości jest puste

  @AT_VCS_025 @confirmed @UC_VCS_03 @REQ_VCS_023 @VER_VCS_011
  Scenario: Brak narzędzia diffu kończy się komunikatem
    Given polecenie narzędzia diffu w ustawieniach wskazuje nieistniejący plik
    When użytkownik otwiera porównanie "app.py" z grupy Changes
    Then widoczny jest komunikat zawierający ścieżkę polecenia
    And narzędzie działa dalej

  @AT_VCS_026 @confirmed @REQ_VCS_023 @DEC_VCS_024 @VER_VCS_011
  Scenario: Narzędzie diffu da się podmienić w ustawieniach
    Given polecenie narzędzia diffu w ustawieniach to ["/usr/local/bin/inny-diff", "{left}", "{right}"]
    When użytkownik otwiera porównanie "app.py" z grupy Changes
    Then uruchomione zostaje "/usr/local/bin/inny-diff" ze ścieżkami obu stron

  @AT_VCS_027 @confirmed @UC_VCS_03 @REQ_VCS_023 @REQ_VCS_017 @VER_VCS_011
  Scenario: Pliki tymczasowe znikają po zamknięciu narzędzia diffu
    Given użytkownik otworzył porównanie "app.py" z grupy Staged
    When okno narzędzia diffu zostaje zamknięte
    Then pliki tymczasowe obu stron nie istnieją
    And repozytorium zostało odświeżone

  @AT_VCS_028 @confirmed @UC_VCS_03 @REQ_VCS_023 @DEC_VCS_039 @VER_VCS_011
  Scenario: Zmiana kopii roboczej w narzędziu diffu jest widoczna po zamknięciu
    Given "app.py" jest w grupie Changes
    And użytkownik otworzył porównanie "app.py" z grupy Changes
    When narzędzie diffu zapisuje w kopii roboczej "app.py" linię "# poprawka"
    And okno narzędzia diffu zostaje zamknięte
    Then plik "app.py" na dysku zawiera linię "# poprawka"
    And repozytorium zostało odświeżone

  @AT_VCS_029 @confirmed @UC_VCS_03 @UC_VCS_04 @REQ_VCS_005 @REQ_VCS_023 @DEC_VCS_040 @VER_VCS_011
  Scenario: Dwuklik otwiera porównanie, a spacja robi stage
    Given "app.py" jest w grupie Changes
    When użytkownik klika dwukrotnie "app.py"
    Then otwiera się porównanie "app.py" z grupy Changes
    And "app.py" pozostaje w grupie Changes
    When użytkownik zaznacza "app.py" i naciska spację
    Then "app.py" jest w grupie Staged
