from django import template

from menu.models import MenuItem
from menu.utils import TreeStore

register = template.Library()


@register.inclusion_tag('menu/menu.html', takes_context=True)
def draw_menu(context, name: str):
    items = MenuItem.objects.select_related('parent').filter(menu__name=name).order_by('parent')
    tree = TreeStore(items)
    context['menu_name'] = name
    context['menu'] = tree

    opened_items = []
    active_items = context.get('active_items', [])
    for id_ in active_items:
        opened_items.extend(map(lambda item: item.pk, tree.get_parent_items(id_)))
    context['opened_items'] = opened_items

    return context


@register.inclusion_tag('menu/menu_item.html', takes_context=True)
def draw_menu_item(context, item: TreeStore.Node):
    context['menu_item'] = item
    return context
