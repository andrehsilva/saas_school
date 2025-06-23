from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, Http404
from django.db.models import Q
from django.core.exceptions import PermissionDenied
from dashboard.permissions import role_required

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required

from django.contrib import messages
from django.urls import reverse

from .models import Document, Category, Grade, Class
from django.contrib.auth.models import User

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
def document_detail(request, pk):
    document = get_object_or_404(Document, id=pk)

    if not has_document_access(request.user, document):
        raise PermissionDenied("Você não tem permissão para acessar este documento.")

    return render(request, "books/document_detail.html", {"document": document})


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





####### dashboard books ############
# --- LISTA DO DASHBOARD ---
@login_required
@role_required(["Diretor", "Coordenador", "Professor", "Colaborador"])
def dashboard_document_list(request):
    title = request.GET.get('title', '').strip()
    author = request.GET.get('author', '').strip()
    category_id = request.GET.get('category', '')
    uploaded_by_id = request.GET.get('uploaded_by', '')

    documents_qs = Document.objects.all()

    if title:
        documents_qs = documents_qs.filter(title__icontains=title)
    if author:
        documents_qs = documents_qs.filter(
            Q(uploaded_by__first_name__icontains=author) |
            Q(uploaded_by__last_name__icontains=author)
        )
    if category_id:
        documents_qs = documents_qs.filter(categories__id=category_id)
    if uploaded_by_id:
        documents_qs = documents_qs.filter(uploaded_by_id=uploaded_by_id)

    documents_qs = documents_qs.select_related('uploaded_by').prefetch_related('categories').order_by('-uploaded_at').distinct()

    paginator = Paginator(documents_qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    categories = Category.objects.all()
    users = User.objects.filter(id__in=Document.objects.values_list('uploaded_by', flat=True).distinct())

    return render(request, 'dashboard/books/list.html', {
        'documents': page_obj,
        'categories': categories,
        'users': users,
        'current_title': title,
        'current_author': author,
        'current_category': category_id,
        'current_uploaded_by': uploaded_by_id,
        'page_obj': page_obj,
    })

# --- CRIAÇÃO ---
@login_required
@role_required(["Diretor", "Coordenador", "Professor", "Colaborador"])
def dashboard_document_create(request):
    categories = Category.objects.all()
    grades = Grade.objects.all()
    classes = Class.objects.all()
    users = User.objects.all()

    # Para selects múltiplos
    selected_categories = request.POST.getlist('categories') if request.method == "POST" else []
    selected_grades = request.POST.getlist('target_grades') if request.method == "POST" else []
    selected_classes = request.POST.getlist('target_classes') if request.method == "POST" else []
    selected_users = request.POST.getlist('target_users') if request.method == "POST" else []

    if request.method == "POST":
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        file = request.FILES.get('file')
        thumbnail = request.FILES.get('thumbnail')

        if not title or not file:
            messages.error(request, "Título e arquivo PDF são obrigatórios.")
        else:
            document = Document.objects.create(
                title=title,
                description=description,
                file=file,
                thumbnail=thumbnail,
                uploaded_by=request.user
            )
            document.categories.set(Category.objects.filter(id__in=selected_categories))
            document.target_grades.set(Grade.objects.filter(id__in=selected_grades))
            document.target_classes.set(Class.objects.filter(id__in=selected_classes))
            document.target_users.set(User.objects.filter(id__in=selected_users))
            messages.success(request, f"Documento '{document.title}' criado com sucesso.")
            return redirect('books:dashboard_document_list')

    return render(request, 'dashboard/books/form.html', {
        'form_title': "Novo Documento",
        'document': None,
        'categories': categories,
        'grades': grades,
        'classes': classes,
        'users': users,
        'selected_categories': selected_categories,
        'selected_grades': selected_grades,
        'selected_classes': selected_classes,
        'selected_users': selected_users,
    })

# --- EDIÇÃO ---
@login_required
@role_required(["Diretor", "Coordenador", "Professor", "Colaborador"])
def dashboard_document_edit(request, document_id):
    document = get_object_or_404(Document, id=document_id)
    categories = Category.objects.all()
    grades = Grade.objects.all()
    classes = Class.objects.all()
    users = User.objects.all()

    if request.method == "POST":
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        file = request.FILES.get('file')
        thumbnail = request.FILES.get('thumbnail')

        document.title = title
        document.description = description
        if file:
            document.file = file
        if thumbnail:
            document.thumbnail = thumbnail
        document.save()

        selected_categories = request.POST.getlist('categories')
        selected_grades = request.POST.getlist('target_grades')
        selected_classes = request.POST.getlist('target_classes')
        selected_users = request.POST.getlist('target_users')

        document.categories.set(Category.objects.filter(id__in=selected_categories))
        document.target_grades.set(Grade.objects.filter(id__in=selected_grades))
        document.target_classes.set(Class.objects.filter(id__in=selected_classes))
        document.target_users.set(User.objects.filter(id__in=selected_users))

        messages.success(request, f"Documento '{document.title}' atualizado com sucesso.")
        return redirect('books:dashboard_document_detail', document_id=document.id)
    else:
        selected_categories = [str(c.id) for c in document.categories.all()]
        selected_grades = [str(g.id) for g in document.target_grades.all()]
        selected_classes = [str(c.id) for c in document.target_classes.all()]
        selected_users = [str(u.id) for u in document.target_users.all()]

    return render(request, 'dashboard/books/form.html', {
        'form_title': f"Editar Documento: {document.title}",
        'document': document,
        'categories': categories,
        'grades': grades,
        'classes': classes,
        'users': users,
        'selected_categories': selected_categories,
        'selected_grades': selected_grades,
        'selected_classes': selected_classes,
        'selected_users': selected_users,
    })

# --- EXCLUSÃO ---
@login_required
@role_required(["Diretor", "Coordenador", "Professor", "Colaborador"])
def dashboard_document_delete(request, document_id):
    document = get_object_or_404(Document, id=document_id)
    if request.method == "POST":
        title = document.title
        document.delete()
        messages.success(request, f"Documento '{title}' excluído com sucesso.")
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f"Documento '{title}' excluído com sucesso."})
        return redirect('books:dashboard_document_list')

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'error': 'Método não permitido. Use POST para excluir.'}, status=405)
    return redirect('books:dashboard_document_list')

# --- DETALHE ---
@login_required
@role_required(["Diretor", "Coordenador", "Professor", "Colaborador"])
def dashboard_document_detail(request, document_id):
    document = get_object_or_404(Document, id=document_id)
    return render(request, 'dashboard/books/detail.html', {'document': document})