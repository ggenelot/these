# Template `these-chapitre`

Ce dépôt contient deux emplacements du template pour couvrir les résolutions de chemins usuelles MyST :

- `docs/templates/these-chapitre` (recommandé si `myst.yml` est dans `docs/`)
- `templates/these-chapitre` (racine du dépôt)

Si votre `myst.yml` est dans `docs/`, utilisez `template: ./templates/these-chapitre`.

Exemple minimal de frontmatter MyST attendu :

```yaml
---
title: "Chapitre 2 — ..."
keywords:
  - mot-clé 1
  - mot-clé 2
parts:
  abstract: |
    ...
  problematic: |
    ...
  literature_note: |
    ...
  partial_conclusion: |
    ...
exports:
  - format: pdf
    template: ./templates/these-chapitre
    output: exports/chapitre-2.pdf
---
```
