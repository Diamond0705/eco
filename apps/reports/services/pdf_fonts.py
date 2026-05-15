from pathlib import Path

from django.conf import settings
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

PDF_FONT_NAME = "EcoLogistSans"
FALLBACK_FONT_NAME = "Helvetica"


def register_pdf_font():
    if PDF_FONT_NAME in pdfmetrics.getRegisteredFontNames():
        return PDF_FONT_NAME

    font_path = _find_font_path()
    if font_path is None:
        # Built-in ReportLab fonts do not fully support Cyrillic; this fallback keeps PDF
        # generation available on minimal systems until REPORTLAB_FONT_PATH is configured.
        return FALLBACK_FONT_NAME

    pdfmetrics.registerFont(TTFont(PDF_FONT_NAME, str(font_path)))
    return PDF_FONT_NAME


def _find_font_path():
    candidates = []
    configured_path = getattr(settings, "REPORTLAB_FONT_PATH", "")
    if configured_path:
        candidates.append(Path(configured_path))

    candidates.extend(
        [
            Path("C:/Windows/Fonts/arial.ttf"),
            Path("C:/Windows/Fonts/Arial.ttf"),
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
            Path("/Library/Fonts/Arial.ttf"),
            Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
        ]
    )

    for path in candidates:
        if path.exists():
            return path
    return None
