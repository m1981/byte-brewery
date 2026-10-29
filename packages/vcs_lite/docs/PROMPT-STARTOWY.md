Kontynuujemy projekt vcs-lite (lekki panel gita w Tkinterze na macOS) w ~/PycharmProjects/byte-brewery/packages/vcs_lite.

Zacznij od:
1. [WSPOLPRACA.md](WSPOLPRACA.md): obowiązujące reguły współpracy i wykonania, w tym zakres zgody na commit/push. Późniejsze polecenia użytkownika mają pierwszeństwo.
2. [SPEC — Punkt wznowienia](SPEC.md#punkt-wznowienia): bieżący stan, dowód, właściciel i następny krok. To punkt wejścia do pracy, bez czytania kroniki. Progi pamięci są w [wymaganiach jakościowych](SPEC.md#wymagania-jakościowe), wyniki dotyczą konkretnych wersji wskazanych w tabeli stanu.
3. Dla dotkniętego obszaru: [SPEC](SPEC.md), [DESIGN](DESIGN.md), [ACCEPTANCE](ACCEPTANCE.feature), [TRACE](TRACE.md) (generowany), [MANUAL-UI](MANUAL-UI.md) (odbiór ręczny) oraz [wzorzec wyglądu](ui-reference/UI-REFERENCE.md). Nie kopiuj tutaj zakresów ID ani liczby zaliczonych testów.
4. [SLOWNIK](SLOWNIK.md): wspólne nazwy obszarów; [RETROSPEKTYWA](RETROSPEKTYWA.md): doświadczenia historyczne. Propozycje i makiety czytaj według odsyłaczy dla aktualnego zadania.

Zasady pracy:
- Po polsku, według docs/WSPOLPRACA.md.
- Commit/push i weryfikacja indeksu: [WSPOLPRACA — Obowiązujące reguły wykonania](WSPOLPRACA.md#obowiązujące-reguły-wykonania).
- Specyfikacja przed kodem: decyzja (DEC z moim cytatem) → REQ/DES/AT → test, który oblewa z właściwego powodu → kod. Nazwy testów od ID (test_req_vcs_…, test_at_vcs_…, test_des_vcs_…); każdy moduł w src/ ma linię „Trace: …”. Wygląd: najpierw makieta HTML do akceptacji.
- Testy w ~/PycharmProjects/byte-brewery: .venv/bin/python -m pytest -p no:cacheprovider -q packages/vcs_lite/tests > <scratchpad>/log.txt 2>&1 i czytaj pełny log (nie ucinaj grepem treści błędów). Wynik podawaj z wersją, zakresem i logiem; dobieraj testy do zmiany. Nazwy plików testów muszą być unikalne w całym katalogu tests/.
- Zrzuty robię sam. Po zmianie UI uruchom okno i poproś o zrzut.
- Aplikacja: /Applications/vcs-lite.app (python tools/make_app.py w packages/vcs_lite; przebudowa tylko przy zmianie logo). Okno do pracy: w byte-brewery `uv run vcs-lite` (moje ustawienia, ~/Library/Application Support/vcs-lite/settings.json; pakiet zainstalowany edytowalnie, więc restart okna wystarcza). Okno do prób: python tools/make_demo.py <pusty folder w scratchpadzie>, potem w packages/vcs_lite: PYTHONPATH=src ../../.venv/bin/python -m vcs_lite.ui.main --settings <folder>/settings.json (w tle).

Ustalenia techniczne:
- Tk w .venv wymaga ui/tkenv.prepare_tk() (OBS-VCS-009). Przyciski to tk.Button z highlightbackground, nie ttk. Zaokrąglenia: widgets.rounded_rect. Własne kontrolki (pasek boczny, lista plików, przełącznik „Widok” SegmentedControl) rysujemy na tk.Canvas.
- W podklasach tk.Canvas nie używaj nazw pól, które ma Tkinter (np. self._options przesłania metodę i okno nie startuje).
- Tk nie dostarcza zdarzeń myszy i klawiatury do ukrytego okna testowego: testuj, że zdarzenie jest przypięte, i wywołuj obsługę wprost. Po każdym przerysowaniu Canvas identyfikatory elementów są nowe: pobieraj je ponownie w teście.
- tk_popup na macOS blokuje test: pozycje menu liczy FileList.prepare_menu, osobno od wyświetlenia.
- Git uruchamia wyłącznie core/gitcli (DES-VCS-001); strumieniowo GitCli.stream. Strony w przeglądarce: core/pagekit (wspólne), core/mdpage (Markdown), core/textpage (lewo–prawo, tekst), core/pageview (adaptery na porcie ExternalDiffTool, at_line), core/filekind (typ pliku), core/browser (domyślna przeglądarka z macOS); okno nie importuje markdown_it (próg i scenariusz: REQ-VCS-100 w SPEC, osobny scenariusz dużej listy: REQ-VCS-105). Beyond Compare usunięty (DEC-VCS-102); wtyczka CLI tylko przez external_diff_tool w settings.json (DEC-VCS-106). Na stronie surowy HTML jest tekstem poza <br> (DEC-VCS-088); CSP dopuszcza tylko Google Fonts.
- Atrapy w tests/world.py: tool (strona lewo–prawo), md_tool, md_reader i text_reader (at_line zapisuje linię), external (wtyczka, domyślnie None), browsed (pliki w przeglądarce), copies (kopie wersji spoza dysku), opened (polecenia open), timers (FakeTimers zamiast after), search_session(); ManualWorker.settle().
- git grep -w jest błędne dla polskich liter (trafia „w” w „żółw”); -i działa (sprawdzone na git 2.47.1).
- Testy nie ruszają schowka użytkownika: okno dostaje atrapę `clipboard`.
- Testy nigdy nie otwierają prawdziwej przeglądarki: strony z --no-open albo atrapy; pomiar pamięci trzyma porównanie przez wtyczkę z atrapą.
- git mv zapisuje w indeksie: przenoś pliki zwykłym mv (indeks rusza tylko użytkownik albo commit przyrostu).
