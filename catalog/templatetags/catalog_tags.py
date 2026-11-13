from django import template

register = template.Library()


@register.filter
def available(stock):
    try:
        return stock.available
    except (AttributeError, TypeError):
        return 0
