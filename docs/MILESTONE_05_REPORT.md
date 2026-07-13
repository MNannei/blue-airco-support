# Milestone 05 Report — Knowledge Import

## Obiettivo

Importare in modo deterministico e auditabile la knowledge base tecnica Blue Airco mantenendo i file sorgente fuori dal repository pubblico.

## Implementazione

- Modelli per batch, casi, contenuti deduplicati, allegati, documenti, ambiti prodotto e trascrizioni.
- Migrazione Alembic `0002_knowledge_import`.
- Validazione preventiva di struttura, JSONL, ID, path, file e SHA-256.
- Vincolo permanente di accesso ristretto per `CASE-WA-010` e `CASE-WA-013`.
- Deduplicazione per hash con conservazione di tutti i percorsi sorgente.
- CLI interna `knowledge-import validate|run|report`.
- Import transazionale, idempotente e registrato in `AuditEvent`.

## Governance

Un documento è autorevole soltanto con stato `approved`. Le trascrizioni automatiche sono sempre non autorevoli fino a revisione umana. Campi modello, seriale e revisione vuoti restano sconosciuti.

## Test aggiunti

Sono presenti test unitari per validazione, hash, path traversal e accessi ristretti, oltre a test PostgreSQL per import transazionale, governance, audit e idempotenza.

## Stato di verifica

Il runtime locale non dispone di Python o Docker. I test non sono quindi dichiarati superati localmente: devono essere eseguiti dalla GitHub Actions dopo la pubblicazione delle sole modifiche software.

## Fuori ambito

Nessun dato cliente viene pubblicato nel repository. Non sono stati implementati OpenAI, WhatsApp, invio automatico, dashboard, diagnosi certe o decisioni di garanzia.
