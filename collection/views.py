from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import Http404
from .models import CollectionItem, Category
from school.models import Student, Parent, Class, Grade

@login_required
def my_collections(request):
    user = request.user
    documents = get_accessible_collections(user)

    search_query = request.GET.get('q', '')
    if search_query:
        documents = documents.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        ).distinct()

    category_id = request.GET.get('category', '')
    if category_id:
        documents = documents.filter(categories__id=category_id)

    paginator = Paginator(documents.order_by('-uploaded_at'), 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    accessible_categories = Category.objects.filter(collectionitem__in=documents).distinct()

    return render(request, 'collection/my_collections.html', {
        'documents': page_obj,
        'search_query': search_query,
        'categories': accessible_categories,
        'selected_category': int(category_id) if category_id.isdigit() else None
    })

def get_accessible_collections(user):
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

    direct = CollectionItem.objects.filter(Q(target_users=user) | Q(target_users__in=student_users))
    class_based = CollectionItem.objects.filter(target_classes__in=user_classes)
    grade_based = CollectionItem.objects.filter(target_grades__in=user_grades)

    return (direct | class_based | grade_based).distinct()

@login_required
def view_html(request, item_id):
    item = get_object_or_404(CollectionItem, id=item_id)

    if not has_access(request.user, item):
        raise Http404("Você não tem permissão para acessar este item.")

    return render(request, 'collection/html_modal.html', {
        'document': item,
        'html_url': item.get_html_url()
    })

def has_access(user, document):
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
