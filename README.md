# Magic Deck Printer

This project creates printable PDFs for Magic cards. It can download card images using the Scryfall API and then generate PDF files ready for duplex printing.

Images and other assets live under the `resources/` directory. Card images are stored in `resources/deck/` and the default card back is `resources/back.jpg`. Generated PDFs are written to the `results/` directory with timestamped names.

## Requirements

- Python 3.7+
- [Pillow](https://pypi.org/project/Pillow/)
- [ReportLab](https://pypi.org/project/reportlab/)
- [PyYAML](https://pypi.org/project/PyYAML/)
- [requests](https://pypi.org/project/requests/)

Install them with:

```bash
pip install Pillow reportlab PyYAML requests
```

## Configuration

Edit `config.yml` to change layout options.

```
PAGE_SIZE: A4            # or LETTER
DPI: 300                 # used for conversions
MARGIN_MM: 5             # margin on all sides
GAP_MM: 2                # space between cards
DEFAULT_BACK: resources/back.jpg   # default back image
blank-back: false       # when true, use a white back instead of DEFAULT_BACK
language-default: es     # preferred language for downloads
pages-intercalation: true # interleave front and back pages in one PDF
horizontal-back-offset: -2 # horizontal shift in mm for backs (negative = left)
vertical-back-offset: 0  # vertical shift in mm for backs (positive = up)
back-oversize: 0.2        # enlarge back images by this many mm in both width and height
page-rotation-degrees: 0  # rotation in degrees. Negative values are transformed
                           # using ``360 - value`` so the argument passed to
                           # ReportLab is always positive
guided-lines: true        # draw thin grey cutting guides on fronts
cross-calibrator: false   # draw small calibration crosses on every corner
```

Cards are printed at the official size of 63.5mm × 88.9mm (2.5" × 3.5").
The script calculates the number of rows and columns automatically to fit as
many cards as possible on each page according to the configured margins and
gaps.

## Preparing card images

Create a `card-list.txt` file listing the cards to download:

```
2 Swamp
3 Island
1 Beast [tfdn]
```

Use square brackets to specify the set code for tokens. This allows
distinguishing tokens with the same name from different sets.

Run the downloader to populate `resources/deck/` with the required images:

```bash
python3 fetch_images.py
```

Images of cards with a different back will be stored in matching `F##` and `B##` files.

## Generating the PDFs

Once the images are in place, run:

```bash
python3 generate_pdf.py
```

PDF files will be created inside the `results/` directory with a name based on
the current date and time. If `pages-intercalation` is enabled (the default) a
single file like `deck_20230101_120000.pdf` will contain alternating front and
back pages. Otherwise two files, `deck_20230101_120000_fronts.pdf` and
`deck_20230101_120000_backs.pdf`, will be produced. The back pages are mirrored
horizontally so that fronts and backs line up when cutting. Use the
`horizontal-back-offset` setting to tweak their horizontal position if your
printer is misaligned. Likewise, adjust `vertical-back-offset` for vertical
alignment issues. Print using the "flip on long edge" duplex option to
ensure proper alignment.

To generate a page containing only calibration crosses use:

```bash
python3 generate_calibration_page.py
```
