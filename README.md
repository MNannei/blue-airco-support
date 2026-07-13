# Blue Airco Support

Blue Airco Support è una piattaforma inizialmente pensata come copilota interno per i tecnici Blue Airco. In questa fase espone soltanto un servizio FastAPI minimale con endpoint di health check; non invia messaggi, non risponde automaticamente ai clienti e non integra OpenAI o WhatsApp.

## Requisiti

- Python 3.12
- Docker e Docker Compose, per PostgreSQL

## Installazione locale

### Windows (PowerShell)

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

### macOS e Linux

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

## Avvio

Avviare PostgreSQL:

```bash
docker compose up -d db
```

Applicare lo schema database (non viene usato `create_all`):

```bash
python -m alembic upgrade head
```

Per annullare la migrazione corrente:

```bash
python -m alembic downgrade base
```

Avviare quindi l'API dall'ambiente virtuale attivo:

```bash
python -m uvicorn app.main:app --reload
```

Il servizio risponde su `http://localhost:8000`; l'health check è disponibile su `GET /health`.

## Safety engine

La Milestone 2 introduce un motore deterministico, indipendente da LLM, che classifica segnali di sicurezza espliciti come `none`, `warning` o `immediate_stop`. I casi critici bloccano il workflow ordinario e richiedono escalation umana. Ogni valutazione produce un audit strutturato con input anonimizzato; il servizio non invia messaggi ai clienti e non determina cause tecniche certe.

## Ticket e persistenza

La Milestone 3 persiste ticket, messaggi inbound, safety assessment ed eventi audit in PostgreSQL tramite SQLAlchemy asincrono. Gli endpoint sotto `/internal` sono strumenti interni non autenticati e non devono essere esposti pubblicamente. La deduplicazione usa `external_message_id`; non esiste alcun invio automatico verso clienti.

## Test

```bash
python -m pytest
```

I test di integrazione richiedono PostgreSQL e lo schema Alembic aggiornato.

I test non sono stati eseguiti nell'ambiente corrente perché Python e Docker non sono disponibili.

## Continuous Integration

La workflow GitHub Actions in `.github/workflows/ci.yml` installa il progetto con le dipendenze di sviluppo, verifica che l'app sia importabile ed esegue automaticamente i test a ogni push e pull request. Il risultato è consultabile nella scheda **Actions** del repository su GitHub.

## Import della knowledge base

La knowledge base tecnica viene importata da un pacchetto locale governato. I dati grezzi dei clienti non devono essere aggiunti al repository pubblico.

```text
knowledge-import validate <bundle-path> --knowledge-root <knowledge-root>
knowledge-import run <bundle-path> --knowledge-root <knowledge-root>
knowledge-import report <batch-key>
```

Il validatore controlla hash SHA-256, percorsi, associazioni ai casi e stati di governance. I documenti non `approved` e le trascrizioni `machine_transcript_unreviewed` restano esclusi dalle fonti autorevoli. `CASE-WA-010` e `CASE-WA-013` mantengono obbligatoriamente accesso ristretto.

## Struttura

- `app/api`: endpoint HTTP.
- `app/core`: componenti di sicurezza e audit.
- `app/models`: modelli di dominio.
- `app/services`: servizi applicativi.
- `app/workflows`: orchestrazione dei workflow.
- `docs`: specifiche, architettura e strategia di test.
- `tests`: test unitari, di integrazione, scenario ed end-to-end.
