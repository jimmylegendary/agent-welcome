# Playwright public-page JSON/CSV example

This small Node example reads one public HTTPS page and writes bounded headings and same-origin links to `output/public-page.json` and `output/public-page.csv`.

## Install and run

```sh
npm install
npx playwright install chromium
npm run crawl -- https://example.com
```

It uses a fresh unauthenticated browser context, rejects URL credentials, IP-literal/local hosts, and non-HTTPS URLs, blocks cross-origin requests, and does not follow links to other pages. It never loads a signed-in browser profile. Do not pass private, tokenized, or authenticated URLs. For untrusted inputs, run it in a network sandbox; a DNS name can still resolve to a private address.

The example does not bypass access controls or promise completeness. Check a site's terms and robots guidance and prefer its public API before collecting at scale. Playwright is installed as a project dependency; this does not install a browser binary, so run the documented browser install command once.
