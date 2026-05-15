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


def draw_key_value_table(pdf, x, y, width, rows, font_name, label_width=55 * mm):
    row_height = 7 * mm
    table_height = row_height * len(rows)
    pdf.setStrokeColor(colors.HexColor("#dfe4dc"))
    pdf.rect(x, y - table_height + 2 * mm, width, table_height, stroke=1, fill=0)
    pdf.setFont(font_name, 9)
    current_y = y - 3 * mm
    for label, value in rows:
        pdf.setFillColor(colors.HexColor("#596057"))
        pdf.drawString(x + 3 * mm, current_y, str(label))
        pdf.setFillColor(colors.black)
        pdf.drawString(x + label_width, current_y, str(value))
        current_y -= row_height
    return y - table_height - 4 * mm


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
