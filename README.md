# JSONHammer

### Command line arguments:

``-c [num]``: Copies. Overrides value in settings.json.
``-o [url]``: Gateway URL. Overrides value in settings.json.

``-o [directory name]``: Output directory.
``-t [num]``: Max threads. Ie maximum upload tasks.
``-d``: Debug. Turns on more verbose printing.

### settings.json:

**Directives:**
- `SELECT_FROM_ARRAY_JSON:[index],[filename]`: Selects index from assets/filename. Must point to a JSON file containing an array of values. Index must start with an alphabetic character. Index will be randomly assigned, which you can then reuse to get consistency across multiple randomly generated files.
- `RANDOM_FROM_ASSETS_JSON:[dir]`: Picks a random value from assets/[dir]. The file must contain an array of values.
- `IMG_FROM_ASSETS:[dir]`: Selects an image from assets/dir. There must be images in this directory. Will upload to IPFS or return the path to the image, depending on settings.
