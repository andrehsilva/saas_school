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
    documents = get_accessible_collections(user)

    search_query = request.GET.get('q', '')
    if search_query:
        documents = documents.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(categories__name__icontains=search_query)
        ).distinct()

    category_id = request.GET.get('category', '')
    if category_id:
        documents = documents.filter(categories__id=category_id)

    paginator = Paginator(documents.order_by('-uploaded_at'), 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    accessible_categories = Category.objects.filter(collectionitem__in=documents).distinct()

    return render(request, 'collection/my_collections.html', {
        'page_obj': page_obj,
        'search_query': search_query,
        'categories': accessible_categories,
        'selected_category': int(category_id) if category_id and category_id.isdigit() else None
    })


@login_required
def collection_detail(request, item_id):
    item = get_object_or_404(CollectionItem, id=item_id)

    if not has_access(request.user, item):
        raise Http404("Você não tem permissão para acessar este conteúdo.")

    return render(request, 'collection/collection_detail.html', {
        'item': item
    })

@login_required
def view_html(request, item_id):
    item = get_object_or_404(CollectionItem, id=item_id)

    if not has_access(request.user, item):
        raise Http404("Você não tem permissão para acessar este item.")

    return render(request, 'collection/html_modal.html', {
        'document': item,
        'html_url': item.get_html_url()
    })