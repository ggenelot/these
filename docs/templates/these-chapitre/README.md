# these-chapitre (dérivé de `lapreprint`)

Template local volontairement **très proche** de `lapreprint`.

Objectif : n'ajouter que l'affichage conditionnel de :
- `parts.abstract` (déjà natif lapreprint)
- `parts.problematic`
- `parts.literature_note`
- `doc.keywords`
- `parts.partial_conclusion`

Exemple d'export (projet avec `myst.yml` dans `docs/`) :

```yaml
exports:
  - format: pdf
    template: ./templates/these-chapitre
    output: exports/chapitre.pdf
```
