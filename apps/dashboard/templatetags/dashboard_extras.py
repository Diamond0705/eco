from django import template

register = template.Library()


@register.filter
def trips_count(value):
    try:
        count = abs(int(value))
        original = int(value)
    except (TypeError, ValueError):
        return value

    if count % 100 in range(11, 15):
        word = "рейсов"
    elif count % 10 == 1:
        word = "рейс"
    elif count % 10 in range(2, 5):
        word = "рейса"
    else:
        word = "рейсов"
    return f"{original} {word}"
