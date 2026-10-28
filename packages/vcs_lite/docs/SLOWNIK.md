# Wspólny język vcs-lite — ubiquitous language

Wspólny słownik rozmów, makiet, wymagań i kodu. Używamy nazw poniżej zamiast niejednoznacznych „lewe okno” i „historia zmian”. Litery A–F oznaczają obszary makiety P21, nie identyfikatory wymagań. Notatnik P21 wdrożony 2026-10-28; wygląd czeka na próbę ręczną użytkownika.

## Obszary aplikacji

| Nazwa | Znaczenie | Obszar / kod |
|---|---|---|
| Okno główne | Całe okno vcs-lite, z repozytoriami, bieżącą pracą i historią. | `MainWindow` |
| Lista repozytoriów | Repo obserwowane i ich bieżący stan. Kliknięcie wybiera repo. | A / `RepoSidebar` |
| Lista zmian | Pliki bieżącego repo, pogrupowane według statusu Git. Może też pokazywać Foldery lub Projekt. | B / `FileList` |
| Notatnik repo | Edytor notatki bieżącego repo, domyślnie dostępny przy liście zmian. | C / `NotesPanel` |
| Panel commita | Pole wiadomości i przyciski tworzenia commita. Należy wyłącznie do listy zmian; nie obejmuje notatnika. | D |
| Lista commitów | Chronologiczna/topologiczna historia, graf, autor, data i sumy linii commitów. | E / `CommitList` |
| Szczegóły commita | Opis, metadane i lista plików wybranego commita. | F / `CommitView` |
| Lista plików commita | Pliki zmienione przez wybrany commit; część jego szczegółów. | Wewnątrz F |
| Historia repo | Cały dolny obszar: lista commitów i szczegóły wybranego commita. | E + F / `HistoryPanel` |
| Obszar roboczy repo | Lista zmian, notatnik i panel commita. | B + C + D |
| Granica paneli | Przesuwana linia określająca rozmiar paneli. Nie jest paskiem przewijania. | separator / sash |
| Pasek przewijania | Kontrolka przesuwania treści wewnątrz panelu. Suwak to jej ruchoma część. | scrollbar |
| Nagłówek panelu | Stały pasek z nazwą, sterowaniem lub opisami kolumn. | header |

Układ P21: **D pod B; C nad F; E pod B i D oraz pod listą repozytoriów**. Nagłówek historii biegnie przez całą szerokość okna nad E i F. C i F mają tę samą prawą kolumnę, rozdzieloną wspólnym nagłówkiem historii.

## Repo i Git

| Termin | Znaczenie |
|---|---|
| rootdir | Katalog wyszukiwania repozytoriów; domyślnie `~/PycharmProjects`. |
| Repo obserwowane | Repo wybrane w oknie „Repozytoria” do pokazywania w aplikacji. |
| Bieżące repo | Repo wybrane w A; określa zawartość B, C, D i historię E/F. |
| Wybrany commit | Commit zaznaczony w E; określa F. Nie przełącza notatki repo. |
| HEAD | Bieżący commit wskazywany przez Git, zwykle przez aktualną gałąź. W świeżym repo wskazuje gałąź bez commita. |
| Indeks | Stan przygotowany do następnego commita, czyli staging area. |
| Kopia robocza | Pliki repo na dysku. |
| Staged | Zmiany indeksu względem HEAD. |
| Changes | Zmiany śledzonych plików kopii roboczej względem indeksu. |
| Unversioned | Pliki nieśledzone i nieignorowane. |
| Conflicts | Pliki w stanie niescalonym, np. po merge lub rebase. |
| Upstream | Gałąź śledzona przez bieżącą gałąź lokalną, zwykle zdalna. |
| Commit | Zapisany w Git stan projektu wraz z metadanymi i powiązaniem z rodzicami. |
| Wiadomość commita | Tekst wpisany w D i zapisany w metadanych commita. |
| Diff / porównanie | Różnice między dwiema wersjami pliku. |

Jeden plik może jednocześnie należeć do Staged i Changes. Lista zmian pokazuje pracę na dysku/indeksie; lista plików commita pokazuje zapisany commit.

## Notatki i stan interfejsu

| Termin | Znaczenie |
|---|---|
| Notatka repo | Jeden trwały tekst przypisany do pełnej ścieżki repo, przechowywany poza jego katalogiem, obok ustawień aplikacji. |
| Pusta notatka | Dostępny edytor bez treści; nie wymaga utworzenia pliku przed pierwszą edycją. |
| Fragment notatki | Zaznaczony tekst, który można skopiować; nie jest osobnym rekordem ani zadaniem. |
| Prompt roboczy | Tekst przygotowany dla agenta. Sam zapis w notatce nie wysyła go agentowi. |
| Autozapis | Zapis zmienionej notatki po przerwie w pisaniu i przy opuszczeniu edytora, zmianie repo lub zamknięciu. |
| Fokus | Kontrolka, która aktualnie odbiera klawiaturę; niezależna od zaznaczenia pliku czy commita. |
| Zaznaczenie | Trwały wybór wiersza albo fragmentu tekstu, niezależny od położenia wskaźnika myszy. |
| Najechanie / hover | Tymczasowe wyróżnienie elementu pod wskaźnikiem. |
| Zwinięcie panelu | Ukrycie obszaru w układzie bez usunięcia jego danych. |

## Liczby zmian

| Termin | Znaczenie |
|---|---|
| Liczby linii +/− | Osobne liczby dodanych i usuniętych linii; nie ich różnica i nie liczba plików. |
| Liczby pliku | Liczby dla jednego pliku w B lub w liście plików F. |
| Suma commita | Łączne liczby tekstowych zmian wszystkich plików commita, pokazywane w E i podsumowaniu F. Merge porównywany z pierwszym rodzicem; pierwszy commit z pustym drzewem. |
| Kompaktowe +/− | Zapis `+334 −34` z małym odstępem; zielone dodania, czerwone usunięcia, szare zera. Wspólny wygląd w B, E i F. |
| Binarne | Zmiana pliku, dla której Git nie podaje liczby linii. Nie jest zerową zmianą tekstową. |
| Brak danych | `—`; nie zastępujemy go pozorną wartością `+0 −0`. |

## Jak używamy słownika

- W uwagach podajemy nazwę obszaru, opcjonalnie literę: „notatnik C”, „lista commitów E”.
- „Notatka” to treść, „notatnik” to edytor, „wiadomość commita” to tekst w D.
- Nowe pojęcie dopisujemy tutaj przy pierwszym uzgodnieniu; znaczenia domenowe mają jedno źródło w tym pliku. SPEC i DESIGN opisują reguły działania i realizację.
- Nazwy techniczne służą powiązaniu z kodem; rozmowa i etykiety interfejsu używają nazw domenowych.
