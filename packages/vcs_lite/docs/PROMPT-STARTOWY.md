Kontynuujemy projekt vcs-lite (lekki panel gita w Tkinterze na macOS) w ~/PycharmProjects/byte-brewery/packages/vcs_lite.

Zanim cokolwiek zrobisz, przeczytaj:
1. docs/WSPOLPRACA.md: konwencja współpracy (BLUF, decyzje do podpisu z rekomendacją, lista spraw dla mnie (CCIR), jeden temat na wiadomość, tabela „Otwarte” z właścicielem). Ma pierwszeństwo nad pozostałymi zasadami.
2. docs/SPEC.md: decyzje DEC-VCS-001–109 z cytatami, wymagania REQ-VCS-001–034, rejestr pytań i sekcja „Punkt wznowienia” (stan i następne kroki).
3. docs/DESIGN.md: DES-VCS-001–060.
4. docs/ui-reference/UI-REFERENCE.md oraz E-01*.html, E-01.png, E-03*.html, E-04-szukaj.html, E-05-diff.html: wiążący wzorzec wyglądu (E-03 strona diffu Markdown, E-04 okno „Szukaj w plikach”, E-05 diff lewo–prawo w przeglądarce).
5. docs/PROPOZYCJA-szukaj.md: analiza „Szukaj w plikach” (wykonane, REQ-VCS-033).
6. docs/RETROSPEKTYWA.md: jak pracowaliśmy i czego unikać.
7. docs/ACCEPTANCE.feature (AT-VCS-001–046), docs/TRACE.md (generowany), docs/MANUAL-UI.md (kroki 1–17 potwierdzone).

Zasady pracy:
- Po polsku, według docs/WSPOLPRACA.md.
- Commity tylko na moje polecenie; pushe robię sam albo na wyraźne polecenie. Przed commitem: testy na samym stanie indeksu (git checkout-index do katalogu tymczasowego). Nigdy git add na całym katalogu (wpada .DS_Store), tylko wskazane pliki. Kolejność: najpierw commit ze specyfikacją, potem kod z testami i TRACE.md.
- Specyfikacja przed kodem: decyzja (DEC z moim cytatem) → REQ/DES/AT → test, który oblewa z właściwego powodu → kod. Nazwy testów od ID (test_req_vcs_…, test_at_vcs_…, test_des_vcs_…); każdy moduł w src/ ma linię „Trace: …”. Wygląd: najpierw makieta HTML do akceptacji.
- Testy w ~/PycharmProjects/byte-brewery: .venv/bin/python -m pytest -p no:cacheprovider -q packages/vcs_lite/tests > <scratchpad>/log.txt 2>&1 i czytaj pełny log (nie ucinaj grepem treści błędów). Obecnie 553 testy przechodzą. Nazwy plików testów muszą być unikalne w całym katalogu tests/.
- Zrzuty robię sam. Po zmianie UI uruchom okno i poproś o zrzut.
- Okno do pracy: w byte-brewery `uv run vcs-lite` (moje ustawienia, ~/Library/Application Support/vcs-lite/settings.json; pakiet zainstalowany edytowalnie, więc restart okna wystarcza). Okno do prób: python tools/make_demo.py <pusty folder w scratchpadzie>, potem w packages/vcs_lite: PYTHONPATH=src ../../.venv/bin/python -m vcs_lite.ui.main --settings <folder>/settings.json (w tle).

Ustalenia techniczne:
- Tk w .venv wymaga ui/tkenv.prepare_tk() (OBS-VCS-009). Przyciski to tk.Button z highlightbackground, nie ttk. Zaokrąglenia: widgets.rounded_rect. Własne kontrolki (pasek boczny, lista plików, przełącznik „Widok” SegmentedControl) rysujemy na tk.Canvas.
- W podklasach tk.Canvas nie używaj nazw pól, które ma Tkinter (np. self._options przesłania metodę i okno nie startuje).
- Tk nie dostarcza zdarzeń myszy i klawiatury do ukrytego okna testowego: testuj, że zdarzenie jest przypięte, i wywołuj obsługę wprost. Po każdym przerysowaniu Canvas identyfikatory elementów są nowe: pobieraj je ponownie w teście.
- tk_popup na macOS blokuje test: pozycje menu liczy FileList.prepare_menu, osobno od wyświetlenia.
- Git uruchamia wyłącznie core/gitcli (DES-VCS-001); strumieniowo GitCli.stream. Strony w przeglądarce: core/pagekit (wspólne), core/mdpage (Markdown), core/textpage (lewo–prawo, tekst), core/pageview (adaptery na porcie ExternalDiffTool, at_line), core/filekind (typ pliku), core/browser (domyślna przeglądarka z macOS); okno nie importuje markdown_it (limit 60 MB). Beyond Compare usunięty (DEC-VCS-102); wtyczka CLI tylko przez external_diff_tool w settings.json (DEC-VCS-106). Na stronie surowy HTML jest tekstem poza <br> (DEC-VCS-088); CSP dopuszcza tylko Google Fonts.
- Atrapy w tests/world.py: tool (strona lewo–prawo), md_tool, md_reader i text_reader (at_line zapisuje linię), external (wtyczka, domyślnie None), browsed (pliki w przeglądarce), copies (kopie wersji spoza dysku), opened (polecenia open), timers (FakeTimers zamiast after), search_session(); ManualWorker.settle().
- git grep -w jest błędne dla polskich liter (trafia „w” w „żółw”); -i działa (sprawdzone na git 2.47.1).
- Testy nigdy nie otwierają prawdziwej przeglądarki: strony z --no-open albo atrapy; pomiar pamięci trzyma porównanie przez wtyczkę z atrapą.
- git mv zapisuje w indeksie: przenoś pliki zwykłym mv (indeks rusza tylko użytkownik albo commit na polecenie).

Następny krok według „Punktu wznowienia”:
1. „Szukaj w plikach” (REQ-VCS-033) i przeglądarka zamiast Beyond Compare (REQ-VCS-023, REQ-VCS-034) gotowe i potwierdzone na ekranie (kroki 16, 6, 17).
2. Niezatwierdzone: specyfikacja i kod obu przyrostów; commity na polecenie, najpierw specyfikacja. Katalog packages/vcs_lite/assets/ nie pochodzi od agenta; nie ruszaj bez pytania.
3. Na przyszłość (bez terminu): własne okno podglądu plików (Q-VCS-056).
