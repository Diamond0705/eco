from django import template

register = template.Library()


@register.filter
def file_size_label(size_bytes):
    if size_bytes is None:
        return "0 байт"

    size_bytes = int(size_bytes)
    if size_bytes >= 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} МБ"
    if size_bytes >= 1024:
        return f"{round(size_bytes / 1024)} КБ"
    return f"{size_bytes} байт"
