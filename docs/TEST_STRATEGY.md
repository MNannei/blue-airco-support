# Test Strategy

- **Unit test:** verificano funzioni, modelli e regole di safety in isolamento.
- **Integration test:** verificano la collaborazione tra API, configurazione, database e servizi.
- **Contract test:** verificano schemi, status code e compatibilità delle interfacce interne ed esterne.
- **Scenario test:** coprono casi operativi realistici, incluse incertezza, escalation e approvazione umana.
- **End-to-end test:** verificano il flusso completo in un ambiente rappresentativo senza invii reali ai clienti.
- **Regression test:** preservano il comportamento corretto dopo bug fix o cambiamenti funzionali.

La suite iniziale contiene un test dell'endpoint `GET /health`. Ogni nuova funzionalità deve aggiornare i livelli pertinenti e la matrice di tracciabilità.

