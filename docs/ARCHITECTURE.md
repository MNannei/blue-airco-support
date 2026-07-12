# Architecture

## Moduli

- `api`: interfaccia HTTP FastAPI.
- `config`: configurazione caricata dall'ambiente tramite `pydantic-settings`.
- `core.safety`: confine delle future regole di sicurezza e validazione.
- `core.audit`: anonimizzazione e modello audit del safety engine.
- `database`: engine SQLAlchemy asincrono, session factory e dependency injection.
- `models`: entità persistite per utenti, clienti, unità, ticket, messaggi, safety, audit e webhook.
- `services`: transazioni applicative, deduplicazione e persistenza safety/audit.
- `workflows`: orchestrazione esplicita dei passaggi operativi.
- `alembic`: schema versionato; nessun `create_all` viene eseguito dall'applicazione.

## Persistenza e transazioni

PostgreSQL è raggiunto tramite `DATABASE_URL` con driver `asyncpg`. Il ticket e il messaggio inbound vengono salvati prima della valutazione safety: un errore nella persistenza safety marca il ticket come `safety_persistence_error` senza eliminarlo. SafetyAssessment e AuditEvent vengono quindi salvati nella transazione di valutazione. Gli AuditEvent non possono essere aggiornati o eliminati tramite ORM.

`external_message_id` è protetto da vincolo univoco. Un controllo anticipato gestisce i retry ordinari; il vincolo database risolve anche la concorrenza. Ogni duplicato ignorato genera un AuditEvent.

## API interne

- `POST /internal/tickets`
- `GET /internal/tickets/{ticket_id}`
- `POST /internal/tickets/{ticket_id}/messages`
- `GET /internal/tickets/{ticket_id}/audit`

Questi endpoint sono interni, non pubblici e non includono ancora autenticazione completa.

## Flusso previsto

```text
messaggio
  → safety engine
  → identificazione macchina
  → workflow
  → fonti approvate
  → bozza
  → approvazione umana
```

La bozza non viene inviata automaticamente. Non sono presenti integrazioni OpenAI, WhatsApp o automazioni rivolte ai clienti. Il testo non determina diagnosi certe o decisioni di garanzia.
