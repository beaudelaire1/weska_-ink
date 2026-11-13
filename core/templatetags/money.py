from django import template

register = template.Library()


@register.filter
def money(value):
    try:
        amount = int(value or 0)
    except (TypeError, ValueError):
        return "—"
    euros, cents = divmod(amount, 100)
    formatted = f"{euros:,}".replace(",", " ")
    return f"{formatted},{cents:02d} €"
