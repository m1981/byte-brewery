# Przegląd SDLC — założenia i plan pilotażu

Data: 2026-10-28. Wersja: 1.0. Status: etapy 1–6 zakończone; przegląd zamknięty, naprawy otwarte.

Zlecenie użytkownika: „Zapisz zalozenia i plan pilotazu oraz DoD i spodziewane korzysci do pliku (md) oraz drugi plik (md) jako rejestr zmian”. Metodę zaproponował agent; użytkownik zaakceptował pilotaż 2026-10-28. Dokument nie zmienia obowiązujących wymagań produktu ani zasad współpracy.

Historia zmian i rejestr działań: [PRZEGLAD-SDLC-REJESTR.md](PRZEGLAD-SDLC-REJESTR.md).

**Bieżący stan (2026-10-29):** pilotaż zakończony; [wynik końcowy i trzy rekomendacje](#etap-6--podsumowanie-i-zakończenie-pilotażu) poniżej. Po pilotażu zamknięto PIL-U-001–007: pięć zaplanowanych przyrostów wykonane. Osobno pozostają próby wizualne 29/30; dalsza praca wraca do przeglądu zakresu konkretnej zmiany. Dowody i kryteria w [rejestrze](PRZEGLAD-SDLC-REJESTR.md#ustalenia-i-działania). Dawne etapy są historią wyników.

**Gdzie zajrzeć:** DoD poniżej określa odbiór całego przeglądu; [rejestr — etap 5](PRZEGLAD-SDLC-REJESTR.md#etap-5--plan-działań-po-ocenie-dowodów) zawiera kolejność, koszt i warunki zamknięcia działań. Szczegółowe logi czytać dopiero przy sprawdzaniu konkretnego dowodu.

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

- [x] Zidentyfikowano badany stan i źródła; wyniki można odnieść do konkretnej wersji.
- [x] Mapa źródeł odróżnia obowiązujące reguły, historię i propozycje, wskazuje odpowiedzialność oraz wyzwalacze aktualizacji.
- [x] Zachowano wynik kontroli struktury, zakres checkera i ewentualną różnicę TRACE.
- [x] Każda z trzech zmian ma ocenę wszystkich sześciu kryteriów z dowodami albo jawnie wskazanym ich brakiem.
- [x] Wszystkie ustalenia wymagające działania mają wpis, priorytet, właściciela, następny krok i warunek zamknięcia w rejestrze.
- [x] Wynik rozróżnia: wdrożone, zweryfikowane i zaakceptowane. Nie przypisano użytkownikowi nieudzielonej akceptacji.
- [x] Wybrano najwyżej trzy rekomendacje z kosztem i sposobem oceny efektu; opisano ograniczenia próby i dalszy krok.
- [x] Zapisano rzeczywisty nakład pracy i oceniono, czy metoda jest warta powtarzania — nakład oszacowany, bez dokładnego pomiaru; ograniczenie w etapie 6.

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

### Etap 1 — ustalenie podstawy (wykonany)

Akceptacja użytkownika 2026-10-28: „akceptuje pilotarz wykonaj etap 1 (chyba ze cos przeoczylem)”. Zatwierdzono pilotaż; bieżące wykonanie ograniczono do etapu 1. Nie stwierdzono brakującego warunku uniemożliwiającego ustalenie podstawy.

**Moment zapisu:** 2026-10-28T22:39:22+01:00. Repozytorium: `/Users/michal/PycharmProjects/byte-brewery`; pakiet: `packages/vcs_lite`; gałąź: `main`.

**Badana wersja bazowa:** `c19208dd4ce797ec5183c3127e832c5282a30aba`. To commit zawierający plan v0.1. Późniejsze commity z wynikami przeglądu nie przesuwają automatycznie tej podstawy. Ewentualna zmiana podstawy wymaga wpisu w rejestrze.

**Rozdzielenie stanów (decyzja wykonawcza agenta):** kod i testy badamy z powyższego commita. Dwie zastane zmiany użytkownika stanowią osobną warstwę kontekstu: robocza wersja PROMPT-STARTOWY będzie uwzględniona przy mapie instrukcji, a zmiana `.gitignore` jest zarejestrowana, lecz nie wpływa na wybrane trzy przypadki. Nie włączamy tych zmian do commita dokumentującego przegląd. Dokumenty wynikowe tego przeglądu nie są dowodem wcześniejszego działania procesu.

Status przed edycją dokumentów wynikowych (`git status --short`, ścieżki od korzenia repo):

```text
M  .gitignore
 M packages/vcs_lite/docs/PROMPT-STARTOWY.md
```

Indeks: dodano jedną regułę ignorowania `.DS_Store`. Katalog roboczy: usunięto pięć końcowych wierszy starej listy następnych kroków z PROMPT-STARTOWY. Poza tym `git status` nie wykazał zmian śledzonych ani plików nieśledzonych; pliki ignorowane nie są objęte tym stwierdzeniem.

Zachowane różnice pozwalające odtworzyć obie warstwy na bazie badanego commita (diff promptu bez kontekstu; przy odtwarzaniu przez `git apply` wymaga `--unidiff-zero`):

```diff
diff --git a/.gitignore b/.gitignore
index 8df88a7..cecf2e3 100644
--- a/.gitignore
+++ b/.gitignore
@@ -41,3 +41,4 @@ frontend/.streamlit/secrets.toml
 /bin/node_modules/.package-lock.json
 /bin/package-lock.json
 /my-chats/
+/packages/vcs_lite/assets/.DS_Store
```

```diff
diff --git a/packages/vcs_lite/docs/PROMPT-STARTOWY.md b/packages/vcs_lite/docs/PROMPT-STARTOWY.md
index 431f809..f1aee40 100644
--- a/packages/vcs_lite/docs/PROMPT-STARTOWY.md
+++ b/packages/vcs_lite/docs/PROMPT-STARTOWY.md
@@ -32,5 +31,0 @@ Ustalenia techniczne:
-Następny krok według „Punktu wznowienia”:
-1. „Szukaj w plikach” (REQ-VCS-033) i przeglądarka zamiast Beyond Compare (REQ-VCS-023, REQ-VCS-034) gotowe i potwierdzone na ekranie (kroki 16, 6, 17).
-2. Adres zdalnego repo do schowka prawym przyciskiem na kafelku (REQ-VCS-035): gotowe i potwierdzone (krok 19). Katalog packages/vcs_lite/assets/ nie pochodzi od agenta; nie ruszaj bez pytania.
-3. Panel „Historia” (DEC-VCS-116–119): plan kroków 0–7 i reguły H-01–H-49 w docs/PROPOZYCJA-historia.md (czytaj przed pracą nad historią); stan w „Punkcie wznowienia” 2d.
-4. Na przyszłość (bez terminu): własne okno podglądu plików (Q-VCS-056).
```

Sumy SHA-256 policzono z surowych bajtów, bez normalizacji końców linii:

| Artefakt | Stan | Bajty | SHA-256 |
|---|---|---:|---|
| `.gitignore` | HEAD | 659 | `514ef5a422b5c4a71673e5f2eea1dfcc2284edc17c7c38724a3ad1869c3a38ab` |
| `.gitignore` | indeks | 695 | `48081f997efa8330588dc573cca7ddb9c18bff7d452936eb561f4477260484af` |
| `.gitignore` | katalog roboczy | 695 | `48081f997efa8330588dc573cca7ddb9c18bff7d452936eb561f4477260484af` |
| `packages/vcs_lite/docs/PROMPT-STARTOWY.md` | HEAD | 5658 | `c2829cb55771c177cf1b55aedf4d7f6d310e43a94838417a073a91a0d9a4f732` |
| `packages/vcs_lite/docs/PROMPT-STARTOWY.md` | indeks | 5658 | `c2829cb55771c177cf1b55aedf4d7f6d310e43a94838417a073a91a0d9a4f732` |
| `packages/vcs_lite/docs/PROMPT-STARTOWY.md` | katalog roboczy | 4990 | `0cfbbea494aa9c8b9b17c249a763c51bbdd7057c1fa8637c5167f9053be0e76a` |

### Środowisko i źródła

| Element | Zaobserwowany stan |
|---|---|
| System / architektura | macOS 26.2 / arm64 |
| Python | 3.12.11; `/Users/michal/PycharmProjects/byte-brewery/.venv/bin/python` |
| pytest | 9.0.2 |
| Tcl | 8.6.14 (`tkinter.Tcl().eval('info patchlevel')`) |
| Tk | 8.6 — wartość `tkinter.TkVersion`; nie ustalano wersji poprawkowej załadowanego GUI |
| Git | 2.47.1 |

Nie uruchamiano pomiarów produktu ani testów GUI w etapie 1. Przed późniejszym pomiarem pamięci należy zapisać rzeczywiste warunki wykonania i wersję Tk uruchomionego okna; same powyższe wersje nie gwarantują odtworzenia wyniku pamięci.

| Plik | Bajty | SHA-256 |
|---|---:|---|
| `/Users/michal/PycharmProjects/docs/sources/swe052.txt` | 99323 | `0d74fda4cb26ba7e01324efee9de9c963b40e6a187fe67cff901338b7c9f0006` |
| `/Users/michal/PycharmProjects/docs/sources/SWE-054.txt` | 46830 | `6528f5f2ef46faaa7fa3589331cc4f3394f84d3e81a5748c3fd196b0343d1894` |
| `/Users/michal/PycharmProjects/byte-brewery/uv.lock` | 228132 | `84a637ed71004c0f8591981c5fcf3f8626307a774030d397c4560e7cd32c06ea` |
| `/Users/michal/PycharmProjects/byte-brewery/packages/vcs_lite/pyproject.toml` | 440 | `d651e154aa4ebeed4fbf4b5dc18f7369eda163a29ae33a3b60d2c337731afa47` |

Wersje źródeł SWE identyfikuje tu zawartość lokalnych kopii, nie numer aktualnego wydania internetowego. SWE-052 ma nagłówek „SW Engineering Handbook Ver D”; SWE-054 zawiera adnotację redakcyjną z 2024-06-24, która nie dowodzi daty publikacji całej kopii. Nie sprawdzano autentyczności ani aktualności względem serwisu NASA. Źródła pozostają w sąsiednim repozytorium; przed kolejnym etapem należy porównać ich sumy, a przy zmianie zachować dostęp do tej wersji lub jawnie zmienić podstawę.

### Zakres zakończony i ograniczenia

Etap 1 zakończony: zapisano bazę, kontekst roboczy, różnice, środowisko i identyfikację źródeł. Etapy 2–6 pozostają niewykonane. Nie wydano ocen trzech przypadków ani ocen zgodności procesu. Nakład etapu 1: około 5 minut aktywnej pracy agenta (szacunek, bez pomiaru tokenów). Kontrola dokumentacji przed commitem służy weryfikacji tego przyrostu i nie zastępuje etapu 3 na ustalonej bazie.


### Etap 2 — mapa źródeł (wykonany)

Zlecenie: „wykonaj rzetelnie Etap 2 i caly czas pamietaj o «Spodziewane korzyści i sposób ich sprawdzenia»”. Analiza 2026-10-28 na bazie `c19208dd4ce797ec5183c3127e832c5282a30aba`, bez przesunięcia podstawy. Odczytano dokumenty bezpośrednio z tego commita do kopii roboczej przeglądu i sprawdzono zgodność z plikami bieżącymi. Wyjątek: PROMPT-STARTOWY w wariancie roboczym opisanym w etapie 1. Ponownie policzone SHA-256 obu źródeł SWE oraz roboczego promptu zgadzają się z etapem 1. Nie wykonywano napraw dokumentów wejściowych.

#### Mapa odpowiedzialności i aktualizacji

„Właściciel” poniżej rozdziela redakcję od decyzji. Role użytkownika i agenta wynikają z WSPOLPRACA §Zasady 1–6, promptu oraz MANUAL-UI §Przygotowanie. Tam, gdzie dokument nie ustala odrębnej procedury aktualizacji, wyzwalacz oznaczono **proponowany** — mapa nie ustanawia go automatycznie jako nowej reguły.

| Źródło | Rola i granica wiarygodności | Odpowiedzialność | Wyzwalacz aktualizacji |
|---|---|---|---|
| Rozmowa użytkownika, cytaty i DEC w [SPEC](SPEC.md) | Źródło intencji i zgody; cytat wymaga kontekstu oraz zakresu. Późniejsza jawna zmiana decyzji zastępuje wcześniejszą w tym zakresie. DEC nie dowodzi wykonania. | Użytkownik decyduje; agent zapisuje cytat, zakres i powiązania. | Decyzja lub doprecyzowanie, przed implementacją — prompt §Zasady pracy. |
| [SPEC](SPEC.md): NEED, REQ, OUT, VER, DoD, Q | Potrzeba, obowiązujące zachowanie, zakres, plan weryfikacji i otwarte decyzje. Status „Potwierdzone” przy wymaganiu nie jest wynikiem testu. Historyczne DEC/Q/OBS zachowują datę i kontekst. | Agent redaguje; użytkownik akceptuje zmianę przyjętej potrzeby/zakresu. | Nowa lub zmieniona potrzeba, odpowiedź na pytanie; przed kodem. |
| SPEC: „Punkt wznowienia” | Miał być źródłem aktualnego statusu i następnego kroku; faktycznie zawiera też chronologiczną historię. Trzeba czytać późniejsze dopiski i osobną sekcję P21. | Agent utrzymuje; użytkownik potwierdza wykonane przez siebie próby. | Odłożenie tematu lub zakończenie etapu — WSPOLPRACA §5–6. Konflikt funkcji bieżącej i historycznej: PIL-U-003. |
| [DESIGN](DESIGN.md) | Przyjęty sposób realizacji i ograniczenia; uzasadnia kod, nie zastępuje potrzeby ani pomiaru. Wstęp wskazuje SPEC oraz wspólny rejestr pytań. | Agent projektuje; użytkownik zatwierdza zmianę zaakceptowanych założeń. | REQ/DES przed implementacją; zmiana rozwiązania w toku pracy wymaga uzgodnienia dokumentu z rozwiązaniem. |
| [ACCEPTANCE.feature](ACCEPTANCE.feature) | Scenariusze oczekiwanego zachowania. Nagłówek wprost: `@confirmed` = potwierdzona potrzeba, nie zaliczony test. Brak adaptera kroków; testy są w pytest. | Agent zapisuje scenariusze; użytkownik potwierdza potrzebę. | Zmiana zachowania i scenariusza, przed kodem; wyniku wykonania nie zapisuje się zmianą tagu. |
| [TRACE](TRACE.md) | Generowany indeks powiązań, przydatny do nawigacji; nie jest źródłem wymagań ani raportem wyników testów. | Generator; agent odpowiada za uruchomienie i przegląd różnicy. | Uruchomienie testu generującego po zmianie wejść. Bez ręcznej edycji — nagłówek TRACE. |
| [MANUAL-UI](MANUAL-UI.md) | Procedury ręczne i zapis przyjętych fragmentów UI. Zakres potwierdzenia wynika z danego kroku, nie z ogólnej pochwały aplikacji. | Agent przygotowuje i zapisuje wynik; użytkownik wykonuje próby/dostarcza zrzut. | Nowy przypadek ręczny; odpowiedź użytkownika lub zrzut — §Zrzuty ekranu. |
| [SLOWNIK](SLOWNIK.md) | Jedno źródło znaczeń i nazw A–F, rozróżnia listę commitów, plików commita i zmian. Zawiera też opis układu/statusu P21, który powtarza inne dokumenty. | Agent utrzymuje uzgodnione pojęcia, użytkownik doprecyzowuje znaczenie. | Pierwsze uzgodnienie nowego pojęcia — §Jak używamy słownika. Dla duplikatów statusu brak osobnego wyzwalacza. |
| [WSPOLPRACA](WSPOLPRACA.md) | Przyjęta konwencja komunikacji i decyzji, wskazana przez prompt jako nadrzędna. Ma nieaktualną regułę commitów, PIL-U-001. | Użytkownik ustala współpracę; agent zapisuje reguły. | **Proponowany:** każda zaakceptowana zmiana sposobu pracy, w tym aktualizacja zastąpionego zapisu. |
| [PROMPT-STARTOWY](PROMPT-STARTOWY.md), wariant roboczy | Punkt wejścia: lektury, polecenia i pułapki techniczne. Kopiuje progi, zakresy ID i wyniki, przez co częściowo jest nieaktualny; nie może rozstrzygać progu produktu wbrew DEC. | Agent redaguje; zastane zmiany użytkownika pozostają jego zmianami. | RETROSPEKTYWA zaleca aktualizację liczby testów i dokumentów; brak automatycznej synchronizacji. PIL-U-002. |
| [UI-REFERENCE](ui-reference/UI-REFERENCE.md) i wskazane makiety | Rejestr zaakceptowanych wzorców: P21 na początku, P20, dalej starsze E. Konkretna decyzja i zakres korekty określają obowiązywanie; nazwa lub data pliku nie wystarczy. Makieta HTML nie dowodzi działania zapisu na dysku. | Agent tworzy; użytkownik akceptuje wygląd/odstępstwo. | Zmiana UI → makieta przed kodem; odstępstwo wpisane do wzorca — UI-REFERENCE, wstęp E-01. |
| `PROPOZYCJA-*.md` | Analizy, alternatywy, niekiedy przyjęte reguły: np. SPEC odsyła do H-01–H-49 historii i R-09–R-13 grup czasowych. Sama nazwa PROPOZYCJA nie unieważnia części przyjętej przez DEC. | Agent opracowuje; użytkownik zatwierdza zakres. | **Proponowany:** przy decyzji oznaczyć przyjęte części i odsyłać do aktualnego REQ; pozostawić warianty historyczne. |
| [RETROSPEKTYWA](RETROSPEKTYWA.md) | Opis sesji 22–23 października i wnioski; stare liczby i „commit na polecenie” są historią, nie bieżącym nakazem. | Agent opracowuje na zlecenie użytkownika. | Kolejna retrospektywa lub korekta faktu; nie przepisywać historii do obecnego stanu. |
| Kod, testy, Git i logi wykonania | Kod pokazuje implementację, test treść sprawdzenia, Git wersję; dopiero log związany z wersją i warunkami pokazuje wynik. Sam commit i nazwa testu nie dowodzą poprawności. | Agent implementuje i gromadzi dowody; użytkownik dostarcza dowody prób ręcznych. | Zmiana kodu/testu i każde wykonanie weryfikacji. Pełny log oraz test indeksu wymagane przez prompt. |

Źródła SWE są materiałem do zaprojektowania metody, nie nadrzędnymi wymaganiami produktu. Plan i rejestr pilotażu są wynikami bieżącego przeglądu, nie dowodami poprawności dawnych przyrostów.

#### Jak rozstrzygamy źródło w tym przeglądzie

Najpierw ustalamy rodzaj pytania (intencja, zachowanie, wygląd, realizacja, wynik, następny krok). Następnie szukamy przyjętej decyzji i jawnego zastąpienia wcześniejszej reguły w jej zakresie. Nie wybieramy automatycznie „najnowszego pliku”. Gdy nie ma rozstrzygnięcia, zapisujemy konflikt; nie dopasowujemy wymagania do kodu. To sposób analizy, nie nowa hierarchia dokumentów narzucona projektowi.

Przykład rozstrzygnięty: DEC-VCS-134 wprost zastępuje próg DEC-VCS-013, a REQ-VCS-100 podaje 85 MiB; historyczne pomiary przy 60 MiB pozostają poprawnymi zapisami dawnego zdarzenia. Przykład niespójnej instrukcji: prompt oddaje pierwszeństwo WSPOLPRACA, ale jednocześnie przytacza późniejsze polecenie użytkownika o commitach. Obowiązuje jawne polecenie użytkownika; sprzeczny tekst pozostaje ustaleniem do naprawy (PIL-U-001).

#### Próba odnalezienia reguły, statusu i następnego kroku

To próba nawigacji w dokumentach, bez oceny kodu i asercji z etapu 4. Każdy wiersz sprawdzono w zapisanych źródłach, bez odtwarzania całej rozmowy.

| Przypadek | Reguła i miejsce odczytu | Status możliwy do ustalenia z dokumentów | Następny krok i luka |
|---|---|---|---|
| 85 MiB | SPEC: DEC-VCS-134, REQ-VCS-100 i REQ-VCS-105; DESIGN: DES-VCS-034. | Próg przyjęty; 100 MiB dla 3000 plików odrębne. SPEC kończy relację P21 wynikiem starego testu przy 60 MiB; nie podaje tam późniejszego wyniku dla 85 MiB. | W etapie 4 powiązać późniejszy wynik z badaną wersją. Dodatkowy trop: commit `c9775b2`, lokalny log `/private/tmp/vcs-85-tests.log`; nie uznano go jeszcze za dowód dla całej bazy. |
| Notatki | SPEC: DEC-VCS-133, REQ-VCS-046, VER-VCS-025; DESIGN: DES-VCS-080; UI-REFERENCE: P21. | Opisane jako wdrożone; makieta zaakceptowana; wygląd aplikacji nadal czeka na zrzut — MANUAL-UI krok 30 oraz SLOWNIK, wstęp. `@confirmed` w AT-VCS-070 nie zamyka tego oczekiwania. | Użytkownik: próba ręczna 30; agent: przygotowanie i ocena wyników. Zachowanie i pokrycie testami do etapu 4. |
| Kompaktowe liczniki | SPEC: Punkt wznowienia 12–14 (cytat i doprecyzowanie), REQ-VCS-040; SLOWNIK: „Liczby zmian”; UI-REFERENCE: P21. | Opis wdrożenia istnieje; MANUAL-UI krok 29 nadal czeka na ocenę i opisuje głównie pliki commita, nie pełny zakres E/B/F. Nie ma jednego wpisu zamykającego całą zmianę. | Agent: odtworzyć w etapie 4 zakres potwierdzeń i weryfikacji. Nie żądać ponownej akceptacji, zanim zostaną sprawdzone istniejące dowody. PIL-U-004. |

#### Wynik względem spodziewanych korzyści

| Korzyść | Co faktycznie ustalono w etapie 2 | Jak sprawdzimy dalszy efekt |
|---|---|---|
| Mniej błędnej interpretacji | Słownik rozróżnia B/E/F; korekta intencji liczników jest zapisana w SPEC pkt 13–14. To wskazuje użyteczny mechanizm, nie dowodzi jeszcze zgodności implementacji. | Etap 4: porównać zakres decyzji z kodem i asercjami. |
| Łatwiejszy powrót | Regułę odnaleziono dla 3/3 prób. Jednoznaczny aktualny następny krok produktu znaleziono dla notatek (1/3); dla pozostałych dwóch trzeba najpierw uzupełnić relację status–dowód. To wynik tej małej próby, nie metryka całego repo. | Po ewentualnej naprawie powtórzyć te same trzy pytania bez lektury całej historii. |
| Wiarygodniejsze „gotowe” | Dokumenty prawidłowo oddzielają akceptację potrzeby od wyniku testu oraz przyjętą makietę od oceny działającego P21. Nie ma podstaw do uznania trzech zmian za w pełni zweryfikowane na bazie samej mapy. | Etap 4: policzyć deklaracje poparte dowodem właściwej wersji; etap 2 tego nie zastępuje. |
| Niższy koszt dokumentowania | Kandydaci do usunięcia duplikacji: próg/liczba testów/zakresy ID w prompcie; status P21 w słowniku, SPEC i MANUAL-UI; dawne następne kroki w Punkcie wznowienia. Mapa odsyła do źródeł zamiast przepisywać wymagania. | Po zmianie procesu sprawdzić liczbę miejsc koniecznych do aktualizacji dla jednej zmiany oraz czas powrotu do zadania. Nie deklarujemy oszczędności bez porównania. |
| Skuteczniejsze naprawy | Cztery ustalenia mają dowód, opiekuna i warunek zamknięcia w rejestrze. Nie wykonano napraw. | Po ich realizacji zweryfikować warunki i obserwować nawroty; obecnie brak danych o skuteczności. |

Koszt etapu: około 15 minut aktywnej analizy i zapisu (szacunek, nie pomiar stopera); tokenów nie zmierzono. Kilka zbyt szerokich odczytów dało ucięte wyniki i wymagało odczytów celowanych — rzeczywisty koszt metody, nie oszczędność. Nie uruchamiano testów produktu ani całej suity. Dla dalszych etapów stosować odczyt wskazanych sekcji/ID i pełne logi weryfikacji, bez masowego wypisywania makiet HTML.

#### Ograniczenia i przekazanie

Mapa obejmuje wskazane dokumenty oraz wejścia potrzebne do trzech prób; nie jest kompletnym audytem każdego zdania wszystkich makiet i propozycji. W `tests/traceability.py` potwierdzono, że dokumenty referencyjne to MANUAL-UI i UI-REFERENCE; WSPOLPRACA, PROMPT i SLOWNIK nie są wejściami tego checkera. Ocena jego pełnego zakresu i wykonanie na bazie pozostają etapem 3. Nie uznano poprawnych ID za dowód spójności znaczenia.

Trzy wskazane logi w `/private/tmp` istnieją: `vcs-85-tests.log`, `vcs-notes-full.log`, `vcs-count-index-tests.log`; sprawdzono istnienie i końcowy rezultat, nie pełną adekwatność dowodu. Brak trwałego archiwum jest ryzykiem przyszłej dostępności, nie stwierdzeniem, że logi zaginęły. Powiązanie ich wersji i warunków pozostaje etapem 4.

Cztery otwarte ustalenia PIL-U-001–004 zapisano bez zmiany reguł wejściowych. Priorytety są wstępne; etap 5 może je zmienić po sprawdzeniu ścieżek dowodowych. Etap 2 zakończony; następny jest etap 3. DoD całego pilotażu nadal niespełnione.


### Etap 3 — kontrola struktury (wykonany)

Wykonano 2026-10-28 od 22:49:45 CET na izolowanym `git archive` bazy `c19208dd4ce797ec5183c3127e832c5282a30aba`. Zmiany użytkownika oraz późniejsze dokumenty pilotażu nie weszły do badanego korpusu. Python 3.12.11, pytest 9.0.2, macOS 26.2 arm64; środowisko i dokładne polecenia są w [result.json](experiments/sdlc-stage3-20261028/result.json). Nie uruchamiano aplikacji, testów GUI ani pełnej suity produktu.

#### Dowód i odtworzenie

- [Pełny log przebiegu bazowego](experiments/sdlc-stage3-20261028/pytest-baseline.log): **22 passed in 0.53s**, kod wyjścia 0. Osiem testów sprawdza rzeczywisty korpus, czternaście zachowanie checkera na danych syntetycznych. To nie jest wykonanie 22 scenariuszy produktu.
- [Różnica TRACE](experiments/sdlc-stage3-20261028/TRACE.diff): plik ma **0 bajtów**. SHA-256 przed i po: `0fa788b69cb793c08aac7893df4f927d54592e8d748a0173022aa4bc728495be`. Zapisany TRACE jest aktualny względem generatora tej bazy.
- Po przebiegu bazowym żadna istniejąca zawartość pliku pakietu z archiwum nie uległa zmianie (porównano SHA-256). Utworzone przez interpreter cache nie są artefaktami wejściowymi.
- [Skrypt odtwarzający](experiments/sdlc-stage3-20261028/run.py) pobiera stały commit, zapisuje logi, różnicę i wynik JSON, a następnie wykonuje próbę kontrolną wyłącznie w katalogu tymczasowym. Dowody zapisano w repo, nie tylko w `/private/tmp`.

Odtworzenie z katalogu pakietu, z zapisem nowego przebiegu poza dowodami pierwotnymi:

```sh
../../.venv/bin/python docs/experiments/sdlc-stage3-20261028/run.py --repo ../.. --output /private/tmp/vcs-stage3-recheck
```

Polecenie właściwego testu, wykonywane w odizolowanym korzeniu repo: `.venv` z oryginalnego środowiska uruchamia `python -m pytest -p no:cacheprovider -vv packages/vcs_lite/tests/test_traceability.py`. Skrypt wymaga dostępności badanego commita w lokalnym Git i środowiska z pytest; nie pobiera zależności ani nie zmienia ustawień użytkownika.

#### Faktyczny zakres wejść

| Wejście | Co odczytuje checker na bazie |
|---|---|
| SPEC i DESIGN | Definicje z rozpoznanych wierszy tabel i nagłówków oraz odwołania pasujące do regexów ID. Nie analizuje logicznego znaczenia tekstu. |
| ACCEPTANCE.feature | Scenariusze z tagami bezpośrednio nad nagłówkiem; pierwszy tag AT, tagi REQ/DEC/UC/VER i `@confirmed`. Nie wykonuje kroków Given/When/Then. |
| MANUAL-UI, UI-REFERENCE | Odwołania do ID i niedozwolone skróty. Brak pliku referencyjnego jest pomijany przez `path.exists()`, nie zgłaszany jako błąd. |
| `tests/**/test_*.py` | Nazwy funkcji `test_*` z AST, także zagnieżdżonych; to nie wynik kolekcji/wykonania całej suity pytest. |
| `src/vcs_lite/**/*.py` | Pierwsza rozpoznana linia `Trace:` w docstringu każdego modułu. Nie śledzi zależności poszczególnych funkcji ani przepływu wywołań. |
| Poza korpusem dokumentów | WSPOLPRACA, PROMPT-STARTOWY, SLOWNIK, RETROSPEKTYWA, teksty PROPOZYCJA, makiety HTML, dokumenty pilotażu, logi wykonania i rozmowa. |

Rozmiar rozpoznanego korpusu: **473 unikalne ID**, w tym 60 REQ (59 bez statusu ZASTĄPIONE), 134 DEC, 80 DES, 70 AT, 25 VER. Pozostałe: 4 NEED, 18 OBS, 71 Q, 9 UC, 1 S, 1 T. **70 scenariuszy ma `@confirmed`; 631 nazw funkcji testowych w 54 plikach; 42 moduły src**. Liczba funkcji AST nie jest liczbą wykonanych testów (m.in. parametryzacja pytest może ją zmieniać).

#### Reguły i wynik

| Reguła | Faktyczne kryterium | Wynik na bazie |
|---|---|---|
| REQ-VCS-200 | Brak wielokrotnych definicji rozpoznanego ID. | 0 błędów |
| REQ-VCS-201 | Rozpoznane odwołania istnieją; brak skrótów wykrywanych przez SHORTHAND_RE. | 0 błędów |
| REQ-VCS-202 | REQ bez statusu ZASTĄPIONE ma powiązanie AT lub VER i DES albo jawny wyjątek „bez DES:”. | 0 błędów |
| REQ-VCS-203 | Każdy rozpoznany AT ma tag REQ; VER/DES wskazuje REQ lub DEC. | 0 błędów |
| REQ-VCS-204 | Nazwa odczytanej funkcji testowej zaczyna się od rozpoznanego, istniejącego ID. | 0 błędów |
| REQ-VCS-205 | Każdy confirmed AT ma nazwę funkcji testowej z tym AT; `TDD_STARTED=True`, więc brak oblewa. | 0 błędów |
| REQ-VCS-206 | Każdy moduł src ma `Trace:` z co najmniej jednym istniejącym ID. | 0 błędów |
| REQ-VCS-207 | Wygenerowanie macierzy i sprawdzenie obecności wiersza REQ-VCS-001. | Test przeszedł; niezależne porównanie potwierdziło brak różnicy TRACE. |

Dodatkowa inspekcja mapy: wszystkie 59 REQ bez statusu ZASTĄPIONE mają co najmniej jedno wyliczone powiązanie do nazwy testu. Osiem z nich (REQ-VCS-200–207) nie ma powiązania do modułu `src`; dotyczą kontroli procesu w `tests/`, więc nie klasyfikujemy tych pustych pól jako usterki. Relacja do modułu nie jest wymagana przez check_202. Powiązania mogą być pośrednie przez DES/AT i nie dowodzą pokrycia zachowania.

#### Próba kontrolna i ograniczenia wyniku

Po zakończeniu pomiaru bazowego, w tej samej kopii tymczasowej zastąpiono TRACE pojedynczym celowo nieaktualnym nagłówkiem. Uruchomiono wyłącznie test REQ-VCS-207: **1 passed, 21 deselected**, a plik został odtworzony do poprzedniej wygenerowanej zawartości. [Pełny log próby](experiments/sdlc-stage3-20261028/pytest-stale-trace-probe.log). Nie zmieniano checkera, wymagań ani TRACE w repo roboczym.

To potwierdza, że zielony wynik generatora nie dowodzi aktualności TRACE przed uruchomieniem. Na rzeczywistej bazie TRACE był aktualny, więc nie znaleziono tu zaległej macierzy. Wymaganie REQ-VCS-207 nakazuje generowanie, nie wymaga błędu przy nieaktualnym pliku; zachowanie jest ograniczeniem kontroli, a ewentualny tryb bez zapisu to propozycja usprawnienia, nie zgłoszenie niespełnienia tego wymagania (PIL-U-005).

Pozostałe granice wynikają z odczytu implementacji: parser rozpoznaje określony format, nie dowolny tekst; nie sprawdza treści asercji, skip/xfail, rezultatów wykonania testów produktu, kompletności warunków wymagania, zgodności cytatu z intencją, aktualności statusu ani uprawnień do akceptacji. Wycofanie/zastąpienie rozpoznaje po szczególnych słowach w komórce opisu. Brak komunikatu checkera nie jest uniwersalnym dowodem braku błędnych odwołań we wszystkich plikach.

#### Korzyści, koszt i dalszy krok

- **Wiarygodniejsze „gotowe”:** oddzielono poprawność struktury, aktualność pliku generowanego i poprawność zachowania. Pierwsze dwie potwierdzono dla konkretnej bazy; trzecia pozostaje do etapu 4.
- **Łatwiejszy powrót i niższy koszt:** zachowano powtarzalne polecenie, pełne logi i dane w repo. Następny recenzent nie musi odtwarzać wyniku z rozmowy lub plików tymczasowych. Cały przebieg skryptu (archiwum, kontrola, inwentaryzacja i próba) trwał 2,119 s; nie jest to czas całego przeglądu ani dowód oszczędności względem dawnego procesu.
- **Mniej błędnej interpretacji:** cztery ustalenia etapu 2 nie znikają po zielonych testach; są poza zakresem checkera albo dotyczą znaczenia treści. Nie wymagamy rozszerzania regexów na każdy dokument zamiast przeglądu semantycznego.
- **Skuteczniejsze naprawy:** dodano jedno ustalenie PIL-U-005 z mierzalnym warunkiem, bez automatycznej zmiany generatora. Brak danych o skuteczności napraw, bo nie były wykonywane.

Nakład aktywnej analizy i dokumentowania: około 5 minut (szacunek); tokenów nie zmierzono. Etap 3 zakończony. Następny: etap 4 — trzy ścieżki dowodowe. Kontrola dokumentów nowego przyrostu przed commitem jest oddzielna od powyższego przebiegu bazowego.


### Etap 4 — trzy ścieżki dowodowe (wykonany)

Wykonanie 2026-10-29. Zlecenie użytkownika: „czy masz zpiasany ten plan i kryteria oddbiodu ora rejestr zmian ktory utrzymujesz? Jak tak to kontynuuj rzetelnie”. Kontynuowano zapowiedziany etap 4, bez wdrażania napraw. Podstawa nadal `c19208dd4ce797ec5183c3127e832c5282a30aba`.

**Wynik:** potrzeby można prześledzić do kodu; nie wszystkie istotne warunki mają trwałe testy regresji i akceptację użytkownika. 64 istniejące testy przeszły. Dodatkowe 29 prób dało 28 wyników zgodnych i jedną odtworzoną regresję: dla konfliktu renderer kompaktowych liczb wypisuje „—” zamiast „konflikt”. Zielona kontrola ID z etapu 3 nie wykryła tego problemu.

#### Dowody, wersja i zakres

Zbudowano osobne archiwum Git bazy w `/private/tmp/vcs-stage4-base-20261029`. Porównano surową zawartość wszystkich plików Python w src i tests z bazą Git przed zamknięciem etapu; po testach i próbach pozostały niezmienione. Ustawienia, repo i notatki prób były tymczasowe; schowek zastąpiony atrapą. Bez screenshotów i zmian produktu.

| Dowód w repo | Co potwierdza |
|---|---|
| [existing-tests.log](experiments/sdlc-stage4-20261029/existing-tests.log) | Pełny przebieg 64 istniejących testów, **64 passed in 15.00s**, bez skip/xfail. Moduły: footprint, repo_notes, gitlog, change_details, recent_changes, file_list_viewport, history_session. |
| [existing-tests.json](experiments/sdlc-stage4-20261029/existing-tests.json) | Wynik każdego testu, udany pomiar pamięci, środowisko, argumenty, SHA-256 plików źródłowych i testowych. Python 3.12.11, pytest 9.0.2, macOS 26.2 arm64. |
| [probes.json](experiments/sdlc-stage4-20261029/probes.json) | Oczekiwany i rzeczywisty wynik 29 dodatkowych prób diagnostycznych. Nie są to testy obecne w bazie ani potwierdzenia użytkownika. |
| [manifest.json](experiments/sdlc-stage4-20261029/manifest.json) | Sumy kontrolne dowodów/skryptów, zgodność kodu z bazą oraz brak zmian w src/tests po próbach. |
| [run_tests.py](experiments/sdlc-stage4-20261029/run_tests.py), [probes.py](experiments/sdlc-stage4-20261029/probes.py) | Skrypty pozwalające odtworzyć wykonanie na rozpakowanej bazie. Drugi zapisuje także wyniki negatywne; jego kod wyjścia sam nie jest werdyktem zgodności — sprawdzić `failed` w JSON. |

Odtworzenie: rozpakować `git archive c19208dd4ce797ec5183c3127e832c5282a30aba` do nowego pustego katalogu, następnie uruchomić oba skrypty Pythonem `.venv` z argumentami `--base <katalog archiwum> --output <nowy katalog wyników>`. Nie nadpisywać pierwotnych dowodów. Pomiar pokazuje tymczasowe okno topmost i używa systemowego `footprint`; próby notatek pokazują okno z danymi tymczasowymi. Skrypty nie instalują zależności.

Starszy `/private/tmp/vcs-85-tests.log` zawiera jedynie wynik 25 testów, bez surowych próbek i identyfikacji wersji wewnątrz logu. `c9775b2` różni się od bazy jedynie dwoma plikami planu pilotażu, co potwierdza zgodność kodu, lecz nie uzupełnia metadanych dawnego uruchomienia. Zamiast uznawać stary log za pełny dowód wykonano jeden nowy pomiar; zachowano także jego wartości sukcesu, których zwykły test nie wypisuje.

#### A. Limit pamięci 85 MiB

**Łańcuch:** cytat „zwiekszymy limit do 85MiB” → DEC-VCS-134 (zastępuje wyłącznie próg, zachowuje zakres DEC-VCS-042) → REQ-VCS-100 → DES-VCS-034 i VER-VCS-006 → `tests/measure_footprint.py::measure/run_child/footprint_mib` → AT-VCS-016 i `test_at_vcs_016_vcs_lite_stays_within_85_mib_with_an_open_compare` → nowy wynik w JSON. Commity: specyfikacja `3962daa`, test/TRACE `c9775b2`; weryfikacja bazowej wersji nie zmienia historycznych pomiarów przy 60 MiB.

Test wymaga pięciu próbek, widocznego topmost, co najmniej 4000 commitów historii, 500 wczytanych i maksimum ≤85. Wspólny pomiar buduje trzy repo, 300 zmian, otwiera atrapę zewnętrznego diffu i mierzy tylko PID aplikacji przez pięć sekund. Przelicza bajty przez `2**20`, więc porównuje MiB. W module osobne asercje kontrolują medianę odświeżenia i brak Git w bezczynności. Zakres 3000 plików i 100 MiB pozostaje oddzielny; nie powtarzano jego pomiaru, bo ten przyrost nie zmienił jego progu ani kodu.

**Nowy pomiar:** 55,4 / 55,5 / 55,5 / 55,4 / 55,4 MiB, maksimum **55,5 MiB**; mediana odświeżania **0,183 s**; Git w bezczynności **0**, przed gotowością **80**. Historia 4000/500, 300 zmian, topmost/viewable = true. Pole `commit` wewnątrz pomiaru jest puste, ponieważ archiwum nie ma `.git`; identyfikację zapewniają baza i zweryfikowane hashe w otaczającym raporcie. Pole `tk` skrypt mierzy przez `info patchlevel` (8.6.14), czyli wersję Tcl, nie niezależny odczyt pakietu Tk — ograniczenie metadanych, nie wynik testu zgodności Tk.

| Kryterium | Ocena | Uzasadnienie |
|---|---|---|
| 1. Intencja i aktualność | spełnione | Jawna zgoda, zmieniony próg i zachowany odrębny limit 100 MiB. |
| 2. Spójność | spełnione | REQ, DES, scenariusz i asercja stosują 85 MiB w tym samym scenariuszu; historyczny pomiar P21 nie jest nowym kryterium. |
| 3. Powiązania | spełnione | Wskazany łańcuch umożliwia dojście w obie strony; stare DEC-VCS-013 nadal występuje jako odnośnik, ale REQ i DEC-VCS-134 jawnie rozstrzygają zmianę. |
| 4. Weryfikacja | spełnione | Oceniono asercje i przygotowanie środowiska; dotyczą zdefiniowanego pomiaru, nie wszystkich możliwych warunków użycia aplikacji. |
| 5. Dowód wykonania | spełnione | Zachowany sukces wraz z próbkami, środowiskiem i identyfikacją bazy. Jedno wykonanie nie dowodzi trwałego usunięcia wcześniejszej zmienności. |
| 6. Obsługa zmiany | niespełnione | Prompt nadal podaje 60 MB, a status bieżącego wyniku był rozproszony: PIL-U-002 i PIL-U-003. Obecny raport uzupełnia dowód, nie naprawia dokumentów wejściowych. |

Status: **próg zaakceptowany, zmiana testu wdrożona, pomiar bazowej wersji zweryfikowany**. Nie deklarujemy, że zmiana progu naprawiła pamięć ani że próba potwierdza wszystkie scenariusze wydajności.

#### B. Notatki repozytorium

**Łańcuch:** potrzeba przechowywania promptów/notatek per repo + korekty układu → akceptacja P21 „switnie, wykonaj” → DEC-VCS-133 → REQ-VCS-046 → DES-VCS-080 → `NoteStore`, `NotesPanel`, integracja `ui/main.py::build` i `MainWindow` → AT-VCS-070, VER-VCS-025, `tests/ui/test_repo_notes.py`, MANUAL-UI krok 30. Commity: `296a052` przed implementacją `c54929c`.

Odczyt kodu potwierdza tożsamość notatki przez pełną rozwiązaną ścieżkę repo, atomowy zapis przez tempfile + fsync + replace, katalog notes obok użytego settings.json, zapis po 700 ms, FocusOut, zmianie repo i zamykaniu. Callback zamknięcia aplikacji wywołuje flush, a po porażce zachowuje okno, odsłania edytor i kieruje do niego fokus. NotesPanel przechowuje pozycję kursora/przewinięcia i przyjmuje funkcję kopiowania; MainWindow wiąże notatnik z repo, nie z wybranym commitem.

**Co faktycznie sprawdzały cztery istniejące testy:** przełączenie repo i powrót w tym samym panelu, brak pliku przed edycją, zachowanie tekstu po błędzie flush, rozróżnienie ścieżek o tej samej nazwie repo, UTF-8, atomowość przy błędzie replace, ochrona pliku o błędnym kodowaniu. Test `…save_switch_and_reopen` nie tworzy nowego panelu/procesu. Żaden z tych czterech testów nie sprawdza callbacku zamknięcia aplikacji ani uruchomienia timera/FocusOut. To luka automatycznej regresji, nie dowód, że funkcja nie działa.

**Nowe próby diagnostyczne:** timer, syntetyczne FocusOut w widocznym oknie, kopiowanie fragmentu/całości przez atrapę, kursor/przewinięcie przy zmianie repo, odczyt przez nowy NotesPanel z nowym NoteStore, sąsiedztwo katalogu settings, wyrównanie współrzędnej X notatnika i szczegółów commita, zablokowane zamknięcie po OSError z widocznym komunikatem i zachowaniem tekstu, udany zapis przy ponowionej próbie zamknięcia — zgodne. To nie jest ponowny start całej aplikacji ani ocena wyglądu przez użytkownika; nie wnioskujemy z samej równości X o pełnej zgodności UI.

| Kryterium | Ocena | Uzasadnienie |
|---|---|---|
| 1. Intencja i aktualność | spełnione | Decyzja i REQ obejmują notatnik domyślny, zapis obok settings i zaakceptowane korekty układu. |
| 2. Spójność | spełnione | Odczyt kodu i wykonane próby nie wykazały sprzeczności z opisanym mechanizmem. Pełny wygląd pozostaje poza tym potwierdzeniem. |
| 3. Powiązania | spełnione | Łańcuch REQ/DES/AT/moduł istnieje; integrację main/main_window i ręczną próbę 30 wskazano dodatkowo, bo sam TRACE dla REQ-VCS-046 pokazuje notes.py. |
| 4. Weryfikacja | brak dowodu | Nowe próby rozszerzyły sprawdzenie, lecz brak trwałych regresji części ścieżek oraz próby pełnego restartu aplikacji. PIL-U-006. |
| 5. Dowód wykonania | brak dowodu | Są wyniki automatyczne i diagnostyczne dla wymienionych warunków; brak końcowej akceptacji wyglądu P21 i pełnej próby ręcznej 30. |
| 6. Obsługa zmiany | niespełnione | Plan ręczny uczciwie pozostaje otwarty, ale suite nie chroni całości krytycznych ścieżek deklarowanych przez AT-VCS-070; zapisano PIL-U-006, nie zamykamy go udanym smoke testem. |

Status: **wdrożone; mechanizmy zweryfikowane w wymienionym zakresie; makieta zaakceptowana; wykonanie całej próby 30 i wygląd aplikacji niepotwierdzone**. Z ogólnych pochwał wcześniejszych funkcji nie wyprowadzono akceptacji P21.

#### C. Kompaktowe kolorowe liczniki

**Łańcuch:** początkowa prośba o +/− w plikach commita → DEC-VCS-132, REQ-VCS-040, DES-VCS-079 → doprecyzowanie lewej listy i cytat „w obu oknach chce wersji kompaktowej z lewego okna ale z kolorami” w SPEC, Punkt wznowienia 13–14 → SLOWNIK „Liczby zmian” i późniejszy P21 rozszerzający wygląd na B → `GitLog.details/commit_totals`, `HistorySession._page_with_totals`, `draw_compact_counts`, FileList/CommitList/CommitView. Statystyka pliku i suma commita są różnymi danymi, choć używają wspólnego renderera.

Backend plików ma asercje root/merge względem pierwszego rodzica/rename/binarne/nietypowe ścieżki/błąd. Test dużego CommitView sprawdza tekst liczb, sumę, przewijanie i liczbę obiektów. Testy FileList sprawdzają tekst, położenie i duże wartości. Odczyt testów i wyszukanie wywołań nie wykazały dedykowanych asercji wyniku `GitLog.commit_totals`, kompaktowego odstępu ani kolorów. Istniejące testy historii mogą przejść także z czytnikiem bez `commit_totals`, bo kod używa opcjonalnego `getattr`. Commity dodające sumy do E (`769b966`) i kompaktowe kolory (`cbeb5ff`) nie zmieniały plików testów — brak nowych regresji jest zgodny z historią, nie tylko domysłem z nazw testów.

Nowe próby sum porównały E z sumą szczegółów F dla root, zwykłej zmiany, obu gałęzi, merge, pustego commita, pliku binarnego, rename oraz nazwy z separatorem rekordu ASCII RS — zgodne. Jest to porównanie dwóch ścieżek opartych o Git, nie niezależny dowód poprawności wszystkich przypadków parsera. Nie przetestowano tu SHA-256 Git ani wszystkich ustawień Git. Renderer poprawnie pokazał +334/−34, kolory, szare zera, odstęp 5 i etykiety binarne/brak danych.

**Odtworzona regresja:** `draw_compact_counts(LineStats(kind='conflict'))` daje „—”. REQ-VCS-043 oraz AT-VCS-065 wymagają „konflikt”; FileList używa właśnie tego renderera w kolumnie linii. Stary `draw_line_counts` miał osobną etykietę konfliktu, a nowy rozróżnia jedynie binary i pozostałe rodzaje nietekstowe. Test core sprawdza rodzaj danych, ale nie tekst na Canvas. Próba potwierdza wadę etykiety, nie błąd operacji scalania ani utratę danych. PIL-U-007.

| Kryterium | Ocena | Uzasadnienie |
|---|---|---|
| 1. Intencja i aktualność | spełnione | Cytaty rozróżniają E i F, P21/SLOWNIK także B; intencję można odtworzyć mimo rozproszenia. |
| 2. Spójność | niespełnione | Renderer konfliktu nie realizuje zachowanego warunku REQ-VCS-043 i AT-VCS-065. |
| 3. Powiązania | niespełnione | Dalsze rozszerzenia zakresu opisano prozą; powiązania strukturalne nie zapewniają znalezienia testu chroniącego sumy E i kolory. PIL-U-004. |
| 4. Weryfikacja | niespełnione | 64 testy przeszły mimo odtworzonej regresji; brak dedykowanych regresji sum E/kolorów, dodatkowe próby są dopiero dowodem audytu. |
| 5. Dowód wykonania | brak dowodu | Nowy log i próby dowodzą określonych zachowań i wady. MANUAL-UI 29 nie zamyka pełnej oceny wszystkich trzech list; brak podstaw do zbiorczej akceptacji wyglądu. |
| 6. Obsługa zmiany | niespełnione | Rozszerzenie renderera na B zmieniło również etykietę konfliktu, której regresja nie ochroniła. PIL-U-004 uzupełnione, PIL-U-007 dodane. |

Status: **wdrożone; podstawowe dane i prezentacja liczb sprawdzone; jedna potwierdzona wada prezentacji; brak pełnego odbioru wyglądu i trwałych regresji rozszerzonego zakresu**. Szare podsumowanie nagłówka F nie zostało samoistnie uznane za wadę — prośba dotyczyła list, a zakres nagłówka wymagałby osobnej interpretacji.

#### Bilans korzyści i kosztu

| Korzyść | Dowód z etapu 4 | Granica wniosku |
|---|---|---|
| Mniej błędnej interpretacji | Rozdzielono sumy E i liczby plików B/F oraz zgodę na makietę od odbioru programu. | Nie udowodniono jeszcze spadku liczby przyszłych pomyłek. |
| Łatwiejszy powrót | Każda z trzech prób ma teraz łańcuch i aktualny krok: pamięć — aktualizacja starych instrukcji; notatki — regresje/restart i próba 30; liczniki — naprawa etykiety i uzupełnienie regresji/statusu. | To wynik nawigacji w raporcie, nie naprawa wszystkich dokumentów wejściowych. |
| Wiarygodniejsze „gotowe” | Próg 85 MiB ma kompletny nowy dowód pomiaru; dwóch funkcji UI nie oznaczono jako w pełni odebrane. 1 z 29 nowych prób wykryła wadę niewidoczną dla zielonej struktury i dobranych istniejących testów. | Liczba usterek nie jest celem przeglądu ani oszacowaniem ich liczby w aplikacji. |
| Niższy koszt dokumentowania | Użyto 7 istniejących modułów zamiast pełnej suity; dowody zapisano raz, a raport/rejestr odsyłają do nich. | Nie ma porównania kosztu z procesem bez przeglądu. Część szerokich odczytów nadal wymagała zawężenia; nie deklarujemy oszczędności tokenów. |
| Skuteczniejsze naprawy | PIL-U-006 i PIL-U-007 mają warunki zamknięcia; PIL-U-004 otrzymuje dowody pokrycia testami. | Nie wykonano napraw, więc skuteczność i nawroty pozostają niezmierzone. |

Nakład etapu 4: około 15 minut aktywnej analizy, prób i zapisu (szacunek, bez pomiaru tokenów). Istniejące testy: 15,00 s. Nie powtarzano pomiaru w celu uzyskania lepszego wyniku i nie badano dalej historycznej niestabilności, zgodnie z DEC-VCS-077. Użyto próby mierzącej aktualny stan, nie twierdzenia o poprawie pamięci.

**Przekazanie:** etap 4 zakończony; wszystkie trzy zmiany oceniono według sześciu kryteriów. Etapy 5–6 pozostają otwarte. W kolejnym kroku należy ocenić łącznie PIL-U-001–007 i wybrać kolejność działań oraz najwyżej trzy rekomendacje; nie wykonywać napraw tylko po to, aby wynik przeglądu wyglądał na pozytywny.


### Etap 5 — ocena i plan działań (wykonany)

Wykonano 2026-10-29 na podstawie ustaleń etapów 2–4. Ponownie sprawdzono sumy dowodów etapu 4: bez zmian. Nie uruchamiano ponownie testów produktu ani pomiarów; nowe wykonanie nie zmieniłoby podstawy priorytetyzacji. Wynik szczegółowy zapisano raz, w [rejestrze działań](PRZEGLAD-SDLC-REJESTR.md#etap-5--plan-działań-po-ocenie-dowodów).

**Kolejność proponowanej realizacji:** (1) etykieta konfliktu i minimalna regresja, (2) jednoznaczny punkt wejścia/status zamiast duplikatów, (3) regresje cyklu notatki, (4) zakres i regresje sum/kolorów, (5) porównanie TRACE w istniejącym sprawdzeniu indeksu. Każde z siedmiu ustaleń ma działanie, opiekuna, wyzwalacz i warunek zamknięcia. To plan realizacji, nie pięć nowych obowiązków przy każdej zmianie.

Pierwszeństwo ma odtworzona wada o małym koszcie, następnie usprawnienie wznowienia pracy. Luka zapisu notatek pozostaje ważna, lecz udane próby nie uzasadniają twierdzenia o utracie danych. PIL-U-005 obniżono ze średniego wstępnego do niskiego: macierz bazowa była aktualna, a sprawdzenie porównawcze jest tanie. Pozostałe priorytety średnie; powody i niepewność jawne w rejestrze. Nie przypisywano sztucznych prawdopodobieństw.

**Związek z celem:** krótsza droga do reguły/statusu/odpowiedzialności; rzeczywiste regresje zachowania zamiast samych ID; wynik z wersją zamiast ogólnego „gotowe”; usunięcie kopii zmiennych danych zamiast ich ciągłego przepisywania. Cel odbioru nawigacji: 3/3 próby bez rozmowy/kroniki; czas i liczba odczytów mierzone dopiero przy realizacji. Nie deklarujemy już osiągniętej oszczędności czasu ani tokenów.

Szacowany koszt przyszłych działań: 120–200 minut aktywnej pracy w pięciu małych przyrostach; pierwsze dwa 40–65 minut. To koszt napraw/usprawnień, **nie** koszt zakończonego etapu 5 ani zwiększenie budżetu przeglądu. Nakład etapu 5: około 8 minut (szacunek). W etapie 6 ocenić całkowity koszt przeglądu i sens powtarzania metody; nie dodawać pełnego audytu do każdej drobnej zmiany.

Sprawdzono także koszt samej dokumentacji: przed etapem 5 plan miał 402 wiersze, rejestr 127. Użytkownik zgłosił utratę orientacji mimo istnienia planu. To jakościowy sygnał, że samo utrzymywanie dokumentów nie wystarcza. Dodano krótki bieżący stan na początku planu; szczegółów działań nie powielono w obu plikach. Liczba wierszy nie mierzy użyteczności — odbiór ma polegać na odnalezieniu odpowiedzi, nie na osiągnięciu arbitralnej długości.

**Odbiór etapu 5:** wszystkie 7 ustaleń sklasyfikowano; odróżniono potwierdzoną wadę, konflikt dokumentacji, lukę dowodu i usprawnienie; wskazano 5 przyrostów z kosztami i odbiorem; żaden wpis nie został zamknięty bez naprawy/dowodu ani uznany za zatwierdzony do wdrożenia. Wszystkie nadal otwarte. Następny etap 6 wybierze najwyżej trzy końcowe rekomendacje i oceni zakończenie pilotażu.

### Etap 6 — podsumowanie i zakończenie pilotażu

**Werdykt agenta, 2026-10-29:** zakończyć ten pilotaż na ustalonej próbie trzech zmian. Metoda jest użyteczna do kontroli znaczenia wymagań i wiarygodności dowodów, ale jej pełna sześciostopniowa forma jest zbyt ciężka jako obowiązek przy każdym drobnym przyroście. Następny krok to realizacja działań z rejestru, nie rozszerzanie audytu na całe repo. To rekomendacja po przeglądzie, nie przypisana użytkownikowi zgoda na wdrożenie.

#### Co wiadomo po przeglądzie

- Baza `c19208dd4ce797ec5183c3127e832c5282a30aba` ma poprawną strukturę w zakresie checkera: 22 testy przeszły; zapisany TRACE odpowiada generatorowi. Oddzielna próba wykazała, że sam zielony test generatora może ukryć wcześniejszą nieaktualność pliku.
- 64 dobrane testy produktu przeszły. Pomiar 300 zmian: maks. 55,5 MiB przy limicie 85 MiB, odświeżenie 0,183 s, zero Git w bezczynności. To wynik jednego określonego scenariusza, nie gwarancja wszystkich warunków wydajności.
- Dodatkowe próby: 28/29 zgodnych; wykryto wadę etykiety konfliktu. Pozostałe wyniki wspierają działanie notatek i liczników w sprawdzonym zakresie, lecz nie zastępują brakujących trwałych regresji ani odbioru ręcznego.
- Siedem ustaleń ma właściciela, działania i warunki zamknięcia. **Żadnego nie zamknięto; napraw nie wdrożono.** Pozostały m.in. odbiór P21/krok 30 i pełny status oceny liczników/krok 29.

Dowody i polecenia są w etapach 3–4; sprawdzono ich integralność i zgodność liczb podsumowania. Nie powtarzano testów produktu tylko na potrzeby podsumowania.

#### Trzy końcowe rekomendacje

Poniższe grupy obejmują wszystkie siedem ustaleń i pięć przyrostów z etapu 5. Nie dodają nowych prac. Kolejność wykonawcza pozostaje w rejestrze: najpierw mała naprawa konfliktu, potem uporządkowanie wznowienia pracy, następnie regresje i kontrola TRACE.

| Rekomendacja | Zakres / koszt aktywnej pracy (szacunek) | Korzyść i sposób sprawdzenia | Ryzyko kosztu procesu |
|---|---|---|---|
| **1. Chronić zachowanie, nie tylko powiązania ID.** | PIL-U-007, PIL-U-006, PIL-U-004; przyrosty 1, 3, 4: **85–140 min**. Naprawa etykiety oraz minimalne regresje cyklu notatki, sum E i wspólnej prezentacji. | Stara wersja oblewa test konfliktu, poprawiona przechodzi; restart naprawdę czyta z dysku; sumy mają niezależne oczekiwane wartości. Odbiór UI zapisany osobno. | Bezrefleksyjne kopiowanie 29 prób do suity zwiększyłoby utrzymanie. Przenosić tylko niechronione warunki; nie powielać testu renderera dla każdej listy. |
| **2. Jedno krótkie miejsce wznowienia i odnośniki zamiast kopii statusu.** | PIL-U-001–003; przyrost 2: **25–40 min**. Uzgodniona reguła commitów, prompt bez kopii progów/liczb, bieżący stan oddzielony od kroniki. | Z promptu odnajdujemy regułę, stan, dowód i krok dla 3/3 prób bez rozmowy/kroniki. Mierzymy odczyty i czas; następna zmiana progu nie wymaga poprawiania jego kopii w prompcie. | Kolejny dashboard byłby nowym duplikatem. Wykorzystać istniejące SPEC i rejestr; stare wyniki zachować jako historię. |
| **3. Przy „gotowe” podawać wersję i dowód oraz sprawdzać artefakt generowany.** | PIL-U-005; przyrost 5: **10–20 min**. Porównanie TRACE w istniejącej kontroli indeksu i zachowanie odnośnika do wyniku. | Celowo nieaktualny TRACE jest jawnie wykrywany, aktualny nie daje różnicy; wynik dotyczy wersji przeznaczonej do commita. | Nie budować nowego frameworka/CI ani raportu przy każdym odczycie. Wystarczy istniejący generator, porównanie i jeden zapis dowodu. |

Łącznie **120–200 min przyszłej realizacji**, bez oczekiwania na ręczny odbiór. Nie jest to koszt już wykonanego pilotażu. Przy małym budżecie pierwszy odcinek z etapu 5 (konflikt + wznowienie) kosztuje szacunkowo 40–65 min; reszta pozostaje otwarta, bez deklaracji pełnego odbioru.

#### Ocena spodziewanych korzyści

| Cel | Wykazany rezultat | Czego jeszcze nie wykazano |
|---|---|---|
| Mniej pomyłek | Przegląd treści odtworzył konkretną niezgodność REQ/AT z renderowaniem, niewidoczną dla checkera ID i dobranych istniejących testów. | Spadku liczby przyszłych błędów po wdrożeniu regresji. |
| Łatwiejszy powrót | Jest mapa źródeł, opis trzech ścieżek i krótki bieżący stan; zidentyfikowano konflikt kroniki z listą zadań. | Poprawy mierzonej czasem lub odbiorem użytkownika. Użytkownik zgłosił zagubienie podczas samego pilotażu — dokumentacja nie gwarantuje czytelności. |
| Wiarygodniejsze „gotowe” | Rozróżniono przyjęte wymaganie/makietę, wykonany kod, zaliczony pomiar, brak regresji i brak odbioru. | Pełnego odbioru dwóch funkcji UI; wyniki jednej próby nie uzasadniają takiej deklaracji. |
| Niższy koszt dokumentowania | Wskazano konkretne duplikaty do usunięcia; dowody mają trwałe miejsce i skrypty odtworzenia. | Oszczędności czasu/tokenów. Przegląd sam powiększył dokumentację i wymagał ponownych odczytów. |
| Skuteczniejsze naprawy | Każde ustalenie ma mierzalny warunek zamknięcia i opiekuna. | Skuteczności napraw i braku nawrotów, ponieważ żadnej jeszcze nie wykonano. |

**Ocena opłacalności:** dodatnia wartość diagnostyczna, nieudowodniony zwrot ekonomiczny. Nie ma pomiaru porównawczego pracy bez przeglądu, więc nie wyliczamy ROI, oszczędności procentowej ani kosztu na wykryty błąd. Warto zachować sprawdzanie ścieżki potrzeba → asercja → wynik i krótką kontrolę bieżącego statusu. Nie warto powtarzać całej kroniki i inwentaryzacji przy każdej zmianie.

#### Nakład i ograniczenia metody

| Etap | Zapisany nakład aktywnej pracy |
|---|---:|
| 1 — podstawa | ok. 5 min |
| 2 — mapa źródeł | ok. 15 min |
| 3 — struktura | ok. 5 min |
| 4 — ścieżki dowodowe | ok. 15 min |
| 5 — działania | ok. 8 min |
| 6 — podsumowanie | ok. 5 min |
| **Razem** | **ok. 53 min, suma szacunków** |

To oszacowania pracy faktycznie wykonanej, nie pomiary stopera. Brak pełnej telemetrii czasu i tokenów; nie można rygorystycznie potwierdzić dotrzymania limitu 90 minut. Odtwarzalne pomiary są w logach (m.in. testy produktu 15,00 s, testy struktury 0,53 s), lecz nie obejmują rozumowania, odczytów ani dokumentowania. Kryterium DoD dotyczące nakładu zamykamy z tym jawnym ograniczeniem, bez przedstawiania szacunku jako dokładnego pomiaru. Kolejny pilotaż powinien mierzyć czas aktywny od początku, jeśli koszt ma rozstrzygać o adopcji metody.

Próba była celowa i mała: trzy zmiany, jedno repo, jedna bazowa wersja i środowisko macOS. Ten sam agent implementował i oceniał; nie jest to niezależny audyt. Nie zweryfikowano wszystkich scenariuszy ani aktualności lokalnych materiałów NASA w internecie. Nie stwierdzono zgodności z normą, bezpieczeństwa całej aplikacji ani przyczyn wszystkich wcześniejszych błędów. Po zmianie kodu trzeba ponownie sprawdzić właściwy zakres, a nie przenosić automatycznie wyniku z bazy.

#### Odbiór końcowy i dalsza praca

DoD przeglądu sprawdzone: baza i mapa źródeł są wskazane; struktura ma dowód; trzy przypadki mają 18 ocen; wszystkie ustalenia mają działania; rozdzielono wdrożenie/weryfikację/akceptację; wybrano trzy rekomendacje z kosztem i odbiorem; nakład i ograniczenia opisano. **Przegląd zakończony według DoD, z szacunkowym rozliczeniem czasu. Nie oznacza to akceptacji wyników przez użytkownika ani zakończenia siedmiu napraw.**

Rekomendacja dalszego stosowania: przy przyszłym przyroście sprawdzać tylko zmienioną potrzebę, dotknięte zależności i dowód; pełniejszy przegląd powtarzać przy regresji mimo zielonych testów, sprzecznych instrukcjach lub braku możliwości ustalenia aktualnego statusu. To propozycja metody, nie nowy obowiązek w WSPOLPRACA. Po wdrożeniu działań powtórzyć test nawigacji trzech przypadków i warunki zamknięcia wpisów — bez ponawiania całego pilotażu.

**Następny konkretny krok:** przyrost 1 z rejestru — naprawa etykiety konfliktu wraz z testem odtwarzającym błąd. Właściciel agent; realizacja po zleceniu wdrożenia. Rejestr pozostaje jedynym miejscem bieżącego śledzenia napraw, a ten raport jest zakończonym zapisem przeglądu.


## Otwarte

| Temat | Właściciel | Następny krok |
|---|---|---|
| Brak otwartych PIL-U; próby ręczne 29/30 poza zamknięciem regresji | Agent / użytkownik | Agent przygotowuje próbę, użytkownik ocenia B/E/F i notatnik P21. |
