from django.db import models
from django.urls import reverse, NoReverseMatch


class MenuItem(models.Model):
    menu = models.ForeignKey('Menu', on_delete=models.CASCADE, editable=False, related_name='items')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    url = models.CharField(max_length=200, blank=True)
    named_url = models.CharField(max_length=200, blank=True)
    label = models.CharField(max_length=40)
    level = models.IntegerField(default=0, editable=False)

    class Meta:
        ordering = ('level',)

    def get_url(self):
        if self.url:
            return self.url
        try:
            return reverse(self.named_url)
        except NoReverseMatch:
            return ""

    def __str__(self):
        parent_label = self.parent.label if self.parent else 'Root'
        return f"Menu(label: {self.label}, parent: {parent_label})"

    def save(self, **kwargs):
        old_level = self.level
        if self.parent:
            self.level = self.parent.level + 1
        else:
            self.level = 0

        if old_level != self.level:
            for child in self.get_children():
                child.save()

        super().save(**kwargs)

    def get_children(self):
        return MenuItem.objects.filter(parent=self.pk)

    @property
    def label_with_spaces(self) -> str:
        return "|    " * self.level + str(self.label)


class Menu(models.Model):
    name = models.CharField(max_length=40, unique=True, db_index=True)

    def get_all_children(self):
        return MenuItem.objects.select_related('parent').filter(menu=self.pk).order_by('parent')
