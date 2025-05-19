from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.http import Http404
from django.db.models import Q

from books.models import Document, Category
from books.utils import get_accessible_documents, has_document_access  # Importe do local correto


@login_required
def my_documents(request):
    user = request.user
    documents = get_accessible_documents(user)
    
    search_query = request.GET.get('q', '')
    if search_query:
        documents = documents.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(categories__name__icontains=search_query)
        ).distinct()
    
    category_id = request.GET.get('category', '')
    if category_id.isdigit():
        documents = documents.filter(categories__id=int(category_id))


    
    # Paginação
    paginator = Paginator(documents.order_by('-uploaded_at'), 12)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    # Categorias disponíveis para filtro
    accessible_categories = Category.objects.filter(
        document__in=documents
    ).distinct()
    
    return render(request, 'books/my_documents.html', {
        'page_obj': page_obj,
        'categories': accessible_categories,
        'search_query': search_query,
        'selected_category': int(category_id) if category_id.isdigit() else None
    })


@login_required
def view_pdf(request, doc_id):
    document = get_object_or_404(Document, id=doc_id)
    
    # Verificação robusta de acesso
    if not has_document_access(request.user, document):
        raise Http404("Acesso não autorizado a este documento.")
    
    return render(request, 'books/pdf_modal.html', {
        'document': document,
        'pdf_url': document.file.url
    })