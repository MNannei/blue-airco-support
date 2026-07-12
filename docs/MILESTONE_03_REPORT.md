# Milestone 03 Report

## Obiettivo

Introdurre persistenza PostgreSQL asincrona, migrazioni, ticket, messaggi inbound, safety assessment, audit immutabile e fondamenta webhook senza canali reali o generazione automatica.

## Schema dati

Lo schema include `User`, `Customer`, `Contact`, `Vessel`, `ProductUnit`, `Ticket`, `Message`, `SafetyAssessment`, `AuditEvent` e `WebhookEvent`. Tutte le entità usano UUID, timestamp e stato. I riferimenti sono chiavi esterne; payload webhook e metadata audit sono JSON. Gli ID messaggio esterni hanno vincoli univoci.

## Migrazione

La revisione `0001_initial_schema` crea e rimuove l'intero schema in ordine referenziale. L'applicazione non invoca `create_all`; upgrade e downgrade sono operazioni Alembic esplicite.

## Controlli applicativi

- Sessioni SQLAlchemy asincrone tramite dependency injection.
- Transazioni esplicite nei servizi.
- Deduplicazione ordinaria e concorrente basata su vincolo database.
- Audit safety persistito con input anonimizzato.
- AuditEvent immutabile tramite eventi ORM.
- Conservazione di ticket e messaggio se la fase safety non può essere persistita.
- Endpoint esclusivamente interni, privi di invio outbound.

## Test

Sono inclusi test unitari di stato ticket, test migrazioni, persistenza, idempotenza sequenziale e concorrente, errore database, immutabilità audit, collegamento unità, API interne e scenario safety persistito. Il conteggio e l'esito effettivi sono quelli pubblicati dal run GitHub Actions della milestone.

## Limiti e rischi

- Gli endpoint interni non implementano ancora autenticazione e non devono essere esposti pubblicamente.
- Audit e ticket sono persistiti, ma non esistono retention policy o cifratura applicativa dedicata.
- L'anonimizzazione resta basata su pattern.
- Non sono implementati webhook reali, dashboard, OpenAI, WhatsApp, diagnosi certe o decisioni di garanzia.

## Divieto di invio automatico

Nessun componente invia messaggi al cliente. Le operazioni gestiscono soltanto messaggi inbound e restituiscono esplicitamente `customer_message_sent=False`.
