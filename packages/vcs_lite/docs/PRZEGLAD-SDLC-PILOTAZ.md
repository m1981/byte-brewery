# Przegląd SDLC — założenia i plan pilotażu

Data: 2026-10-28. Wersja: 0.1. Status: plan przygotowany; pilotaż niewykonany.

Zlecenie użytkownika: „Zapisz zalozenia i plan pilotazu oraz DoD i spodziewane korzysci do pliku (md) oraz drugi plik (md) jako rejestr zmian”. Szczegóły metody poniżej są propozycją agenta. Dokument nie zmienia obowiązujących wymagań produktu ani zasad współpracy.

Historia zmian i rejestr działań: [PRZEGLAD-SDLC-REJESTR.md](PRZEGLAD-SDLC-REJESTR.md).

## Cel i granice

Sprawdzić, czy nasz proces prowadzi od rzeczywistej potrzeby użytkownika do właściwego rozwiązania i wiarygodnego dowodu jego działania, a następnie wybrać niewielkie usprawnienia o największej wartości. Poprawność identyfikatorów jest warunkiem pomocniczym; nie dowodzi zgodności treści.

Pilotaż obejmuje trzy zmiany w vcs-lite oraz reguły współpracy, które nimi sterowały. Nie jest audytem zgodności z NASA, pełnym przeglądem aplikacji ani upoważnieniem do wdrożenia znalezionych usprawnień. Naprawy produktu i zmiany przyjętych reguł otrzymują osobny zakres i właściwą decyzję.

## Podstawa i założenia

- Materiały wejściowe: lokalne kopie [SWE-052](../../../../docs/sources/swe052.txt), zwłaszcza §3–4, §7–8, oraz [SWE-054](../../../../docs/sources/SWE-054.txt), zwłaszcza §3, §7–8. Ścieżki źródeł: `~/PycharmProjects/docs/sources/`. Ich zgodność z aktualnymi publikacjami NASA nie została potwierdzona. Wykorzystujemy wskazówki, nie deklarujemy spełnienia norm.
- SWE-052 pomaga prześledzić zależności, SWE-054 — zapisać niespójność, przeanalizować jej wpływ i sprawdzić skuteczność naprawy.
- Relacja wymaganie–test nie oznacza pokrycia całego wymagania; wynik testu nie oznacza akceptacji użytkownika. Puste komórki macierzy nie są same w sobie błędem.
- Podstawowa kontrola struktury obejmie cały korpus obsługiwany przez istniejący checker. Ręczna kontrola znaczenia obejmie trzy wybrane zmiany. Wnioski poza tą próbą będą oznaczane jako hipotezy.
- Zgodność dokumentów nie wystarczy, jeżeli wspólnie opisują błędnie zrozumianą potrzebę. Wymagania nie mogą być osłabiane wyłącznie po to, by pasowały do implementacji.
- Historycznej decyzji nie uznajemy za niespójność tylko dlatego, że później ją zmieniono. Sprawdzamy, czy można ustalić obowiązującą wersję i zakres zmiany.
- Agent przygotowuje analizę i dowody; użytkownik rozstrzyga niejasną intencję i zmiany zaakceptowanych zasad. Samokontrola tego samego agenta nie jest niezależnym audytem. Dodatkowy recenzent pozostaje opcją, nie warunkiem pilotażu.

## Próba

| Przypadek | Powód wyboru | Pytania szczególne |
|---|---|---|
| Limit pamięci 85 MiB | Zmiana mierzalnego kryterium | Czy zgoda dotyczy właściwego scenariusza? Czy jednostki, próg, test i dokumentacja są zgodne? Czy odróżniono pomiar bazowy od 3000 plików? |
| Notatki repozytorium | Zachowanie, zapis danych i układ UI | Czy zapis po utracie focusa, przełączenie repo, błąd zapisu i ponowne otwarcie mają odpowiednie dowody? Co potwierdzono automatycznie, a co nadal wymaga oceny wyglądu? |
| Kompaktowe kolorowe liczniki zmian | Ryzyko pomylenia obszarów UI | Czy intencja wskazuje właściwe listy? Czy projekt i testy rozróżniają sumę commita od statystyk pojedynczego pliku? Czy pokrywają zero, dane binarne i brak danych? |

To pytania do sprawdzenia, nie gotowe ustalenia o wadach.

## Plan wykonania

| Etap | Czynności | Wynik |
|---|---|---|
| 1. Ustalenie podstawy | Zapisać SHA badanego commita, datę, wersje środowiska potrzebne do testów i `git status`. Oddzielić stan commita, indeksu oraz zmiany robocze. Zachować diff lub sumy kontrolne analizowanych zmian roboczych. Zanotować wersje/sumy kontrolne dwóch źródeł SWE. | Jednoznaczny opis badanego stanu w tym pliku, w sekcji wyników. |
| 2. Mapa źródeł | Sprawdzić role SPEC, DESIGN, ACCEPTANCE, TRACE, MANUAL-UI, SLOWNIK, WSPOLPRACA, PROMPT-STARTOWY, makiet i zapisów decyzji. Dla każdego wskazać: źródło obowiązujące, historia, dowód lub materiał pomocniczy; właściciela i wyzwalacz aktualizacji. Konfliktu nie rozstrzygać samą datą pliku. | Krótka mapa i jawne konflikty reguł. |
| 3. Kontrola struktury | Uruchomić testy traceability na izolowanej kopii ustalonego stanu. Zachować polecenie, wynik i różnicę wygenerowanego TRACE względem wersji zapisanej. Sprawdzić zakres skanowanych plików. | Wynik automatyczny z ograniczeniami; zielony test nie zastępuje kontroli aktualności TRACE. |
| 4. Trzy ścieżki dowodowe | Dla każdej zmiany przejść: intencja/decyzja → aktualne wymaganie → projekt → kod → weryfikacja → wynik → akceptacja. Wrócić od kodu i testu do uzasadnienia. Sprawdzić również plan, zasoby oraz status zakończenia. | Oceny kryteriów i wskazania konkretnych plików, ID, commitów lub brakujących dowodów. |
| 5. Ocena ustaleń | Oddzielić potwierdzoną niespójność od braku dowodu i pytania. Określić wpływ, priorytet, właściciela, następny krok i warunek zamknięcia. | Wpisy w rejestrze, bez automatycznego uznawania propozycji za zatwierdzoną. |
| 6. Podsumowanie | Wybrać najwyżej trzy usprawnienia; podać korzyść, koszt, sposób sprawdzenia i ryzyko dodatkowej biurokracji. Zapisać ograniczenia próby i decyzję: rozszerzyć, poprawić metodę albo zakończyć. | Wyniki i rekomendacja w tym pliku; działania i ich historia w rejestrze. |

Proponowany budżet pierwszego przebiegu: do 90 minut aktywnej analizy, bez oczekiwania na testy i użytkownika. Po jego wykorzystaniu zapisujemy zakres wykonany i pozostały; limit czasu nie oznacza zaliczenia DoD. Najpierw czytamy zmienione fragmenty i wskazane zależności. Powtarzamy testy tylko wtedy, gdy istniejący wynik nie dotyczy badanej wersji, brakuje go lub ujawniono istotną wątpliwość. Nie uruchamiamy automatycznie całej suity.

## Kryteria oceny każdej zmiany

1. **Intencja i aktualność:** znane źródło potrzeby, zakres zgody i obowiązująca wersja wymagania; propozycje odróżnione od decyzji.
2. **Spójność:** projekt i kod realizują tę samą potrzebę; plan oraz deklarowany status odpowiadają rzeczywistemu zakresowi prac.
3. **Powiązania:** można przejść w obie strony między istotnymi artefaktami; każde powiązanie ma sens, nie tylko poprawny ID.
4. **Weryfikacja:** asercje lub procedura ręczna sprawdzają istotne warunki i odpowiednie przypadki błędne; wskazano, czego nie pokrywają.
5. **Dowód wykonania:** wynik ma wersję, środowisko, datę i rezultat. Odróżniamy test zaplanowany, wykonany i zaliczony oraz akceptację użytkownika.
6. **Obsługa zmiany:** sprawdzono wpływ na zależne dokumenty i testy; niezgodności mają opiekuna i weryfikowalny sposób zamknięcia.

Ocena każdego kryterium: **spełnione / niespełnione / brak dowodu / nie dotyczy**. „Nie dotyczy” wymaga uzasadnienia. „Brak dowodu” nie jest dowodem usterki produktu. Ogólne „wygląda dobrze” nie wystarcza jako uzasadnienie oceny.

## Definition of Done pilotażu

- [ ] Zidentyfikowano badany stan i źródła; wyniki można odnieść do konkretnej wersji.
- [ ] Mapa źródeł odróżnia obowiązujące reguły, historię i propozycje, wskazuje odpowiedzialność oraz wyzwalacze aktualizacji.
- [ ] Zachowano wynik kontroli struktury, zakres checkera i ewentualną różnicę TRACE.
- [ ] Każda z trzech zmian ma ocenę wszystkich sześciu kryteriów z dowodami albo jawnie wskazanym ich brakiem.
- [ ] Wszystkie ustalenia wymagające działania mają wpis, priorytet, właściciela, następny krok i warunek zamknięcia w rejestrze.
- [ ] Wynik rozróżnia: wdrożone, zweryfikowane i zaakceptowane. Nie przypisano użytkownikowi nieudzielonej akceptacji.
- [ ] Wybrano najwyżej trzy rekomendacje z kosztem i sposobem oceny efektu; opisano ograniczenia próby i dalszy krok.
- [ ] Zapisano rzeczywisty nakład pracy i oceniono, czy metoda jest warta powtarzania.

DoD dotyczy zakończenia **przeglądu**, nie usunięcia wszystkich usterek. Otwarte działania mogą pozostać, jeśli są jawne i przypisane. Działanie naprawcze jest zamknięte dopiero po sprawdzeniu jego warunku zamknięcia na wskazanej wersji. Odrzucenie lub odroczenie wymaga uzasadnienia; nie jest naprawą.

## Spodziewane korzyści i sposób ich sprawdzenia

| Oczekiwana korzyść | Jak ją sprawdzimy |
|---|---|
| Mniej realizacji błędnie zrozumianej potrzeby | Czy kontrola intencji ujawnia rozbieżności niewidoczne dla checkera ID? Zapisujemy konkretne przypadki. |
| Łatwiejszy powrót do pracy | Czy dla każdej próby można wskazać obowiązującą regułę, status i następny krok bez rekonstruowania całej rozmowy? |
| Wiarygodniejsze „gotowe” | Ile deklaracji ma dowód dla właściwej wersji, a ile wymaga uzupełnienia lub zmiany statusu? |
| Mniejszy koszt dokumentowania | Mierzymy czas analizy i powtarzane odczyty; wskazujemy duplikaty możliwe do zastąpienia odnośnikiem lub generowaniem. Tokeny raportujemy tylko, jeśli pomiar jest dostępny. |
| Skuteczniejsze naprawy | Przy późniejszej realizacji działań sprawdzamy dowody zamknięcia i nawroty tego samego problemu. |

To hipotezy korzyści. Pierwszy przebieg ustala punkt odniesienia; sam nie dowodzi redukcji kosztów ani liczby błędów. Liczba znalezionych problemów nie jest celem ani miarą jakości recenzenta.

## Wyniki pilotażu

Jeszcze nie wykonano. Przy wykonaniu uzupełnić: badany stan, mapę źródeł, ocenę trzech przypadków, dowody, nakład pracy, ograniczenia i rekomendacje. Do tego czasu pola DoD pozostają nieodhaczone.

## Otwarte

| Temat | Właściciel | Następny krok |
|---|---|---|
| Wykonanie pilotażu | Agent | Po zleceniu wykonania ustalić badaną wersję i rozpocząć etap 1. |
