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
language-default: es     # preferred language for downloads
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
```

Run the downloader to populate `resources/deck/` with the required images:

```bash
python fetch_images.py
```

Images of cards with a different back will be stored in matching `F##` and `B##` files.

## Generating the PDFs

Once the images are in place, run:

```bash
python generate_pdf.py
```

PDF files will be created inside the `results/` directory with a name based on
the current date and time, for example `deck_20230101_120000_fronts.pdf` and
`deck_20230101_120000_backs.pdf`. Print them using the "flip on long edge"
duplex option so that fronts and backs align.
