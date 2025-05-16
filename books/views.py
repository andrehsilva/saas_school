from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.http import Http404
from django.db.models import Q

from books.models import Document, Category
from school.models import Student, Parent, Class, Grade
from school.models import UserRole  # Supondo que está em 'users'

@login_required
def my_documents(request):
    user = request.user
    documents = get_accessible_documents(user)

    # Filtro de busca (título ou descrição)
    query = request.GET.get('q', '')
    if query:
        documents = documents.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        ).distinct()

    # Filtro por categoria
    category_id = request.GET.get('category', '')
    if category_id:
        documents = documents.filter(categories__id=category_id)

    # Paginação (12 documentos por página)
    paginator = Paginator(documents.order_by('-uploaded_at'), 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Categorias acessíveis com base nos documentos visíveis
    accessible_categories = Category.objects.filter(document__in=documents).distinct()

    return render(request, 'books/my_documents.html', {
        'documents': page_obj,
        'page_obj': page_obj,
        'search_query': query,
        'categories': accessible_categories,
        'selected_category': int(category_id) if category_id.isdigit() else None
    })


def get_accessible_documents(user):
    roles = UserRole.objects.filter(user=user).select_related('role')
    role_names = [r.role.name.lower() for r in roles]

    documents = Document.objects.filter(target_users=user)

    if 'teacher' in role_names:
        classes = Class.objects.filter(teachers=user)
        grades = Grade.objects.filter(class__in=classes)
        documents |= Document.objects.filter(
            Q(target_classes__in=classes) | Q(target_grades__in=grades)
        )

    elif 'coordinator' in role_names or 'director' in role_names:
        all_classes = Class.objects.all()
        all_grades = Grade.objects.all()
        documents |= Document.objects.filter(
            Q(target_classes__in=all_classes) | Q(target_grades__in=all_grades)
        )

    student = Student.objects.filter(user=user).first()
    if student:
        classes = student.classes_assigned.all()
        grades = Grade.objects.filter(class__in=classes)
        documents |= Document.objects.filter(
            Q(target_classes__in=classes) |
            Q(target_grades__in=grades) |
            Q(target_users=user)
        )

    parent = Parent.objects.filter(user=user).first()
    if parent:
        children = parent.children.all()
        children_users = [c.user for c in children]
        classes = Class.objects.filter(students__in=children).distinct()
        grades = Grade.objects.filter(class__in=classes)
        documents |= Document.objects.filter(
            Q(target_classes__in=classes) |
            Q(target_grades__in=grades) |
            Q(target_users__in=children_users)
        )

    return documents.distinct()


def has_document_access(user, document):
    # Acesso direto
    if document.target_users.filter(id=user.id).exists():
        return True

    # Acesso como aluno
    student = Student.objects.filter(user=user).first()
    if student:
        if document.target_classes.filter(students=student).exists():
            return True
        if document.target_grades.filter(class__students=student).exists():
            return True

    # Acesso como responsável
    parent = Parent.objects.filter(user=user).first()
    if parent:
        children = parent.children.all()
        if document.target_classes.filter(students__in=children).exists():
            return True
        if document.target_grades.filter(class__students__in=children).exists():
            return True

    # Acesso por papel administrativo
    roles = UserRole.objects.filter(user=user).select_related('role')
    role_names = [r.role.name.lower() for r in roles]

    if 'teacher' in role_names:
        if document.target_classes.filter(teachers=user).exists():
            return True
        if document.target_grades.filter(subjects__teachers=user).exists():
            return True

    if 'coordinator' in role_names or 'director' in role_names:
        return True

    return False


@login_required
def view_pdf(request, doc_id):
    document = get_object_or_404(Document, id=doc_id)

    if not has_document_access(request.user, document):
        raise Http404("Você não tem permissão para acessar este documento.")

    return render(request, 'books/pdf_modal.html', {
        'document': document,
        'pdf_url': document.file.url
    })
