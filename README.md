# JSONHammer

### Command line arguments:

- ``-c [num]``: Copies. Overrides value in settings.json.
- ``-o [url]``: Gateway URL. Overrides value in settings.json.
- ``-o [directory name]``: Output directory.
- ``-t [num]``: Max threads. Ie maximum upload tasks.
- ``-d``: Debug. Turns on more verbose logging.

### settings.json:

**Directives:**
- `PICK_FROM_ASSETS_WITHINDEX:[index],[dirname]`: Selects index from assets/filename. Filename must point to a directory containing several files. Index must start with an alphabetic character. Index will be randomly assigned, which you can then reuse to get consistency across multiple randomly generated files. For instance, if I have

- assets
  - spritesheets
    - Spritesheet0.png
    - Spritesheet1.png
    - Spritesheet2.png
  - displayimage
    - DisplayImage0.png
    - DisplayImage1.png
    - DisplayImage2.png

I could put in settings.json:
```json
{
  ...
  "template": {
   "displayImage": "PICK_FROM_ASSETS_WITHINDEX:displayimage,x",
   "spritesheet": "PICK_FROM_ASSETS_WITHINDEX:spritesheets,x"
  }
}
```

and that would make sure displayimage and spritesheets line up with each other **as long as the two directories are
one-to-one in alphabetical order** as exampled above.

- `RANDOM_FROM_ASSETS_JSON:[dir]`: Picks a random value from assets/[dir]. The file must contain an array of values.
- `IMG_FROM_ASSETS:[dir]`: Selects an image from assets/dir. There must be images in this directory. Will upload to IPFS or return the path to the image, depending on settings.
