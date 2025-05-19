# collection/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import Http404
from .models import CollectionItem, Category
from .utils import get_accessible_collections, has_access

@login_required
def my_collections(request):
    user = request.user
    collections = get_accessible_collections(user)

    # Filtros
    search_query = request.GET.get('q', '')
    if search_query:
        collections = collections.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(categories__name__icontains=search_query)
        ).distinct()

    category_id = request.GET.get('category', '')
    if category_id.isdigit():
        collections = collections.filter(categories__id=int(category_id))

    # Paginação
    paginator = Paginator(collections.order_by('-uploaded_at'), 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Categorias acessíveis
    accessible_categories = Category.objects.filter(
        collectionitem__in=collections
    ).distinct()

    return render(request, 'collection/my_collections.html', {
        'page_obj': page_obj,
        'categories': accessible_categories,
        'search_query': search_query,
        'selected_category': int(category_id) if category_id.isdigit() else None
    })

@login_required
def view_html(request, item_id):
    item = get_object_or_404(CollectionItem, id=item_id)

    if not has_access(request.user, item):
        raise Http404("Acesso não autorizado a este item.")

    return render(request, 'collection/html_modal.html', {
        'document': item,
        'html_url': item.get_html_url()
    })
    