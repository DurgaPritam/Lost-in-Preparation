# Deploying to Vercel (free Hobby plan)

**Live:** https://lost-in-preparation.vercel.app (Vercel project `soujanya-chattis-projects/lost-in-preparation`, deployed 2026-11-08 from a local build).

## Redeploying (how it is deployed now)

The project is not connected to GitHub, so a push does not redeploy. To publish the current checkout, from `site/` with the Vercel CLI logged in to that account:

```bash
vercel build --prod             # runs npm run build locally (it reads ../site-data and ../contract, which an upload of site/ alone would lack)
vercel deploy --prebuilt --prod # uploads .vercel/output and points https://lost-in-preparation.vercel.app at it
```

To switch to automatic deploys on push instead, follow the one-time setup below (Root Directory `site`, files outside it included).

## About the build

It is a static export: Vercel runs the build and then serves `site/out/`. No server functions, environment variables or secrets are used.

## One-time setup (you)

1. Log in at **vercel.com** with **GitHub**, using the `DurgaPritam` account. The Hobby plan is free.
2. **Add New… → Project → Import** `DurgaPritam/Lost-in-Preparation`, then grant the Vercel GitHub app access to this private repository when asked.
3. In the import screen, set:
   - **Root Directory:** `site`
   - **Include files outside the Root Directory in the Build Step:** on (the default). The build reads `../site-data/` and `../contract/schemas/`.
   - **Framework, commands and output:** leave as they are. They come from [`vercel.json`](vercel.json): no framework preset, `npm ci`, `npm run build`, output `out`, trailing slashes, cache headers.
   - **Node.js version:** 20.x or later (Project Settings → General).
4. Click **Deploy**. Each later push to `main` redeploys, and each pull request gets a preview URL.

To use the CLI instead: run `npm i -g vercel`, then `vercel login`, then `cd site && vercel` (link the project with root `site`), then `vercel --prod`.

## What the build does

`npm run build` runs `prebuild` first:
1. It generates the TypeScript types and Zod schemas from `contract/schemas/`.
2. It validates every `site-data/` file and exits 1 on any mismatch, so a bad data file fails the deployment.
3. It writes `public/data/`.
4. It runs the preparation-engine parity gate (`npm run engine:parity`) and fails if the browser engine differs from any published Python estimate.

Then `next build` exports every page as static HTML (one per recipe, plus the screens and the redirect stubs for v1 addresses). The v1 addresses also get real 301 redirects from `vercel.json`.
