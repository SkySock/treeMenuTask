from django.shortcuts import render
from django.views import View


class IndexView(View):

    def get(self, request, *args, **kwargs):

        items = request.GET.get('active_items', '')
        context = {'active_items': items.split(';')}
        return render(request, 'menu/index.html', context=context)
