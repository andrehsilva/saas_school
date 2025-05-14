from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Note
from school.models import Student, Parent, Subject, Grade

@login_required
def notes_timeline(request):
    user = request.user
    is_parent = False
    students = []

    # Determinar se é aluno ou responsável
    try:
        student = Student.objects.get(user=user)
        students = [student]
    except Student.DoesNotExist:
        try:
            parent = Parent.objects.get(user=user)
            students = parent.children.all()
            is_parent = True
        except Parent.DoesNotExist:
            pass

    # Query base
    notes = Note.objects.filter(student__in=students) if students else Note.objects.none()

    # Aplicar filtros
    subject_id = request.GET.get('subject')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    search_query = request.GET.get('q')

    if subject_id:
        notes = notes.filter(subject_id=subject_id)
    if date_from:
        notes = notes.filter(date__gte=date_from)
    if date_to:
        notes = notes.filter(date__lte=date_to)
    if search_query:
        notes = notes.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(performance__icontains=search_query) |
            Q(score__icontains=search_query)
        ).distinct()

    # Obter opções de filtros
    subjects = Subject.objects.filter(  
        note__student__in=students
    ).distinct() if students else Subject.objects.none()

    # Paginação
    paginator = Paginator(notes.order_by('-date'), 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'note/notes_timeline.html', {
        'notes': page_obj,
        'subjects': subjects,
        'is_parent': is_parent,
        'search_query': search_query or '',
        'selected_subject': int(subject_id) if subject_id else '',
        'date_from': date_from or '',
        'date_to': date_to or '',
    })