from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Note
from django.http import JsonResponse
from school.models import Student, Parent, Subject, Grade
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from dashboard.permissions import role_required
from .forms import NoteForm  # ajuste o import conforme seu form


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



@login_required
def note_detail(request, note_id):
    note = get_object_or_404(Note, id=note_id)

    # Verificação de permissão
    user = request.user
    is_allowed = False

    try:
        # Se for o próprio aluno
        is_allowed = note.student.user == user
    except:
        pass

    try:
        # Se for um responsável do aluno
        parent = Parent.objects.get(user=user)
        if note.student in parent.children.all():
            is_allowed = True
    except Parent.DoesNotExist:
        pass

    if not is_allowed:
        return HttpResponseForbidden("Você não tem permissão para ver essa nota.")

    return render(request, 'note/note_detail.html', {'note': note})




#################
###dashboard###
############

@login_required
def dashboard_note_list(request):
    notes = Note.objects.select_related('student', 'subject').all()
    students = Student.objects.all()
    subjects = Subject.objects.all()

    # Filtros
    title = request.GET.get('title', '').strip()
    student_id = request.GET.get('student', '')
    subject_id = request.GET.get('subject', '')

    if title:
        notes = notes.filter(title__icontains=title)
    if student_id:
        notes = notes.filter(student_id=student_id)
    if subject_id:
        notes = notes.filter(subject_id=subject_id)

    notes = notes.order_by('-date')
    paginator = Paginator(notes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'dashboard/notes/list.html', {
        'notes': page_obj,
        'students': students,
        'subjects': subjects,
        'current_title': title,
        'current_student': student_id,
        'current_subject': subject_id,
    })


@login_required
@role_required(["Diretor", "Coordenador", "Professor"])
def dashboard_note_create(request):
    if request.method == "POST":
        form = NoteForm(request.POST, request.FILES)
        if form.is_valid():
            note = form.save()
            messages.success(request, f"Nota '{note.title}' criada com sucesso.")
            return redirect('notes:dashboard_note_list')
        else:
            messages.error(request, "Erro ao criar a nota. Verifique os campos.")
    else:
        form = NoteForm()
    return render(request, 'dashboard/notes/form.html', {
        'form': form,
        'form_title': "Nova Nota",
        'note': None,
    })



@login_required
def dashboard_note_edit(request, note_id):
    note = get_object_or_404(Note, id=note_id)
    if request.method == 'POST':
        form = NoteForm(request.POST, request.FILES, instance=note)
        if form.is_valid():
            form.save()
            messages.success(request, f'Nota "{note.title}" atualizada com sucesso.')
            return redirect('notes:dashboard_note_list')
        else:
            messages.error(request, 'Erro ao atualizar a nota. Verifique os campos.')
    else:
        form = NoteForm(instance=note)
    return render(request, 'dashboard/notes/form.html', {
        'form': form,
        'form_title': 'Editar Nota',
        'note': note,
    })

@login_required
@role_required(["Diretor", "Coordenador", "Professor", "Colaborador"])
def dashboard_note_detail(request, note_id):
    """
    Visualização detalhada de uma nota no dashboard
    """
    note = get_object_or_404(Note, pk=note_id)

    # Verifica se o usuário tem permissão para ver esta nota
    has_permission = False

    # Aluno da nota
    if note.student == request.user:
        has_permission = True

    
    # Administrador
    elif request.user.roles.filter(role__name__in=["Diretor", "Coordenador"]).exists():
        has_permission = True

    if not has_permission:
        messages.error(request, "Você não tem permissão para visualizar esta nota.")
        return redirect('notes:dashboard_note_list')

    return render(request, 'dashboard/notes/detail.html', {
        'note': note
    })


@login_required
def dashboard_note_delete(request, note_id):
    note = get_object_or_404(Note, id=note_id)
    if request.method == 'POST':
        note.delete()
        messages.success(request, f'Nota "{note.title}" excluída com sucesso.')
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Método inválido.'})