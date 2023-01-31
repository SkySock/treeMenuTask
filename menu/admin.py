from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponseRedirect
from django.urls import path
from django.views.generic import RedirectView

from menu.models import MenuItem, Menu
from menu.utils import TreeStore, get_parent_choices, ParentMenuItemChoiceField


class MenuItemAdmin(admin.ModelAdmin):

    def __init__(self, model, admin_site, menu):
        super().__init__(model, admin_site)
        self._menu = menu

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        choices = get_parent_choices(self._menu, obj)
        form.base_fields['parent'] = ParentMenuItemChoiceField(choices=choices)
        return form

    def save_model(self, request, obj, form, change):
        obj.menu = self._menu
        obj.save()

    def response_change(self, request, obj):
        super().response_change(request, obj)
        if "_continue" in request.POST:
            return HttpResponseRedirect(request.path)
        elif "_addanother" in request.POST:
            return HttpResponseRedirect("../add/")
        else:
            return HttpResponseRedirect("../../")

    def response_add(self, request, obj, post_url_continue=None):

        pk_value = obj._get_pk_val()
        post_url_continue = f'../{pk_value}/'
        response = super().response_add(request, obj, post_url_continue)
        if "_continue" in request.POST:
            return response
        elif "_addanother" in request.POST:
            return HttpResponseRedirect(request.path)
        elif "_popup" in request.POST:
            return response
        else:
            return HttpResponseRedirect("../../")
    
    def response_delete(self, request, obj_display, obj_id):
        response = super().response_delete(request, obj_display, obj_id)
        return response


@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    menu_item_admin_class = MenuItemAdmin

    def get_urls(self):
        urls = super().get_urls()
        menu_urls = [
            path('<int:menu_pk>/items/<int:item_pk>/', self.admin_site.admin_view(self.edit_menu_item)),
            path('<int:menu_pk>/items/<int:item_pk>/delete/', self.admin_site.admin_view(self.delete_menu_item)),
            path('<int:menu_pk>/items/add/', self.admin_site.admin_view(self.add_menu_item)),

            path('item_changelist/', RedirectView.as_view(url='../'), name='menu_menuitem_changelist'),
            path('item_add/', RedirectView.as_view(url='/'), name='menu_menuitem_add'),
            path('item/<int:item_pk>/change/', RedirectView.as_view(url='/'), name='menu_menuitem_change'),

        ]
        return menu_urls + urls

    def change_view(self, request, object_id, form_url="", extra_context=None):
        menu = self.get_menu_with_permissions(request, object_id)
        menu_items = TreeStore(menu.get_all_children()).head.get_flattened()
        if not extra_context:
            extra_context = {'menu_items': menu_items}
        else:
            extra_context['menu_items'] = menu_items
        return super().change_view(request, object_id, form_url=form_url, extra_context=extra_context)

    def add_menu_item(self, request, menu_pk):
        menu = self.get_menu_with_permissions(request, menu_pk)

        menuitem_admin = self.menu_item_admin_class(MenuItem, self.admin_site, menu)
        return menuitem_admin.add_view(request, extra_context={'menu': menu})

    def edit_menu_item(self, request, menu_pk, item_pk):
        menu = self.get_menu_with_permissions(request, menu_pk)

        menu_item_admin = self.menu_item_admin_class(MenuItem, self.admin_site, menu)
        return menu_item_admin.change_view(request, str(item_pk), extra_context={'menu': menu, "show_delete": False})

    def delete_menu_item(self, request, menu_pk, item_pk):
        menu = self.get_menu_with_permissions(request, menu_pk)

        menu_item_admin = self.menu_item_admin_class(MenuItem, self.admin_site, menu)
        return menu_item_admin.delete_view(request, str(item_pk), extra_context={'menu': menu})

    def get_menu_with_permissions(self, request, menu_pk):
        try:
            menu = Menu.objects.get(pk=menu_pk)
        except Menu.DoesNotExist:
            raise Http404(f'Menu with pk={menu_pk} does not exist.')

        if not self.has_change_permission(request, menu):
            raise PermissionDenied
        return menu
