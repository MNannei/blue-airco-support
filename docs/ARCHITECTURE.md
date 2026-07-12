# Architecture

## Moduli

- `api`: interfaccia HTTP FastAPI.
- `config`: configurazione caricata dall'ambiente tramite `pydantic-settings`.
- `core.safety`: confine delle future regole di sicurezza e validazione.
- `core.audit`: confine della futura tracciabilità di decisioni, fonti e approvazioni.
- `models`: modelli del dominio.
- `services`: servizi applicativi e accesso alle fonti approvate.
- `workflows`: orchestrazione esplicita dei passaggi operativi.

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

La bozza non viene inviata automaticamente. In questa fase il flusso è soltanto documentato: non sono presenti integrazioni OpenAI, WhatsApp o automazioni rivolte ai clienti.

