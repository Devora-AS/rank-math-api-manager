# TODO - Rank Math API Manager Plugin

## Nåværende Status

Versjon `1.0.9` er klargjort for release etter verifisert kompatibilitetsarbeid mot WordPress `6.9.3` og Rank Math SEO `1.0.265`.

Nylig fullført:

- Verifisert lokal runtime-kompatibilitet mot siste støttede WordPress- og Rank Math-versjoner.
- Forbedret autorisasjon og sanitering for REST-endepunkt og meta-felter.
- Strammet inn validering i updater og gjort flere PHP 8.x-sikkerhetstiltak.
- Oppdatert bruker- og utviklerdokumentasjon for `1.0.9`.

## Høy Prioritet

### 1. Legg til støtte for sider

- Legg til støtte for posttypen `page` i det tilpassede REST-endepunktet.
- Registrer Rank Math-meta for sider i native REST-responser.
- Verifiser tilgangskontroll, sanitering og idempotente oppdateringer for sider.
- Oppdater API-dokumentasjon og eksempler for innlegg, sider og produkter der det er relevant.

### 2. Legg til CI/CD-pipeline og GitHub Actions-workflows

- Legg til CI-workflow for pull requests og pushes til beskyttede brancher.
- Legg til release-workflow for pakking, validering og taggede releaser.
- Legg til [Plugin Check Action](https://github.com/WordPress/plugin-check-action) for å kjøre Plugin Check mot pluginen.
- Legg til PHP CodeSniffer (PHPCS).
- Legg til WPCS (WordPress Coding Standards).
- Legg til unit tester med PHPUnit.
- Legg til [WordPress Plugin Integration Test](https://github.com/marketplace/actions/wordpress-plugin-integration-test).
- Legg til kontroller for syntaks, virus/malware-skanning og kjente sårbarheter.

### 3. Styrk automatiske kvalitetsporter

- Legg til dekning i CI for minimum støttede PHP- og WordPress-versjoner.
- Legg til smoke-tester for REST-oppdateringer mot innlegg, sider og WooCommerce-produkter.
- La build feile ved kodestandardbrudd, fatale feil og pakkingsproblemer.
- Arkiver build-artefakter for release-verifisering.

## Medium Prioritet

### 4. Forbedre observabilitet og drift

- Legg til bedre styring av debug-logging for feilsøking.
- Legg til tydeligere admin-diagnostikk for avhengighets- og updater-feil.
- Dokumenter en repeterbar verifiseringsflyt for lokalt miljø og staging.

### 5. Utvid API-muligheter

- Vurder valgfri rate limiting på endepunkt-nivå.
- Vurder API-nøkkel- eller token-basert autentisering for headless-integrasjoner.
- Vurder audit logging for SEO-metadata-endringer.

### 6. Utvid kompatibilitetsdekning

- Test mot flere PHP-versjoner som pluginen støtter.
- Test mot flere WordPress minor-versjoner og vanlige hostingmiljøer.
- Verifiser oppførsel med flere kombinasjoner av Rank Math og WooCommerce.

## Lavere Prioritet

### 7. Forbedringer i admin-UX

- Legg til en dedikert admin-side for diagnostikk og konfigurasjon.
- Legg til statuspanel for release, updater og avhengigheter.

### 8. Internasjonalisering

- Viderefør og synkroniser norsk og engelsk dokumentasjon.
- Gå gjennom alle brukerrettede strenger for oversettbarhet.

## Dokumentasjonsoppfølging

- Hold `README.md`, `README-NORWEGIAN.md`, `readme.txt` og `docs/` synkronisert for hver release.
- Oppdater roadmap-punkter når funksjoner fullføres eller utsettes.
- Legg til CI/CD-dokumentasjon når workflows er på plass.

## Ressurser

- [WordPress Auto-Update Documentation](https://developer.wordpress.org/plugins/wordpress-org/plugin-developer-faq/#how-does-the-wordpress-org-plugin-update-system-work)
- [WordPress Plugin Update API](https://developer.wordpress.org/rest-api/reference/plugins/)
- [WordPress Coding Standards](https://developer.wordpress.org/coding-standards/)
- [Plugin Check Action](https://github.com/WordPress/plugin-check-action)
- [WordPress Plugin Integration Test](https://github.com/marketplace/actions/wordpress-plugin-integration-test)

---

**Sist oppdatert**: Mars 2026  
**Status**: Aktiv vedlikehold / release-klargjort
