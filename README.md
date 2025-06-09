# Magic Deck Printer

This project creates printable PDFs for Magic cards. It can download card images using the Scryfall API and then generate PDF files ready for duplex printing.

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
CARDS_PER_PAGE: 10       # must match GRID columns × rows
GRID: [2, 5]             # [columns, rows]
MARGIN_MM: 5             # margin on all sides
GAP_MM: 2                # space between cards
DEFAULT_BACK: back.jpg   # default back image in project root
language-default: es     # preferred language for downloads
```

## Preparing card images

Create a `card-list.txt` file listing the cards to download:

```
2 Swamp
3 Island
```

Run the downloader to populate `deck-to-print/` with the required images:

```bash
python fetch_images.py
```

Images of cards with a different back will be stored in matching `F##` and `B##` files.

## Generating the PDFs

Once the images are in place, run:

```bash
python generate_pdf.py
```

The resulting `fronts.pdf` and `backs.pdf` can be printed using the
"flip on long edge" duplex option so that fronts and backs align.
