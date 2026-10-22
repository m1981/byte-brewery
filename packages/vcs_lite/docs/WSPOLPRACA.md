# vcs-lite — konwencja współpracy użytkownika i agenta

Przyjęta 2026-10-22 (użytkownik: „D1: tak D2: do docs/WSPOPLRACA.md”). Wzór: doktryna „Completed Staff Work” (memorandum płk. Archera J. Lercha dla Provost Marshal General armii USA, „Army and Navy Journal”, 29 stycznia 1942), BLUF z pisarstwa wojskowego oraz zamiar dowódcy i CCIR (informacje krytyczne dla decyzji dowódcy). Cel: użytkownik nie jest przeładowany treścią, a nadal podejmuje wszystkie ważne decyzje.

Zastępuje regułę promptu startowego „najpierw wypisz pytania”: na starcie sesji agent podaje rozumienie zadania w BLUF i tylko pytania z listy CCIR, każde z rekomendacją.

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

## Bez zmian

- Język polski; commity i pushe robi użytkownik, agent o nie nie pyta.
- TDD, nazwy testów od ID, linia `Trace:` w modułach.
- Zrzuty robi użytkownik; agent uruchamia okno i porównuje zrzut ze wzorcem.
