from reportlab.lib import colors
from reportlab.lib.units import mm

LEFT = 15 * mm
RIGHT = 15 * mm
TOP = 14 * mm
BOTTOM = 14 * mm
LINE_HEIGHT = 6 * mm


def draw_header(pdf, width, height, font_name, title):
    pdf.setFillColor(colors.HexColor("#1f5f43"))
    pdf.setFont(font_name, 15)
    pdf.drawString(LEFT, height - TOP, "EcoLogist")
    pdf.setFillColor(colors.black)
    pdf.setFont(font_name, 12)
    pdf.drawRightString(width - RIGHT, height - TOP, title)
    pdf.setStrokeColor(colors.HexColor("#dfe4dc"))
    pdf.line(LEFT, height - TOP - 4 * mm, width - RIGHT, height - TOP - 4 * mm)
    return height - TOP - 12 * mm


def draw_footer(pdf, width, font_name):
    pdf.setStrokeColor(colors.HexColor("#dfe4dc"))
    pdf.line(LEFT, BOTTOM + 5 * mm, width - RIGHT, BOTTOM + 5 * mm)
    pdf.setFillColor(colors.HexColor("#596057"))
    pdf.setFont(font_name, 8)
    pdf.drawString(LEFT, BOTTOM, "Сформировано системой EcoLogist")
    pdf.setFillColor(colors.black)


def ensure_space(pdf, y, width, height, font_name, title, required_height):
    if y - required_height >= BOTTOM + 8 * mm:
        return y
    draw_footer(pdf, width, font_name)
    pdf.showPage()
    return draw_header(pdf, width, height, font_name, title)


def draw_title(pdf, text, x, y, font_name):
    pdf.setFont(font_name, 18)
    pdf.setFillColor(colors.black)
    pdf.drawString(x, y, text)
    return y - 10 * mm


def draw_section_title(pdf, text, x, y, font_name):
    pdf.setFillColor(colors.HexColor("#1f5f43"))
    pdf.setFont(font_name, 12)
    pdf.drawString(x, y, text)
    pdf.setFillColor(colors.black)
    return y - 7 * mm


def key_value_table_height(pdf, width, rows, font_name, label_width=55 * mm, font_size=9):
    row_height = 7 * mm
    value_width = width - label_width - 3 * mm
    return sum(
        max(
            row_height,
            len(_wrap_text(pdf, str(value), font_name, font_size, value_width)) * 5 * mm,
        )
        for _label, value in rows
    )


def draw_key_value_table(pdf, x, y, width, rows, font_name, label_width=55 * mm):
    row_height = 7 * mm
    font_size = 9
    line_height = 5 * mm
    value_width = width - label_width - 3 * mm
    prepared_rows = [
        (
            str(label),
            _wrap_text(pdf, str(value), font_name, font_size, value_width),
        )
        for label, value in rows
    ]
    row_heights = [
        max(row_height, len(value_lines) * line_height) for _label, value_lines in prepared_rows
    ]
    table_height = sum(row_heights)
    pdf.setStrokeColor(colors.HexColor("#dfe4dc"))
    pdf.rect(x, y - table_height + 2 * mm, width, table_height, stroke=1, fill=0)
    pdf.setFont(font_name, font_size)
    current_y = y - 3 * mm
    for (label, value_lines), current_row_height in zip(prepared_rows, row_heights, strict=True):
        pdf.setFillColor(colors.HexColor("#596057"))
        pdf.drawString(x + 3 * mm, current_y, label)
        pdf.setFillColor(colors.black)
        for line_index, line in enumerate(value_lines):
            pdf.drawString(x + label_width, current_y - line_index * line_height, line)
        current_y -= current_row_height
    return y - table_height - 4 * mm


def _wrap_text(pdf, text, font_name, font_size, max_width):
    if pdf.stringWidth(text, font_name, font_size) <= max_width:
        return [text]

    lines = []
    current_line = ""
    for word in text.split():
        candidate = f"{current_line} {word}".strip()
        if pdf.stringWidth(candidate, font_name, font_size) <= max_width:
            current_line = candidate
            continue
        if current_line:
            lines.append(current_line)
        current_line = _append_wrapped_word(pdf, lines, word, font_name, font_size, max_width)
    if current_line:
        lines.append(current_line)
    return lines or [text]


def _append_wrapped_word(pdf, lines, word, font_name, font_size, max_width):
    if pdf.stringWidth(word, font_name, font_size) <= max_width:
        return word

    current_part = ""
    for character in word:
        candidate = f"{current_part}{character}"
        if pdf.stringWidth(candidate, font_name, font_size) <= max_width:
            current_part = candidate
            continue
        if current_part:
            lines.append(current_part)
        current_part = character
    return current_part


def draw_simple_table(pdf, x, y, widths, headers, rows, font_name, row_height=7 * mm):
    pdf.setFont(font_name, 8)
    current_y = y
    pdf.setFillColor(colors.HexColor("#eef8f1"))
    pdf.rect(x, current_y - row_height + 2 * mm, sum(widths), row_height, stroke=0, fill=1)
    pdf.setFillColor(colors.black)

    current_x = x
    for header, width in zip(headers, widths, strict=True):
        pdf.drawString(current_x + 2 * mm, current_y - 3 * mm, str(header))
        current_x += width
    current_y -= row_height

    for row in rows:
        current_x = x
        for value, width in zip(row, widths, strict=True):
            pdf.drawString(current_x + 2 * mm, current_y - 3 * mm, str(value))
            current_x += width
        pdf.setStrokeColor(colors.HexColor("#dfe4dc"))
        pdf.line(
            x,
            current_y - row_height + 2 * mm,
            x + sum(widths),
            current_y - row_height + 2 * mm,
        )
        current_y -= row_height
    return current_y - 2 * mm
