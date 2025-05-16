from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.http import Http404
from django.db.models import Q

from books.models import Document, Category
from school.utils.documents_access import get_accessible_documents, has_document_access


@login_required
def my_documents(request):
    user = request.user
    documents = get_accessible_documents(user)

    query = request.GET.get('q', '')
    if query:
        documents = documents.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        ).distinct()

    category_id = request.GET.get('category', '')
    if category_id:
        documents = documents.filter(categories__id=category_id)

    paginator = Paginator(documents.order_by('-uploaded_at'), 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    accessible_categories = Category.objects.filter(document__in=documents).distinct()

    return render(request, 'books/my_documents.html', {
        'documents': page_obj,
        'page_obj': page_obj,
        'search_query': query,
        'categories': accessible_categories,
        'selected_category': int(category_id) if category_id.isdigit() else None
    })


@login_required
def view_pdf(request, doc_id):
    document = get_object_or_404(Document, id=doc_id)

    if not has_document_access(request.user, document):
        raise Http404("Você não tem permissão para acessar este documento.")

    return render(request, 'books/pdf_modal.html', {
        'document': document,
        'pdf_url': document.file.url
    })
