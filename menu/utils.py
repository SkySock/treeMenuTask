from itertools import chain
from django.forms import ChoiceField
from menu.models import MenuItem


class TreeStore:
    class Node:
        def __init__(self, menu_item: MenuItem | None):
            if not menu_item:
                self._id = 0
            else:
                self._id: int = menu_item.pk
            self.parent = None
            self.children: list["TreeStore.Node"] = []
            self.item = menu_item

        @property
        def id(self) -> int:
            return self._id

        @property
        def has_children(self) -> bool:
            return bool(self.children)

        def is_descendant(self, other: "TreeStore.Node") -> bool:
            """
            Проверка является ли узел потомком узла
            """
            if self is other:
                return False
            current = self
            while current.parent:
                current = current.parent
                if current is other:
                    return True

            return False

        def add_child(self, child: "TreeStore.Node") -> None:
            """
            Добавляет новый дочерний узел к текущему.
            :param child: TreeStore.Node
            :return: None
            """
            child.parent = self
            self.children.append(child)

        def get_flattened(self):
            flat_structure = [self.item] if self.item else []
            for child in self.children:
                flat_structure = chain(flat_structure, child.get_flattened())
            return flat_structure

        def get_parent_items(self):
            """
            Возвращает цепочку от текущего элемента до первого предка
            """
            if self.item is None:
                return []
            current = self
            items = []
            while current.parent or current.item:
                items.append(current.item)
                current = current.parent

            return items

    def __init__(self, items: list[MenuItem]):

        self._tree = {}
        self._head = self.Node(None)
        self._tree[self._head.id] = self._head

        for item in items:
            if item.parent:
                parent = self._get_node(item.parent.pk)
            else:
                parent = self._head
            child = self.Node(item)
            parent.add_child(child)
            self._tree[child.id] = child

    def _get_node(self, id_: int) -> Node | None:
        return self._tree.get(id_)

    @property
    def head(self):
        return self._head

    def get_parent_items(self, id_: str | int):
        """
        Возвращает цепочку от текущего элемента до первого предка включая текущий элемент
        """
        if type(id_) == str:
            try:
                id_ = int(id_)
            except ValueError:
                return []

        assert type(id_) == int
        node = self._get_node(id_)
        if node is None:
            return []
        return node.get_parent_items()

    def get_possible_parents(self, id_: int) -> list[MenuItem]:
        """
        Возвращает список возможных родителей для сохранения.
        """
        current = self._get_node(id_)
        items = [tree_item for tree_item in self._tree.values()]

        def is_possible(node):
            if node.is_descendant(current) or node is current or node.item is None:
                return False
            return True

        return list(map(lambda node: node.item, filter(is_possible, items)))


class ParentMenuItemChoiceField(ChoiceField):
    def clean(self, value):
        if value == '':
            return None
        return MenuItem.objects.get(pk=value)


def get_parent_choices(menu, menu_item=None):
    menu_tree = TreeStore(menu.get_all_children())
    choices = [(None, 'Root')]
    if menu_item is None:
        choices.extend(map(lambda i: (i.pk, i), menu_tree.head.get_flattened()))
        return choices
    for item in menu_tree.get_possible_parents(menu_item.pk):
        choices.append((item.pk, item))
    return choices
