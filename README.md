# Magic Deck Printer

This project creates printable PDFs for Magic cards stored as images. The
script reads all images inside `deck-to-print/` and generates two files:
`fronts.pdf` and `backs.pdf`. They have the same layout so they can be
printed in duplex mode.

## Requirements

- Python 3.7+
- [Pillow](https://pypi.org/project/Pillow/)
- [ReportLab](https://pypi.org/project/reportlab/)
- [PyYAML](https://pypi.org/project/PyYAML/)

Install them with:

```bash
pip install Pillow reportlab PyYAML
```

## Configuration

Edit `config.yml` to change layout options.

```
PAGE_SIZE: A4            # or LETTER
DPI: 300                 # used for conversions
CARDS_PER_PAGE: 10       # must match GRID columns × rows
GRID: [2, 5]             # [columns, rows]
MARGIN_MM: 5             # margin on all sides
GAP_MM: 2                # space between cards
DEFAULT_BACK: back.jpg   # default back image in project root
```

Place your card images in `deck-to-print/` with names like:

```
4 Swamp.jpg       # print this image 4 times
F01 Card Front.jpg
B01 Card Back.jpg
```

`F` indicates the front of a two-sided card and `B` the matching back with
the same numeric identifier. Cards without a specific back will use the
`DEFAULT_BACK` image.

## Usage

Run the generator from the project root:

```bash
python generate_pdf.py
```

The resulting `fronts.pdf` and `backs.pdf` can be printed using the
"flip on long edge" duplex option so that fronts and backs align.
