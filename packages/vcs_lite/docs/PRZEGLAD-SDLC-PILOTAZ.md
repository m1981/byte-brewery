# Przegląd SDLC — założenia i plan pilotażu

Data: 2026-10-28. Wersja: 0.2. Status: pilotaż zaakceptowany; etap 1 zakończony, etapy 2–6 niewykonane.

Zlecenie użytkownika: „Zapisz zalozenia i plan pilotazu oraz DoD i spodziewane korzysci do pliku (md) oraz drugi plik (md) jako rejestr zmian”. Metodę zaproponował agent; użytkownik zaakceptował pilotaż 2026-10-28. Dokument nie zmienia obowiązujących wymagań produktu ani zasad współpracy.

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

- [x] Zidentyfikowano badany stan i źródła; wyniki można odnieść do konkretnej wersji.
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


## Otwarte

| Temat | Właściciel | Następny krok |
|---|---|---|
| Etap 2 — mapa źródeł | Agent | Następny etap po zakończonym etapie 1; wykonanie po zleceniu kontynuacji. |
