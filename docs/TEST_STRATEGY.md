# Test Strategy

- **Unit test:** verificano funzioni, modelli e regole di safety in isolamento.
- **Integration test:** verificano la collaborazione tra API, configurazione, database e servizi.
- **Contract test:** verificano schemi, status code e compatibilità delle interfacce interne ed esterne.
- **Scenario test:** coprono casi operativi realistici, incluse incertezza, escalation e approvazione umana.
- **End-to-end test:** verificano il flusso completo in un ambiente rappresentativo senza invii reali ai clienti.
- **Regression test:** preservano il comportamento corretto dopo bug fix o cambiamenti funzionali.

La suite contiene il test dell'endpoint `GET /health` e, per il safety engine:

- test unitari positivi e negativi per ciascuna categoria di rischio;
- test della priorità dei segnali critici sui warning;
- test di audit, timestamp, ticket opzionale e anonimizzazione;
- test del servizio applicativo, incluso il divieto di invio automatico;
- scenari critici, ordinari e ambigui.

Le regole sono deterministiche e indipendenti da LLM. I test negativi non devono indebolire i requisiti critici: ogni nuova esclusione richiede un caso documentato e una verifica di regressione. Contract, integration ed end-to-end test restano da aggiungere quando esisteranno interfacce o persistenza corrispondenti.
