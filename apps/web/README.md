# Web App

Analyst-facing PrioriTx frontend for browsing:

- benchmark health
- strict vs exploratory mode comparisons
- ranked target shortlists
- deterministic target explanations
- flat benchmark export previews

The UI uses materialized benchmark snapshots for the high-level dashboard and live API calls for shortlist and explanation detail, so first paint stays fast while the evidence-heavy views continue to load.

## Run locally

Start the API first:

```bash
PYTHONPATH=packages/py python3 apps/api/server.py
```

Then serve the web app:

```bash
cd apps/web
python3 -m http.server 4173
```

Open:

```text
http://127.0.0.1:4173
```
