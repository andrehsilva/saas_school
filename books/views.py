from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.http import FileResponse, Http404, JsonResponse
from django.db.models import Q

from books.models import Document, Category
from school.models import Student, Parent, Class, Grade

@login_required
def my_documents(request):
    user = request.user
    documents = get_accessible_documents(user)

    # Filtro por busca unificado
    search_query = request.GET.get('q', '')
    if search_query:
        documents = documents.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        ).distinct()

    # Filtro por categoria específica
    category_id = request.GET.get('category', '')
    if category_id:
        documents = documents.filter(categories__id=category_id)

    # Paginação
    paginator = Paginator(documents.order_by('-uploaded_at'), 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Categorias acessíveis
    accessible_categories = Category.objects.filter(document__in=documents).distinct()

    return render(request, 'books/my_documents.html', {
        'documents': page_obj,
        'page_obj': page_obj,
        'search_query': search_query,
        'categories': accessible_categories,
        'selected_category': int(category_id) if category_id.isdigit() else None
    })

def get_accessible_documents(user):
    student = Student.objects.filter(user=user).first()

    if not student:
        parent = Parent.objects.filter(user=user).first()
        students = parent.children.all() if parent else Student.objects.none()
        student_users = [s.user for s in students]
    else:
        students = [student]
        student_users = [user]

    user_classes = Class.objects.filter(students__in=students).distinct()
    user_grades = Grade.objects.filter(class__in=user_classes).distinct()

    direct_documents = Document.objects.filter(Q(target_users=user) | Q(target_users__in=student_users))
    class_documents = Document.objects.filter(target_classes__in=user_classes)
    grade_documents = Document.objects.filter(target_grades__in=user_grades)

    return (direct_documents | class_documents | grade_documents).distinct()

@login_required
def view_pdf(request, doc_id):
    doc = get_object_or_404(Document, id=doc_id)

    if not has_document_access(request.user, doc):
        raise Http404("Você não tem permissão para acessar este documento.")

    return render(request, 'books/pdf_modal.html', {
        'document': doc,
        'pdf_url': doc.file.url
    })

def has_document_access(user, document):
    if document.target_users.filter(id=user.id).exists():
        return True

    student = Student.objects.filter(user=user).first()
    if student:
        if document.target_classes.filter(students=student).exists():
            return True
        if document.target_grades.filter(class__students=student).exists():
            return True

    try:
        parent = Parent.objects.get(user=user)
        students = parent.children.all()
        if document.target_classes.filter(students__in=students).exists():
            return True
        if document.target_grades.filter(class__students__in=students).exists():
            return True
    except Parent.DoesNotExist:
        pass

    return False
