# PR log

---

## Add 3D block-diagram generator for GeoTIFF DEMs

- PR #43 — merged
- Author: @ggenelot
- Created: 2026-04-22
- Closed: 2026-04-22
- Merged: 2026-04-22
- Source branch: codex/implement-initial-block-diagram-prototype-k880s4
- Target branch: codex/implement-initial-block-diagram-prototype
- Milestone: none
- Labels: codex
- Diff summary: +124 / -40 across 1 file(s)
- Commits: 2
- URL: https://github.com/ggenelot/these/pull/43

### Description

### Motivation
- Provide a minimal, reproducible building block to generate oblique 3D block-diagrams from GeoTIFF DEMs including basic preprocessing and export. 
- Support realistic data handling such as NoData management, optional bounding-box cropping, and reprojection of geographic rasters to a local UTM CRS.
- Allow applying a georeferenced texture and vertical exaggeration to improve visualization quality.

### Description
- Implement a new module with core functions `load_dem` and `create_block_diagram` that read a DEM, compute pixel-center coordinates, and return elevation arrays with NoData converted to `nan`.
- Add reprojection logic in `_load_dem_core` to convert geographic CRS rasters to a suitable local UTM CRS via `_utm_crs_from_lonlat` and `rasterio.warp.reproject`.
- Implement optional texture reprojection with `_load_texture_on_dem_grid` to sample RGB texture onto the DEM grid and normalize it for `matplotlib` facecolors, controlled by `USE_TEXTURE` and `TEXTURE_PATH`.
- Create 3D rendering with `matplotlib` in `create_block_diagram`, including vertical exaggeration, base plane and vertical faces to form a closed block, optional texture usage, camera control via `azimuth`/`elevation`, and image export via `Figure.savefig`.

### Testing
- No automated tests were added for this change.

------
[Codex Task](https://chatgpt.com/codex/cloud/tasks/task_e_69e8bacc81dc832a912d14fa40f512d2)

---

## Add DEM-based 3D block-diagram generator (load_dem, create_block_diagram)

- PR #42 — merged
- Author: @ggenelot
- Created: 2026-04-22
- Closed: 2026-04-22
- Merged: 2026-04-22
- Source branch: codex/implement-initial-block-diagram-prototype-3f4gmo
- Target branch: codex/implement-initial-block-diagram-prototype
- Milestone: none
- Labels: codex
- Diff summary: +51 / -0 across 1 file(s)
- Commits: 2
- URL: https://github.com/ggenelot/these/pull/42

### Description

### Motivation
- Fournir une brique minimale et reproductible pour générer un bloc-diagramme 3D à partir d'un MNT GeoTIFF en automatisant le chargement, le recadrage et l'export image.
- Gérer les cas courants des MNT géographiques (degrés) en reprojetant vers un CRS UTM local et en normalisant les NoData pour un rendu homogène.

### Description
- Ajout du module complet avec les fonctions `load_dem` pour charger et recadrer un MNT, convertir les masques NoData en `nan` et reprojeter automatiquement les rasters géographiques vers un CRS UTM local si nécessaire.
- Implémentation de `create_block_diagram` qui construit une vue oblique 3D via `matplotlib` en appliquant une `vertical_exaggeration`, en fermant le volume par une base et des faces latérales et en exportant la figure vers un fichier image.
- Validation d'entrée ajoutée pour `vertical_exaggeration` et découpage optionnel par `bounds`, avec calcul des centres de pixels et limitation du maillage (`rcount`/`ccount`) pour le rendu.
- Exposition publique des fonctions via `__all__` et documentation des paramètres et retours dans les docstrings.

### Testing
- Aucun test automatisé n'a été ajouté ni exécuté dans cette modification.

------
[Codex Task](https://chatgpt.com/codex/cloud/tasks/task_e_69e8bacc81dc832a912d14fa40f512d2)

---

## Changed the folder structure

- PR #24 — merged
- Author: @ggenelot
- Created: 2026-02-06
- Closed: 2026-02-06
- Merged: 2026-02-06
- Base branch: main
- URL: https://github.com/ggenelot/these/pull/24

### Description

_No description provided._

---

## Fixing the downloading problem

- PR #23 — merged
- Author: @ggenelot
- Created: 2026-02-06
- Closed: 2026-02-06
- Merged: 2026-02-06
- Base branch: main
- URL: https://github.com/ggenelot/these/pull/23

### Description

_No description provided._

---

## Added affiliation data

- PR #21 — merged
- Author: @ggenelot
- Created: 2026-02-06
- Closed: 2026-02-06
- Merged: 2026-02-06
- Base branch: main
- URL: https://github.com/ggenelot/these/pull/21

### Description

_No description provided._

---

## Allowing page pdf download

- PR #22 — merged
- Author: @ggenelot
- Created: 2026-02-06
- Closed: 2026-02-06
- Merged: 2026-02-06
- Base branch: edition/metadata
- URL: https://github.com/ggenelot/these/pull/22

### Description

_No description provided._

---

## Change the structure of the thesis

- PR #19 — merged
- Author: @ggenelot
- Created: 2026-02-05
- Closed: 2026-02-05
- Merged: 2026-02-05
- Base branch: main
- URL: https://github.com/ggenelot/these/pull/19

### Description

_No description provided._

---

## Changed index to markdown format

- PR #18 — closed
- Author: @ggenelot
- Created: 2026-02-05
- Closed: 2026-02-05
- Base branch: main
- URL: https://github.com/ggenelot/these/pull/18

### Description

_No description provided._

---

## Enable hover preview for links

- PR #16 — closed
- Author: @ggenelot
- Created: 2026-02-04
- Closed: 2026-02-05
- Base branch: main
- URL: https://github.com/ggenelot/these/pull/16

### Description

_No description provided._

---

## Migration to jupyter book 2 framework

- PR #17 — merged
- Author: @ggenelot
- Created: 2026-02-04
- Closed: 2026-02-05
- Merged: 2026-02-05
- Base branch: main
- URL: https://github.com/ggenelot/these/pull/17

### Description

_No description provided._

---

## Created a file for ComMod in the context part

- PR #13 — merged
- Author: @ggenelot
- Created: 2026-01-20
- Closed: 2026-02-03
- Merged: 2026-02-03
- Base branch: main
- URL: https://github.com/ggenelot/these/pull/13

### Description

Create a working file explaining how the ComMod approach is relevant to prospective modelling

---

## Rédaction d'un projet de terrain

- PR #12 — merged
- Author: @ggenelot
- Created: 2026-01-19
- Closed: 2026-02-03
- Merged: 2026-02-03
- Base branch: main
- URL: https://github.com/ggenelot/these/pull/12

### Description

Rédaction d'un document pour cadrer le terrain, ses objectifs et ses méthodes. 

---

## Fixing list of figures issues

- PR #10 — merged
- Author: @ggenelot
- Created: 2025-12-12
- Closed: 2026-02-03
- Merged: 2026-02-03
- Base branch: main
- URL: https://github.com/ggenelot/these/pull/10

### Description

_No description provided._

---

## First draft of a socio-ecosystem representation

- PR #14 — merged
- Author: @ggenelot
- Created: 2026-01-20
- Closed: 2026-02-03
- Merged: 2026-02-03
- Base branch: main
- URL: https://github.com/ggenelot/these/pull/14

### Description

_No description provided._

---

## Add reference to about documents : readme, license, contributing

- PR #15 — merged
- Author: @ggenelot
- Created: 2026-02-02
- Closed: 2026-02-02
- Merged: 2026-02-02
- Base branch: main
- URL: https://github.com/ggenelot/these/pull/15

### Description

_No description provided._

---

## Exploration

- PR #11 — merged
- Author: @ggenelot
- Created: 2026-01-19
- Closed: 2026-01-19
- Merged: 2026-01-19
- Base branch: main
- URL: https://github.com/ggenelot/these/pull/11

### Description

Fixed some bugs related to changes in the file structure + added a citation file. 

---

## Redaction/notebooks

- PR #9 — merged
- Author: @ggenelot
- Created: 2025-12-12
- Closed: 2025-12-12
- Merged: 2025-12-12
- Base branch: main
- URL: https://github.com/ggenelot/these/pull/9

### Description

_No description provided._

---

## Redaction/notebooks

- PR #7 — merged
- Author: @ggenelot
- Created: 2025-12-11
- Closed: 2025-12-12
- Merged: 2025-12-12
- Base branch: main
- URL: https://github.com/ggenelot/these/pull/7

### Description

Moved notebooks to the method zone

---

## Include proper bibliography linked to zotero

- PR #8 — merged
- Author: @ggenelot
- Created: 2025-12-12
- Closed: 2025-12-12
- Merged: 2025-12-12
- Base branch: main
- URL: https://github.com/ggenelot/these/pull/8

### Description

_No description provided._

---

## Adding CI tools

- PR #6 — merged
- Author: @ggenelot
- Created: 2025-12-11
- Closed: 2025-12-11
- Merged: 2025-12-11
- Base branch: main
- URL: https://github.com/ggenelot/these/pull/6

### Description

_No description provided._

---

## Feature/api

- PR #5 — merged
- Author: @ggenelot
- Created: 2025-12-11
- Closed: 2025-12-11
- Merged: 2025-12-11
- Base branch: main
- URL: https://github.com/ggenelot/these/pull/5

### Description

Changed source for utils

---

## Minor changes in the path

- PR #4 — closed
- Author: @ggenelot
- Created: 2025-12-11
- Closed: 2025-12-11
- Base branch: main
- URL: https://github.com/ggenelot/these/pull/4

### Description

New pull request to check that it works with RTD PR versions.

---

## Minor changes in the path

- PR #3 — closed
- Author: @ggenelot
- Created: 2025-12-11
- Closed: 2025-12-11
- Base branch: main
- URL: https://github.com/ggenelot/these/pull/3

### Description

_No description provided._

---

## Changed a typo in importing autodoc

- PR #2 — merged
- Author: @ggenelot
- Created: 2025-12-11
- Closed: 2025-12-11
- Merged: 2025-12-11
- Base branch: main
- URL: https://github.com/ggenelot/these/pull/2

### Description

Changed a typo

---

## Redaction/api

- PR #1 — merged
- Author: @ggenelot
- Created: 2025-12-11
- Closed: 2025-12-11
- Merged: 2025-12-11
- Base branch: main
- URL: https://github.com/ggenelot/these/pull/1

### Description

Added API pages in the documentation. Not quite sure it is going to work but we'll see. 

