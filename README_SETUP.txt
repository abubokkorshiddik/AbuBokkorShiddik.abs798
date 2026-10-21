# ResearchRadar AI backend setup

This bundle is designed for the existing public portfolio repository:
`abubokkorshiddik/AbuBokkorShiddik.abs798`

## Expected repository structure

Keep the existing portfolio files. Add these files/folders:

- `ResearchRadarAI/index.html` — the ResearchRadar dashboard HTML
- `ResearchRadarAI/backend/researchradar.py` — scheduled collector
- `ResearchRadarAI/data/articles.json` — generated paper dataset
- `ResearchRadarAI/data/reports.json` — generated reports manifest
- `.github/workflows/researchradar-daily.yml` — scheduled workflow at repository root

The HTML file needs to be inside `ResearchRadarAI/` and named `index.html` for this URL:
`https://abubokkorshiddik.github.io/AbuBokkorShiddik.abs798/ResearchRadarAI/`

The existing root file `ResearchRadarAI.html` can stay in place.

## Workflow
- Collects scholarly metadata from OpenAlex and Europe PMC for five broad research searches.
- Deduplicates by DOI/title.
- Writes `ResearchRadarAI/data/articles.json` and `ResearchRadarAI/data/reports.json`.
- If `OPENAI_API_KEY` is configured in repository Actions secrets, requests an AI-assisted synthesis.
- If no key is configured, still creates a metadata-only report.
- Runs daily at 08:00 Bangladesh time and can be run manually from Actions.

## Add the API secret
GitHub repository → Settings → Secrets and variables → Actions → New repository secret.
Name: `OPENAI_API_KEY`
Value: your newly created OpenAI API key. Never paste it in a public file or chat.

If you already shared an API key in a chat, revoke that key and create a new one before use.

## Allow Actions to commit generated data
GitHub repository → Settings → Actions → General → Workflow permissions → select
"Read and write permissions" → Save.

The workflow uses `contents: write` too, but repository Actions settings may still restrict it.

## Important
The workflow writes JSON into the repository and commits changes so GitHub Pages can serve the data. The website should load the data from `./data/articles.json` and `./data/reports.json` once `index.html` is in the `ResearchRadarAI` folder.
