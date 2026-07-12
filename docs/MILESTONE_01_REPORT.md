# Milestone 01 Report

## Obiettivo della milestone

Creare la base verificabile di Blue Airco Support come copilota interno per i tecnici: servizio FastAPI minimale, endpoint `GET /health`, configurazione locale PostgreSQL, documentazione di sicurezza e pipeline CI. La milestone non comprende risposte automatiche ai clienti né integrazioni OpenAI o WhatsApp.

## File creati e modificati

La milestone comprende:

- configurazione di progetto: `pyproject.toml`, `.env.example`, `.gitignore` e `docker-compose.yml`;
- applicazione: package `app`, configurazione FastAPI ed endpoint health;
- test: struttura `tests` e test unitario dell'health check;
- documentazione: `AGENTS.md`, `README.md` e documenti in `docs`;
- automazione: `.github/workflows/ci.yml`.

Durante la revisione finale, `app/config.py` è stato allineato ai valori locali non segreti dichiarati in `.env.example` e `docker-compose.yml`. È stato inoltre aggiunto questo report.

## Architettura attuale

L'applicazione crea un'istanza FastAPI in `app/main.py` e registra il router definito in `app/api/health.py`. `app/config.py` carica la configurazione tramite `pydantic-settings`. I package `core`, `models`, `services` e `workflows` definiscono soltanto i confini dei moduli futuri.

Il flusso previsto resta:

```text
messaggio → safety engine → identificazione macchina → workflow
→ fonti approvate → bozza → approvazione umana
```

Questo flusso non è ancora implementato.

## Controlli implementati

- Endpoint `GET /health` con schema di risposta tipizzato.
- Configurazione applicativa caricabile da ambiente.
- PostgreSQL locale configurato con volume persistente e healthcheck.
- Valori di sviluppo espliciti e non destinati alla produzione.
- Regole vincolanti su sicurezza, audit, fonti, accuratezza e approvazione umana.
- Pipeline GitHub Actions su `push` e `pull_request`, con Python 3.12, installazione dell'extra `dev`, verifica dell'import e pytest dettagliato.

## Test presenti

È presente `tests/unit/test_health.py`, che usa `TestClient` per verificare:

- status code HTTP `200`;
- risposta JSON `{"status": "ok", "service": "blue-airco-support"}`.

Le dipendenze di sviluppo dichiarano pytest e httpx; FastAPI gestisce la versione compatibile di Starlette come dipendenza transitiva.

## Test non ancora eseguiti

I test locali non sono stati eseguiti. Anche l'esito della pipeline GitHub Actions non è noto finché la workflow non viene eseguita su GitHub. Non viene dichiarato alcun test superato.

## Limitazioni dell'ambiente

L'ambiente di lavoro corrente non dispone di Python, Docker o una shell Linux funzionante. Per istruzione, non sono stati effettuati ulteriori tentativi di installazione, esecuzione dei test o avvio di container.

## Rischi aperti

- La pipeline CI non è ancora stata validata da un'esecuzione reale su GitHub.
- Non esiste ancora un lock file delle dipendenze.
- PostgreSQL non è coperto da test di integrazione.
- I moduli safety e audit sono soltanto confini architetturali, senza implementazione.
- Non sono ancora presenti test contract, scenario, end-to-end o regression effettivi.
- I valori locali di database sono esempi non sicuri per un ambiente di produzione.

## Prossimi passi

- Verificare la prima esecuzione della workflow nella scheda Actions di GitHub.
- Aggiungere test di integrazione e scenario prima di introdurre nuovi workflow.
- Definire modelli di dominio, fonti approvate, safety engine e audit trail con requisiti tracciabili.
- Progettare esplicitamente il passaggio di approvazione umana prima di qualsiasi comunicazione esterna.

## Divieto di invio automatico WhatsApp

L'invio automatico di messaggi WhatsApp è vietato nella milestone attuale. Non è presente alcuna integrazione WhatsApp e nessuna bozza può essere inviata automaticamente a un cliente.
