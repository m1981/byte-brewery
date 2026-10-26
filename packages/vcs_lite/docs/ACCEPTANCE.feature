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

  @AT_VCS_004 @confirmed @UC_VCS_03 @REQ_VCS_003 @REQ_VCS_023 @DEC_VCS_102 @VER_VCS_011
  Scenario: Strona diffu dostaje strony zgodne z grupą pliku
    Given "app.py" ma w indeksie linię "return x * 3" zamiast "return x * 2" z HEAD
    And kopia robocza "app.py" ma dodatkowo linię "# todo"
    When użytkownik otwiera porównanie "app.py" z grupy Staged
    Then strona diffu w przeglądarce dostaje po lewej treść z HEAD, a po prawej treść z indeksu
    When użytkownik otwiera porównanie "app.py" z grupy Changes
    Then strona diffu dostaje po lewej treść z indeksu, a po prawej plik z kopii roboczej

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
  @AT_VCS_007 @confirmed @UC_VCS_03 @REQ_VCS_007 @DEC_VCS_105 @VER_VCS_011
  Scenario: Plik binarny nie ma diffu, ale można go stage'ować
    Given nieśledzony plik "dane.bin" ma zawartość binarną
    When użytkownik klika dwukrotnie "dane.bin"
    Then strona w przeglądarce pokazuje „Brak podglądu zmian” i rozmiar pliku
    And akcja Stage dla "dane.bin" jest dostępna

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
    And repo z 300 zmianami ma 4000 commitów z gałęziami, a panel „Historia” pokazuje jego historię
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

  @AT_VCS_025 @confirmed @UC_VCS_03 @REQ_VCS_023 @DEC_VCS_106 @VER_VCS_011
  Scenario: Brak narzędzia zewnętrznego kończy się komunikatem
    Given polecenie "external_diff_tool" w ustawieniach wskazuje nieistniejący plik
    When użytkownik wybiera z menu kontekstowego „Porównaj w narzędziu zewnętrznym” dla "app.py"
    Then widoczny jest komunikat zawierający ścieżkę polecenia
    And narzędzie działa dalej

  @AT_VCS_026 @confirmed @REQ_VCS_023 @DEC_VCS_106 @VER_VCS_011
  Scenario: Narzędzie zewnętrzne podłącza się wpisem w ustawieniach
    Given ustawienia nie mają "external_diff_tool"
    Then menu kontekstowe "app.py" nie ma pozycji „Porównaj w narzędziu zewnętrznym”
    Given polecenie "external_diff_tool" w ustawieniach to ["/usr/local/bin/inny-diff", "{left}", "{right}"]
    When użytkownik wybiera z menu kontekstowego „Porównaj w narzędziu zewnętrznym” dla "app.py"
    Then uruchomione zostaje "/usr/local/bin/inny-diff" ze ścieżkami obu stron
    And dwuklik na "app.py" nadal otwiera diff w przeglądarce

  @AT_VCS_027 @confirmed @UC_VCS_03 @REQ_VCS_023 @REQ_VCS_017 @VER_VCS_011
  Scenario: Pliki tymczasowe znikają po zapisaniu strony diffu
    Given użytkownik otworzył porównanie "app.py" z grupy Staged
    When proces strony diffu się kończy
    Then pliki tymczasowe obu stron nie istnieją
    And repozytorium zostało odświeżone

  @AT_VCS_028 @confirmed @UC_VCS_03 @REQ_VCS_023 @DEC_VCS_106 @VER_VCS_011
  Scenario: Zmiana kopii roboczej w narzędziu zewnętrznym jest widoczna po zamknięciu
    Given "app.py" jest w grupie Changes, a ustawienia mają "external_diff_tool"
    And użytkownik otworzył „Porównaj w narzędziu zewnętrznym” dla "app.py"
    When narzędzie zapisuje w kopii roboczej "app.py" linię "# poprawka"
    And okno narzędzia zostaje zamknięte
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

  @AT_VCS_030 @confirmed @UC_VCS_04 @REQ_VCS_024 @DEC_VCS_050 @VER_VCS_002
  Scenario: Poprawiony plik w konflikcie można oznaczyć jako rozwiązany
    Given repozytorium "gamma" ma plik "f.txt" w konflikcie po merge
    And użytkownik usunął z "f.txt" znaczniki konfliktu i zapisał plik
    When użytkownik zaznacza "f.txt" i naciska spację
    Then grupa Conflicts jest pusta
    And "f.txt" jest w grupie Staged
    And przycisk commita jest aktywny po wpisaniu wiadomości

  @AT_VCS_031 @confirmed @UC_VCS_04 @REQ_VCS_024 @DEC_VCS_050 @VER_VCS_002
  Scenario: Plik ze znacznikami konfliktu nie zostaje oznaczony
    Given repozytorium "gamma" ma plik "f.txt" w konflikcie po merge
    And "f.txt" nadal zawiera linię "<<<<<<< HEAD" w linii 1
    When użytkownik zaznacza "f.txt" i naciska spację
    Then widoczny jest komunikat zawierający "f.txt" i "linia 1"
    And "f.txt" pozostaje w grupie Conflicts
    And przycisk commita jest nieaktywny

  @AT_VCS_032 @confirmed @REQ_VCS_025 @DEC_VCS_055 @VER_VCS_015
  Scenario: Widok folderów grupuje pliki i jest zapamiętany
    Given repozytorium "alpha" ma nowe pliki "spec-evidence/a.json" i "spec-evidence/b.json" oraz zmieniony "README.md"
    When użytkownik wybiera widok „Foldery”
    Then w grupie Unversioned jest węzeł "spec-evidence" z liczbą „2 pliki” i dwoma plikami pod nim
    And "README.md" w grupie Changes nie ma węzła folderu
    When narzędzie zostaje zamknięte i uruchomione ponownie
    Then wybrany jest widok „Foldery”

  @AT_VCS_033 @confirmed @REQ_VCS_026 @DEC_VCS_056 @VER_VCS_015
  Scenario: Przycisk przy folderze robi stage wszystkich jego plików
    Given widok folderów jest włączony
    And w grupie Unversioned jest węzeł "spec-evidence" z plikami "a.json" i "b.json"
    When użytkownik najeżdża na węzeł "spec-evidence" i klika „+”
    Then "spec-evidence/a.json" i "spec-evidence/b.json" są w grupie Staged
    And grupa Unversioned nie zawiera węzła "spec-evidence"

  @AT_VCS_034 @confirmed @UC_VCS_05 @REQ_VCS_027 @DEC_VCS_065 @VER_VCS_003
  Scenario: Merge rozwiązany do treści HEAD da się zakończyć commitem
    Given w repozytorium trwa merge z konfliktem w "f.txt"
    And użytkownik usunął znaczniki, zostawił treść z HEAD i oznaczył plik spacją jako rozwiązany
    Then repozytorium nie jest pokazane jako czyste, a druga linia w pasku bocznym to „main · merge”
    When użytkownik wpisuje wiadomość "Merge branch 'other'"
    Then Commit jest aktywny, choć grupa Staged jest pusta
    When użytkownik wybiera Commit
    Then powstaje commit scalający z dwoma rodzicami i merge się kończy

  @AT_VCS_035 @confirmed @UC_VCS_04 @REQ_VCS_028 @DEC_VCS_072 @VER_VCS_002
  Scenario: Przegląd plik po pliku: po spacji zaznaczenie przechodzi na następny plik grupy
    Given w grupie Unversioned są "u1.txt", "u2.txt" i "u3.txt"
    And zaznaczony jest "u1.txt"
    When użytkownik naciska spację
    Then do zakończenia operacji zaznaczony pozostaje "u1.txt"
    And po jej zakończeniu "u1.txt" jest w grupie Staged, a zaznaczony jest "u2.txt" w grupie Unversioned
    When użytkownik zaznacza "u3.txt" i naciska spację
    Then zaznaczony jest "u2.txt", bo "u3.txt" był ostatni w grupie

  @AT_VCS_036 @confirmed @UC_VCS_04 @REQ_VCS_029 @DEC_VCS_073 @VER_VCS_002
  Scenario: Zaznaczanie wielu plików jak w Eksploratorze i stage ich jedną spacją
    Given w grupie Unversioned są "u1.txt", "u2.txt", "u3.txt" i "u4.txt"
    When użytkownik klika "u1.txt", a potem z klawiszem Shift klika "u3.txt"
    Then zaznaczone są "u1.txt", "u2.txt" i "u3.txt"
    When użytkownik z klawiszem Ctrl klika "u2.txt"
    Then zaznaczone są "u1.txt" i "u3.txt"
    When użytkownik naciska spację
    Then "u1.txt" i "u3.txt" są w grupie Staged po jednym wywołaniu git add
    And zaznaczony jest "u4.txt"

  @AT_VCS_037 @confirmed @UC_VCS_04 @REQ_VCS_005 @REQ_VCS_029 @DEC_VCS_040 @VER_VCS_002
  Scenario: Menu kontekstowe robi stage zaznaczonych plików
    Given w grupie Unversioned zaznaczone są "u1.txt" i "u2.txt"
    When użytkownik klika prawym przyciskiem "u2.txt"
    Then zaznaczenie się nie zmienia, a menu ma aktywną pozycję „Stage (2)” i nieaktywne „Unstage” oraz „Porównaj”
    When użytkownik wybiera „Stage (2)”
    Then "u1.txt" i "u2.txt" są w grupie Staged

  @AT_VCS_038 @confirmed @UC_VCS_04 @REQ_VCS_030 @DEC_VCS_074 @VER_VCS_002
  Scenario: Zaznaczone pliki poza kontrolą trafiają do .gitignore z menu kontekstowego
    Given w grupie Unversioned są "u1.txt", "u2.txt" i "u3.txt", a repo nie ma pliku .gitignore
    And zaznaczone są "u1.txt" i "u2.txt"
    When użytkownik wybiera z menu kontekstowego „Dodaj do .gitignore (2)”
    Then .gitignore zawiera linie "/u1.txt" i "/u2.txt"
    And grupa Unversioned zawiera ".gitignore" i "u3.txt", a nie zawiera "u1.txt" ani "u2.txt"
    And zaznaczony jest "u3.txt"

  @AT_VCS_039 @confirmed @UC_VCS_03 @REQ_VCS_031 @REQ_VCS_023 @DEC_VCS_102 @VER_VCS_016
  Scenario: Dwuklik na .md otwiera wyrenderowany diff, a na innym pliku tekstowym diff lewo–prawo
    Given plik "README.md" ma w kopii roboczej nowy akapit, a "app.py" jest nowy
    When użytkownik klika dwukrotnie "README.md"
    Then otwiera się wyrenderowany diff "README.md" z tytułem "README.md (kopia robocza)"
    And menu kontekstowe "README.md" nie ma pozycji „Porównaj źródło”
    When użytkownik klika dwukrotnie "app.py"
    Then otwiera się diff lewo–prawo "app.py" w przeglądarce

  @AT_VCS_040 @confirmed @UC_VCS_02 @REQ_VCS_032 @DEC_VCS_089 @DEC_VCS_098 @VER_VCS_015
  Scenario: Widok Projekt pokazuje też pliki bez zmian i otwiera je
    Given repozytorium "alpha" śledzi "docs/plan.md" i "src/app.py" bez zmian oraz ma zmieniony "README.md"
    When użytkownik wybiera widok „Projekt”
    Then grupa Changes zawiera "README.md"
    And pod nią drzewo PROJEKT ma zwinięte foldery "docs" i "src" oraz plik "README.md" w kolorze zmienionego
    When użytkownik rozwija "docs" i klika dwukrotnie "plan.md"
    Then otwiera się wyrenderowany dokument "plan.md" w trybie czytania
    When użytkownik rozwija "src" i klika dwukrotnie "app.py"
    Then "src/app.py" otwiera się w przeglądarce jako strona tekstowa z numerami linii

  @AT_VCS_041 @confirmed @UC_VCS_08 @REQ_VCS_033 @DEC_VCS_093 @VER_VCS_017
  Scenario: Szukanie całego słowa z polskimi literami i maską plików
    Given repozytorium "alpha" śledzi "notatki.md" z linią "Żółw idzie w las" i "src/app.py" z linią "w = 1"
    When użytkownik szuka "w" z opcją „całe słowo” i maską "md"
    Then jedynym trafieniem jest "notatki.md", linia 1, z podświetlonym samym "w" przed "las"
    When użytkownik czyści maskę
    Then trafieniami są "notatki.md" i "src/app.py"
    When użytkownik szuka "ŻÓŁW" z opcją „wielkość liter”
    Then nie ma trafień

  @AT_VCS_042 @confirmed @UC_VCS_08 @REQ_VCS_033 @REQ_VCS_034 @DEC_VCS_095 @DEC_VCS_098 @VER_VCS_017
  Scenario: Enter na trafieniu otwiera plik przy trafionej linii
    Given okno „Szukaj w plikach” pokazuje trafienie w "docs/plan.md", linia 3, i w "src/app.py", linia 1
    When użytkownik naciska Enter na trafieniu w "docs/plan.md"
    Then otwiera się wyrenderowany dokument "docs/plan.md" w trybie czytania przy linii 3
    And okno „Szukaj w plikach” się zamyka
    When użytkownik otwiera okno ponownie i naciska Enter na trafieniu w "src/app.py"
    Then "src/app.py" otwiera się w przeglądarce jako strona tekstowa przy linii 1

  @AT_VCS_043 @confirmed @UC_VCS_08 @REQ_VCS_033 @DEC_VCS_097 @VER_VCS_017
  Scenario: Szukanie rusza po przerwie w pisaniu, a starszy wynik jest odrzucany
    Given okno „Szukaj w plikach” jest otwarte w repozytorium "alpha"
    When użytkownik wpisuje "tyd", a po 100 ms "tydzień"
    Then przez 250 ms od ostatniego znaku nic nie jest szukane
    And potem szukane jest tylko "tydzień"
    When wynik szukania "tyd" przychodzi po wyniku szukania "tydzień"
    Then okno pokazuje wynik szukania "tydzień"
    And przy ponad 500 trafieniach okno pokazuje pierwsze 500 i ostrzeżenie

  @AT_VCS_044 @confirmed @UC_VCS_08 @REQ_VCS_033 @DEC_VCS_097 @VER_VCS_017
  Scenario: Podwójny Shift otwiera okno, Shift z literą albo kliknięciem nie
    Given w oknie głównym wybrane jest repozytorium "alpha"
    When użytkownik naciska i puszcza Shift dwa razy w ciągu 350 ms
    Then otwiera się okno „Szukaj w plikach — alpha” z frazą z poprzedniego otwarcia
    When użytkownik pisze wielką literę, a potem naciska i puszcza Shift raz
    Then okno się nie otwiera
    When użytkownik klika z Shift, a potem naciska i puszcza Shift raz
    Then okno się nie otwiera

  @AT_VCS_045 @confirmed @UC_VCS_03 @REQ_VCS_034 @DEC_VCS_100 @VER_VCS_011
  Scenario: Typ pliku decyduje, gdzie się otwiera
    Given repozytorium "alpha" ma zmieniony "logo.png", w Staged nową wersję "ikona.png", nieśledzony "opis.pdf", niezmienione "notatki.txt" i "archiwum.zip"
    When użytkownik klika dwukrotnie "logo.png" w grupie Changes
    Then plik "logo.png" z kopii roboczej otwiera się w domyślnej przeglądarce
    When użytkownik klika dwukrotnie "ikona.png" w grupie Staged
    Then w domyślnej przeglądarce otwiera się kopia "ikona.png" z indeksu
    When użytkownik klika dwukrotnie "opis.pdf" w grupie Unversioned
    Then plik "opis.pdf" otwiera się w domyślnej przeglądarce
    When użytkownik w drzewie PROJEKT klika dwukrotnie "notatki.txt", a potem "archiwum.zip"
    Then "notatki.txt" otwiera się jako strona tekstowa, a "archiwum.zip" w domyślnej aplikacji
    When użytkownik wybiera z menu kontekstowego „Otwórz w aplikacji” dla "logo.png"
    Then "logo.png" otwiera się w domyślnej aplikacji macOS

  @AT_VCS_046 @confirmed @UC_VCS_03 @REQ_VCS_023 @DEC_VCS_103 @VER_VCS_011
  Scenario: Diff lewo–prawo pokazuje zmienione linie obok siebie
    Given w "app.py" linia 2 zmienia "return x * 2" na "return x * 3", linia 30 jest usunięta, a reszta z 60 linii jest bez zmian
    When użytkownik otwiera porównanie "app.py" z grupy Changes
    Then strona ma po lewej i po prawej numery linii, a wiersz linii 2 ma podkreślone "2" po lewej i "3" po prawej
    And wiersz linii 30 ma po prawej stronie zakreskowane pole
    And niezmienione linie dalej niż 3 od zmiany są zwinięte z liczbą linii

  @AT_VCS_047 @confirmed @REQ_VCS_104 @DEC_VCS_110 @VER_VCS_018
  Scenario: vcs-lite jako aplikacja macOS z logo
    Given "assets/logo.png" jest kwadratowym logo bez przezroczystości
    When użytkownik uruchamia "tools/make_app.py" z katalogiem docelowym
    Then w katalogu jest "vcs-lite.app" z nazwą "vcs-lite", ikoną "vcs-lite.icns" i programem uruchamiającym vcs-lite z byte-brewery
    And ikona ma przezroczyste rogi i margines, a środek pochodzi z logo
    When użytkownik uruchamia "tools/make_app.py" ponownie
    Then "vcs-lite.app" zostaje zastąpiona nową
    And obca "vcs-lite.app" w tym katalogu nie zostaje zastąpiona

  @AT_VCS_048 @confirmed @UC_VCS_02 @REQ_VCS_035 @DEC_VCS_113 @DEC_VCS_115 @VER_VCS_019
  Scenario: Prawy przycisk na repo kopiuje adres zdalnego repo
    Given wybrane jest repo "alpha", a repo "beta" ma zdalne "upstream" i "origin" z adresem "git@github.com:m1981/beta.git"
    When użytkownik klika prawym przyciskiem kafelek "beta"
    Then w schowku jest "https://github.com/m1981/beta.git", menu się nie otwiera, a wybrane zostaje "alpha"
    When użytkownik klika prawym przyciskiem kafelek repo bez zdalnego
    Then schowek się nie zmienia i słychać sygnał systemu

  # ---------- Historia (UC-VCS-09, PROPOZYCJA-historia.md, reguły H-01–H-49) ----------
  # Kształty historii zapisane jak „A ← B” (B ma rodzica A); kolumny grafu liczone od 0.

  @AT_VCS_049 @confirmed @UC_VCS_09 @REQ_VCS_036 @DEC_VCS_118 @VER_VCS_020
  Scenario: Panel historii jest zawsze widoczny pod listą plików i panelem commita
    Given okno vcs-lite z wybranym repo
    Then panel „Historia” zajmuje całą szerokość nad paskiem stanu i nie ma przycisku zamknięcia
    And panel commita leży pod listą plików, a pasek repozytoriów sięga do panelu historii
    When użytkownik przeciąga granicę tak, że historia miałaby 60 pt
    Then historia ma 120 pt
    When użytkownik ustawia historię na 300 pt i uruchamia vcs-lite ponownie
    Then historia ma 300 pt

  @AT_VCS_050 @confirmed @UC_VCS_09 @REQ_VCS_038 @VER_VCS_020
  Scenario: Historia liniowa to jedna prosta linia
    Given historia A ← B ← C
    Then wiersze to C, B, A, wszystkie w kolumnie 0, w jednym kolorze
    And tor kończy się na kropce A

  @AT_VCS_051 @confirmed @UC_VCS_09 @REQ_VCS_038 @VER_VCS_020
  Scenario: Gałąź scalona przez merge
    Given historia A ← B ← M i A ← F1 ← F2 ← M, gdzie M ma rodziców B i F2
    Then M stoi w kolumnie 0 i ma łuk do nowego toru w kolumnie 1
    And F2 i F1 stoją w kolumnie 1, B w kolumnie 0
    And tor z kolumny 1 kończy się łukiem na A w kolumnie 0
    And kolumna 1 ma inny kolor niż kolumna 0

  @AT_VCS_052 @confirmed @UC_VCS_09 @REQ_VCS_038 @VER_VCS_020
  Scenario: Dwie gałęzie wychodzą z jednego commita i nie są scalone
    Given historia A ← B (main) i A ← X (feature), kolejność wierszy X, B, A
    Then X stoi w kolumnie 0, B w kolumnie 1
    And A stoi w kolumnie 0, a tor z kolumny 1 dochodzi do A łukiem i się kończy

  @AT_VCS_053 @confirmed @UC_VCS_09 @REQ_VCS_038 @VER_VCS_020
  Scenario: Merge ośmiornicy z rodzicem, na którego już czeka tor
    Given merge O z rodzicami P1, P2, P3, P4, a nad O czubek Y z rodzicem P3
    Then O ma łuki do toru Y (który czeka na P3) oraz do nowych torów P2 i P4
    And żadna linia nie przechodzi przez kropkę innego commita

  @AT_VCS_054 @confirmed @UC_VCS_09 @REQ_VCS_038 @VER_VCS_020
  Scenario: Niezwiązane historie i płytki klon
    Given repo z gałęzią main (A ← B) i gałęzią docs utworzoną przez --orphan (D1 ← D2)
    Then obie historie są rysowane osobno, bez łuku między nimi, a tory kończą się na A i na D1
    Given płytki klon, którego najstarszy commit ma etykietę grafted
    Then ten commit jest rysowany jak korzeń, bez etykiety „grafted”

  @AT_VCS_055 @confirmed @UC_VCS_09 @REQ_VCS_038 @VER_VCS_020
  Scenario: Graf jest dokładany przy kolejnej stronie
    Given historia z gałęzią, której początek leży poniżej pierwszych 500 commitów
    When użytkownik przewija listę do końca pierwszej strony
    Then tor gałęzi biegnie do dołu pierwszej strony, a po wczytaniu drugiej kończy się na właściwym commicie
    And wiersze pierwszej strony nie zmieniają kolumn ani kolorów
    And układ dla całej historii naraz jest taki sam jak po dwóch stronach

  @AT_VCS_056 @confirmed @UC_VCS_09 @REQ_VCS_038 @VER_VCS_020
  Scenario: Szeroki graf jest przycięty do ośmiu kolumn
    Given dziesięć gałęzi wychodzących z jednego commita i niescalonych
    Then graf ma szerokość ośmiu kolumn
    And commity z kolumn 9 i 10 mają puste w środku kropki w ósmej kolumnie, bez swoich linii

  @AT_VCS_057 @confirmed @UC_VCS_09 @REQ_VCS_037 @VER_VCS_020
  Scenario: Etykiety, zakres i niewypchnięte commity
    Given repo z gałęzią main śledzącą origin/main, dwoma commitami nad origin/main, tagiem v1, schowkiem (stash) i notatką
    Then lista nie zawiera commitów schowka ani notatki
    And dwa najnowsze commity mają znacznik ↑ i pogrubiony tytuł
    And etykieta main jest oznaczona jako bieżąca, origin/main jako zdalna, v1 jako tag, bez origin/HEAD
    Given lokalna gałąź o nazwie "origin/fake"
    Then jej etykieta jest gałęzią lokalną

  @AT_VCS_058 @confirmed @UC_VCS_09 @REQ_VCS_037 @VER_VCS_020
  Scenario: Puste repo, błąd i odświeżenie z zachowaniem zaznaczenia
    Given świeże repo bez commitów
    Then panel pokazuje „Repo nie ma jeszcze commitów”, a git nie dostaje argumentu HEAD
    Given repo z historią i zaznaczonym commitem C
    When użytkownik robi nowy commit
    Then historia jest czytana na nowo, nowy commit jest na górze, a C nadal jest zaznaczony
    When użytkownik robi amend zaznaczonego commita
    Then zaznaczony jest pierwszy wiersz
    And przez cały czas Commit i Pull nie czekają na odczyt historii

  @AT_VCS_059 @confirmed @UC_VCS_09 @REQ_VCS_039 @VER_VCS_020
  Scenario: Filtr szuka w wiadomości, autorze i hashu i pokazuje listę bez linii grafu
    Given commity „fix parser” autora Ola, „docs” autora Ola i „fix ui” autora Michal
    When użytkownik wpisuje "ola"
    Then po 250 ms lista ma „fix parser” i „docs”
    When użytkownik wpisuje "fix"
    Then lista ma „fix parser” i „fix ui”, a graf ma tylko kropki w jednej kolumnie
    When użytkownik wpisuje pierwsze 7 znaków hasha „docs”
    Then lista ma tylko „docs”

  @AT_VCS_060 @confirmed @UC_VCS_09 @REQ_VCS_040 @VER_VCS_020
  Scenario: Pliki commita, diff i menu commita
    Given zaznaczony merge M z rodzicami B i F2, zdalny origin "git@github.com:m1981/app.git"
    Then pliki M to zmiany względem B
    When użytkownik klika dwukrotnie plik "a.py" z listy plików M
    Then w przeglądarce otwiera się diff "a.py" z B po lewej i z M po prawej
    When użytkownik wybiera z menu M „Kopiuj adres commita”
    Then w schowku jest "https://github.com/m1981/app/commit/<pełny hash M>"
    Given zaznaczony pierwszy commit repo
    Then jego pliki są wszystkie dodane

  @AT_VCS_061 @confirmed @UC_VCS_09 @REQ_VCS_041 @DEC_VCS_124 @VER_VCS_020
  Scenario: Pokaż historię pliku z listy zmian, także po zmianie nazwy
    Given plik "b.txt" powstał przez zmianę nazwy "a.txt" i ma 4 commity, a w repo są też inne commity
    When użytkownik wybiera „Pokaż historię” w menu kontekstowym "b.txt" w grupie Changes
    Then panel „Historia” pokazuje tylko 4 commity pliku, bez linii grafu, ze znacznikiem „Plik: b.txt ✕”
    When użytkownik klika dwukrotnie najstarszy commit
    Then w przeglądarce otwiera się diff pliku "a.txt" z tego commita
    When użytkownik klika znacznik
    Then panel pokazuje całą historię z grafem

  @AT_VCS_062 @confirmed @UC_VCS_09 @REQ_VCS_041 @DEC_VCS_124 @VER_VCS_020
  Scenario: Historia folderu i historia pliku razem z filtrem
    Given folder "docs" z plikami zmienianymi w kilku commitach
    When użytkownik wybiera „Pokaż historię” na folderze "docs" w drzewie PROJEKT
    Then panel pokazuje commity zmieniające cokolwiek w "docs", ze znacznikiem „Folder: docs ✕”
    When użytkownik wpisuje w filtr tekst z wiadomości jednego z nich
    Then lista ma tylko commity spełniające oba warunki
    When użytkownik wybiera inne repo
    Then panel pokazuje całą historię tego repo

  @AT_VCS_063 @confirmed @UC_VCS_09 @REQ_VCS_041 @DEC_VCS_124 @VER_VCS_020
  Scenario: Plik bez historii i historia pliku z panelu historii
    Given plik "nowy.txt" w grupie Unversioned
    Then pozycja „Pokaż historię” w jego menu jest nieaktywna
    Given zaznaczony commit z plikiem "a.py" w szczegółach
    When użytkownik wybiera „Pokaż historię” w menu pliku "a.py" w szczegółach
    Then panel pokazuje historię "a.py"

  @AT_VCS_064 @confirmed @REQ_VCS_042 @VER_VCS_021
  Scenario: Ostatnie zapisy i grupy czasu
    Given zmienione pliki z czasami zapisu, remisami i usunięty plik bez czasu
    When użytkownik otwiera widok Zmiany
    Then każdy status jest sortowany od najnowszego zapisu, przy remisie po pełnej ścieżce
    And nowa sekcja zaczyna się po przerwie ponad 5 minut lub rozpiętości ponad 15 minut
    And pliki bez czasu są na końcu w sekcji „Czas nieznany”
    And etykieta pokazuje wiek najnowszego pliku, a dymek pełny zakres i liczbę plików

  @AT_VCS_065 @confirmed @REQ_VCS_043 @VER_VCS_021
  Scenario: Liczby linii względem stron statusu Git
    Given częściowo staged plik, plik dodany, usunięty, przemianowany i binarny
    Then Staged pokazuje liczby HEAD do indeksu, Changes indeks do dysku, Unversioned wszystkie dodane linie
    And rename bez zmiany treści pokazuje +0 −0, binarny „binarne”, konflikt „konflikt”
    And błąd odczytu daje „—” z wyjaśnieniem, a nie fałszywe zera
    And odczyt nie zmienia indeksu i nie uruchamia zewnętrznych narzędzi diff ani textconv

  @AT_VCS_066 @confirmed @REQ_VCS_042 @REQ_VCS_043 @REQ_VCS_028 @VER_VCS_021
  Scenario: Kolumna liczb i przegląd plików przez separatory
    Given zaznaczony plik w widoku Zmiany z separatorami czasu
    When następuje odświeżenie z nową kolejnością plików
    Then zaznaczenie pozostaje przy tym samym pliku
    When użytkownik naciska spację
    Then zaznaczenie przechodzi do następnego widocznego pliku, pomijając separatory
    And liczby są wyrównane w stałej prawej kolumnie także przy długich nazwach i wąskiej liście
    And widoki Foldery i Projekt zachowują dotychczasowy układ


  @AT_VCS_067 @proposal @REQ_VCS_105 @VER_VCS_022
  Scenario: Widoczne okno zachowuje responsywność przy 3000 zmienionych plików
    Given repo tymczasowe z 3000 zmienionych plików i historią 4000 commitów
    And rzeczywiste okno jest widoczne i utrzymywane topmost przez cały pomiar
    When użytkownik najeżdża na wiersze, przewija do środka i końca, wybiera plik i używa strzałek
    And zmienia widoki i rozmiar okna oraz odświeża repo
    Then wszystkie 3000 plików są dostępne, wybór i kolumna liczb pozostają poprawne
    And na Canvas są tylko obiekty widocznego obszaru z niewielkim zapasem
    And interakcje i przerwy pętli zdarzeń mieszczą się w 0,5 s, odświeżenie w 2 s, pamięć w 100 MiB
