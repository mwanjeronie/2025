# 🍌 Bananas — A Simple Site

A small, self-contained static website all about bananas: quick facts, nutrition
stats, an interactive ripeness guide, and random trivia.

## Files

- `index.html` — page structure and content
- `styles.css` — styling (responsive, no dependencies)
- `script.js` — small interactive bits (ripeness guide + random trivia)
- `vercel.json` — static-deploy config (clean URLs)

## Running it

No build step or dependencies required. Just open `index.html` in a browser,
or serve the folder locally:

```bash
cd banana-site
python3 -m http.server 8000
# then visit http://localhost:8000
```

## Deploying to Vercel

This is a zero-config static site. From the `banana-site` folder:

```bash
npx vercel deploy --prod --yes
```

The first run will prompt you to log in (or use `--token=$VERCEL_TOKEN` for a
non-interactive deploy in CI / automation).
