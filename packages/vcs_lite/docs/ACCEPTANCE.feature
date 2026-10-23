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
