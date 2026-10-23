# vcs-lite — retrospektywa sesji 2026-10-22–23

Spojrzenie z perspektywy inżyniera procesów SDLC, programisty i inżyniera wymagań: jak przebiegała praca, co pozwoliło szybko dowieźć kolejne przyrosty, co nie zadziałało. Sporządzone przez agenta na prośbę użytkownika 2026-10-23.

## Krótko

Każdą zmianę prowadziła ta sama pętla: obserwacja użytkownika (najczęściej zrzut ekranu) → diagnoza na faktach → propozycja z makietą → decyzja użytkownika → zapis w specyfikacji → test, który najpierw oblewa → kod → zrzut użytkownika → commit na polecenie. Najwięcej dały trzy rzeczy: zapisane decyzje z cytatami, automatyczne sprawdzanie śledzenia powiązań razem z TDD (łapały błędy agenta) oraz korekty sposobu rozmowy wprowadzane przez użytkownika („jeden temat na raz”, „nie zostawiajmy osieroconych tematów”).

## Liczby

| Miara | Początek | Koniec |
|---|---|---|
| Testy | 242 przechodzą, 1 celowo oblewa | 412 przechodzi |
| Decyzje w `SPEC.md` | DEC-VCS-001–058 | DEC-VCS-001–092 |
| Commity agenta | — | 21, każdy sprawdzony testami na samym stanie indeksu |
| Kroki `MANUAL-UI.md` | potwierdzone 1–4 i 15 | potwierdzone 1–15 |

## Przebieg

1. **Domknięcie zaplanowanej pracy.** Ręczna weryfikacja UI-6, odświeżanie po fokusie i pomiar pamięci (UI-7). Zrzuty wyciągnęły dwie luki: brakujący chip konfliktu i merge, którego nie dało się zakończyć (OBS-VCS-010, DEC-VCS-065).
2. **Ustalenie sposobu współpracy.** Konwencja w [WSPOLPRACA.md](WSPOLPRACA.md): BLUF, decyzje do podpisu, lista spraw dla użytkownika (CCIR), jeden temat na wiadomość.
3. **Przyrosty z obserwacji użytkownika.**
   - lista plików: podpowiedzi i długie ścieżki, przegląd plik po pliku, zaznaczanie jak w Eksploratorze, menu kontekstowe, „Dodaj do .gitignore”, zawsze widoczny Staged;
   - diff Markdown w przeglądarce: demo z 22 przypadkami, kolory obu motywów, czcionka, podkreślenia zamiast tła, `<br>`;
   - przełącznik „Widok” i drzewo projektu.
4. **Analiza przed budową.** Wyszukiwanie w plikach ([PROPOZYCJA-szukaj.md](PROPOZYCJA-szukaj.md)).

## Proces jednego przyrostu

1. **Obserwacja.** Zrzut albo zdanie: „jest rozmyte”, „przewija się w pustkę”, „tooltip koliduje z tekstem”.
2. **Diagnoza na faktach, nie na pamięci.** Lektura kodu, uruchomienie gita, pomiar. Przykłady: `footprint` dla pamięci; `git grep -w` trafiający w „żółw”; kontrast kolorów policzony liczbowo; zrzut z DevTools z `font-weight: 700`, który wskazał sztuczne pogrubienie czcionki.
3. **Propozycja do podpisu.** Jedna rekomendacja, „dlaczego”, „co, jeśli nie”. Przy wyglądzie zawsze makieta HTML albo demo przed kodem (P11–P14, wzorzec E-03, galeria przypadków Markdown).
4. **Decyzja i specyfikacja.** Decyzja zapisana jako DEC z cytatem użytkownika, potem wymaganie, projekt i scenariusz AT. Specyfikacja zawsze przed kodem, więc commit ze specyfikacją szedł pierwszy.
5. **TDD.** Test oblewa z właściwego powodu, potem kod, potem pełny zestaw testów z logiem zapisanym do pliku.
6. **Weryfikacja na żywym oknie.** Zrzut albo „OK” od użytkownika.
7. **Commit tylko na polecenie.** Przed nim testy na samym stanie indeksu (wypakowanym do katalogu tymczasowego).

## Komunikacja

Co działało:

- **Decyzje D1–D3 z rekomendacją.** Odpowiedzi były krótkie („D1 tak”, „12a i 12b są genialne”), a zapis jednoznaczny.
- **Zrzuty jako źródło prawdy.** Prawie każdy wyłapał coś, czego testy nie widzą: kontrast w ciemnym motywie, nachodzący tekst, sztuczne pogrubienie.
- **Makiety przed kodem.** Wybór między wariantami kosztował minutę zamiast przeróbki kodu.
- **Korekty procesu przez użytkownika, od razu zapisane w konwencji.** „Jeden temat na raz” skróciło wiadomości; „nie zostawiajmy osieroconych tematów” wprowadziło tabelę „Otwarte” i pilnowanie „Punktu wznowienia”.
- **Podział ról.** Użytkownik wnosił cel i ocenę z perspektywy użycia („czytam częściej .md niż kod”), agent diagnozę i wykonanie, z jawnym zaznaczaniem, czego nie wie.

## Co pomagało agentowi

- **`SPEC.md` z cytatami i „Punkt wznowienia”.** Pamięć między sesjami: wiadomo, co ustalono i dlaczego.
- **Test śledzenia powiązań.** Każde wymaganie ma test, każdy moduł linię `Trace:`; kilka razy przypomniał o brakującym scenariuszu.
- **TDD jako siatka bezpieczeństwa.** Złapało błędy agenta, zanim dotarły do użytkownika: pole `_options` przesłaniające metodę Tkintera (okno nie startowało), znikający nagłówek tabeli, sklejone słowa w diffie, kolizję kluczy w Workerze.
- **Izolowane próby.** Repozytoria demo i prototyp w scratchpadzie, bez ryzyka dla prawdziwych repozytoriów.
- **Prompt startowy z ustaleniami technicznymi** (ukryte okno testowe, Tk w `.venv`), bez odkrywania ich od nowa.

## Co nie działało i wnioski

- **Błędy agenta:**
  - rekomendacja strony „ours” w kroku 14; przy okazji wyszła prawdziwa luka;
  - przełącznik „Źródło” na stronie, który nie mógł uruchomić Beyond Compare; skorygowane;
  - `.DS_Store` dodany do indeksu przez `git add` na całym katalogu; wycofany przed commitem;
  - testy przechodzące z niewłaściwego powodu, np. przewijanie w dół i z powrotem w górę. Wniosek: zawsze sprawdzać, że test oblewa z właściwej przyczyny.
- **Ucięte logi.** Dwa razy filtrowanie wyjścia ucięło treść błędu niestabilnego testu pamięci. Wniosek: pełne logi przebiegów zapisywać do plików.
- **Za długie wiadomości na początku**, do czasu prośby o jeden temat na raz.
- **Jeden duży commit** (`767cbf0`). Kilka funkcji zmieniało te same fragmenty `file_list.py`, więc nie dało się ich rozdzielić. Wniosek: commitować częściej, po każdym przyroście.

## Na następne sesje

- Konwencja z [WSPOLPRACA.md](WSPOLPRACA.md) zostaje bez zmian.
- Prompt startowy aktualizować o liczbę testów i nowe dokumenty.
- Commit po każdym zamkniętym przyroście, gdy użytkownik o to poprosi.
