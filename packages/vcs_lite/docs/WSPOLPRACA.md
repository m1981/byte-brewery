# vcs-lite — konwencja współpracy użytkownika i agenta

Przyjęta 2026-10-22 (użytkownik: „D1: tak D2: do docs/WSPOPLRACA.md”). Wzór: doktryna „Completed Staff Work” (memorandum płk. Archera J. Lercha dla Provost Marshal General armii USA, „Army and Navy Journal”, 29 stycznia 1942), BLUF z pisarstwa wojskowego oraz zamiar dowódcy i CCIR (informacje krytyczne dla decyzji dowódcy). Cel: użytkownik nie jest przeładowany treścią, a nadal podejmuje wszystkie ważne decyzje.

Zastępuje regułę promptu startowego „najpierw wypisz pytania”: na starcie sesji agent podaje rozumienie zadania w BLUF i tylko pytania z listy CCIR, każde z rekomendacją.

Wspólny język rozmów, makiet i kodu: [SLOWNIK.md](SLOWNIK.md). Dla paneli używamy nazw i oznaczeń A–F zamiast „lewe/prawe okno”.

## Zasady

1. **Zamiar użytkownika** to `SPEC.md`, `DESIGN.md`, `ui-reference/` i „Punkt wznowienia”. W ich granicach agent sam ustala szczegóły (nazwy, kształt testów, kolejność drobnych zmian) i zapisuje każdą taką decyzję w dokumentach jako „decyzja agenta”, żeby użytkownik mógł ją później podważyć.
2. **Do użytkownika trafia tylko lista CCIR:**
   - zmiana czegoś, co użytkownik już zaakceptował;
   - odstępstwo od wzorca wyglądu;
   - luka albo sprzeczność w specyfikacji;
   - działanie nieodwracalne albo na zewnątrz: push, prawdziwe repozytoria, instalacja w `.venv`, publikacja;
   - zmiana kolejności prac;
   - blokada, której agent nie umie obejść.
3. **Decyzja jako gotowe działanie do podpisu:** jedna rekomendacja, jedno zdanie „dlaczego”, jedno zdanie „co, jeśli nie”; alternatywy najwyżej wymienione. Odpowiedź w formie „D1: tak”. Najwyżej 3 decyzje w wiadomości; pozostałe czekają w rejestrze pytań w `SPEC.md`.
4. **Układ każdej wiadomości:**
   - BLUF: 1–3 zdania, co zrobione i czego agent potrzebuje;
   - **Do decyzji** (D1–D3);
   - **Czeka na Ciebie**: zrzuty, kroki ręczne;
   - **Informacyjnie**: kilka linii; szczegóły w dokumentach, w wiadomości tylko odnośnik.
5. **Otwarte:** tabela (kiedy, mówi punkt 6); każdy punkt ma właściciela (użytkownik / agent) i następny krok. Żaden temat nie zostaje bez opiekuna; temat odłożony trafia do „Punktu wznowienia” albo rejestru pytań.
6. **Jeden temat na wiadomość** (użytkownik 2026-10-22: „Jeden tamtat na raz bo sie gubie”). Wiadomość dotyczy jednej sprawy: jednej decyzji albo jednej czynności użytkownika. Pełna tabela „Otwarte” tylko na prośbę albo na końcu etapu; poza tym na końcu jedna linia „Dalej: …”. Pozostałe tematy czekają w „Punkcie wznowienia” w `SPEC.md`, więc żaden nie ginie.
7. **Test przed wysłaniem:** czy agent podpisałby proponowane działanie sam i postawił na nie swoją reputację? Szkic jest dozwolony, ale kompletny, a nie przerzucający pracę na użytkownika.

## Obowiązujące reguły wykonania

- Język polski.
- **Commit i push:** od 2026-10-26 obowiązuje polecenie użytkownika „rob commity po kazdym logicznym przyroscie”. Agent wykonuje commit po logicznym przyroście bez ponownego pytania. Push wykonuje użytkownik albo agent na wyraźne polecenie; zgoda na commit nie obejmuje pushowania. Ta reguła zastępuje dawną zasadę „commity i pushe robi użytkownik”.
- Dodawaj i commituj tylko jawnie wskazane ścieżki (`git add <ścieżki>`, `git commit -- <ścieżki>`), nigdy cały katalog. Zachowuj niezwiązane zmiany użytkownika w indeksie i kopii roboczej. Przed commitem sprawdź przygotowaną wersję: `git checkout-index --all --prefix=<katalog tymczasowy>/`, dobrane testy w tej kopii, [kontrola TRACE przed/po](#kontrola-aktualności-trace-na-kopii-indeksu) i pełny log wyniku. Dla samej dokumentacji wystarczy kontrola odnośników/treści i istniejące testy śledzenia, bez pełnej suity produktu.
- Nowe wymagania: najpierw commit specyfikacji, potem kod z testami i wygenerowanym TRACE. Naprawa zachowania już wymaganego korzysta z istniejących ID.
- TDD, nazwy testów od ID, linia `Trace:` w modułach.
- Zrzuty robi użytkownik; agent uruchamia okno i porównuje zrzut ze wzorcem.

## Kontrola aktualności TRACE na kopii indeksu

Przy weryfikacji indeksu uruchom poniższy blok **w katalogu `packages/vcs_lite` wyeksportowanej kopii**, Pythonem z `.venv` repo głównego (`python` poniżej oznacza ten interpreter). Zachowaj pełne stdout/stderr w logu poza kopią, np. przez `> /private/tmp/vcs-trace-check.log 2>&1`, i przeczytaj log. Kontrola używa istniejącego testu/generatora; nie zmienia jego trybu pracy. Wynik zaliczony wymaga zarówno sukcesu pytest, jak i identycznych bajtów TRACE przed/po. Brak pliku przed próbą też jest błędem aktualności.

```python
from pathlib import Path
import hashlib
import subprocess
import sys

trace = Path('docs/TRACE.md')
before = trace.read_bytes() if trace.exists() else None
result = subprocess.run([
    sys.executable, '-m', 'pytest', '-p', 'no:cacheprovider', '-q',
    'tests/test_traceability.py',
])
after = trace.read_bytes() if trace.exists() else None
fingerprint = lambda data: hashlib.sha256(data).hexdigest() if data is not None else 'MISSING'
print('TRACE before SHA256:', fingerprint(before), flush=True)
print('TRACE after  SHA256:', fingerprint(after), flush=True)
current = before is not None and before == after
print('TRACE aktualny w indeksie:', 'TAK' if current else 'NIE', flush=True)
# Pytest może naprawić TRACE i przejść; kontrola nadal odrzuca nieaktualne wejście.
sys.exit(result.returncode or (0 if current else 1))
```

Jeśli kontrola odrzuci aktualność, nie commituj na podstawie naprawionej kopii. W kopii roboczej wygeneruj TRACE jawnie: `python -m pytest -p no:cacheprovider -q tests/test_traceability.py -k test_req_vcs_207_matrix_is_generated`. Sprawdź różnicę, dodaj wyłącznie `docs/TRACE.md` oraz właściwe pliki przyrostu do indeksu, wyeksportuj **nową** kopię i ponów kontrolę. Jeśli pytest zgłosił inne błędy, usuń ich przyczynę przed ponowną weryfikacją. Generator pozostaje dostępny osobno; nie wolno uznać jego sukcesu za dowód aktualności wejścia.

To kontrola wersji zapisanej i powiązań, nie dowód poprawności zachowania produktu. Dobierz osobno testy zmienionego zachowania. Nie trzeba powtarzać pełnej suity tylko z powodu aktualizacji TRACE.
