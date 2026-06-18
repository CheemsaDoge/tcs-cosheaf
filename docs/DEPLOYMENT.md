# Static Website Deployment

The website is a read-only Astro static site over sanitized demo export data.
It does not require hosting secrets for local builds or public preview builds,
and it must not fetch private repositories, call providers, or handle GitHub
tokens in the browser.

## Build Locally

```bash
cd website
npm ci
npm test
npm run build
```

The static output directory is:

```text
website/dist
```

The build consumes the committed demo fixture under:

```text
website/src/fixtures/site-data/
```

## Demo Data

The committed fixture is demo-only website data. To refresh it from a safe demo
workspace, run the export command against that demo workspace and review the
diff before committing:

```bash
cosheaf site export --demo --out website/src/fixtures/site-data
```

Before publishing a public preview, confirm the fixture remains demo/public
safe:

- no API keys, tokens, provider prompts, or hidden reviewer identity;
- no private research data unless explicitly marked demo-only;
- no accepted status created by the website;
- gate, verifier, AI, issue, PR, and report output remain display context only;
- skipped, unavailable, or not-run checks are not described as pass.

## GitHub CI Check

The `Website build` workflow runs on website/deployment changes and executes:

```bash
cd website
npm ci
npm test
npm run build
```

It uploads `website/dist` as a CI artifact named `website-dist`. The workflow
does not deploy the site and does not require secrets.

## Cloudflare Pages

Use these settings for a manual Cloudflare Pages project:

```text
Framework preset: Astro
Root directory: /
Build command: cd website && npm ci && npm run build
Build output directory: website/dist
Environment variables: none required for the public demo build
```

Keep production deployment credentials in the hosting provider, not in this
repository. If a future deployment needs a custom domain, access token, or Pages
project ID, configure it in Cloudflare or GitHub environment secrets and keep
the repository build path read-only.

## Equivalent Static Hosts

Any static host that can run the local build command and publish `website/dist`
is sufficient. The first deployable release is a public read-only preview; it is
not a production SaaS service and does not add authenticated actions.
