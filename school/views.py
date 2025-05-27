import json
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.serializers.json import DjangoJSONEncoder
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from school.models import Grade, Class, Subject, Student, Parent
from school.models import Role, UserRole
from django.utils import timezone

# Apenas para admin
@staff_member_required
def import_users_view(request):
    return HttpResponse("Importar Usuários - função ainda não implementada")

def get_teacher_users():
    try:
        teacher_role = Role.objects.get(name__iexact="Professor")
        teacher_ids = UserRole.objects.filter(role=teacher_role).values_list('user_id', flat=True)
        return User.objects.filter(id__in=teacher_ids)
    except Role.DoesNotExist:
        return User.objects.none()

# Listagem de séries
@login_required
@permission_required('school.view_grade', raise_exception=True)
def grade_list(request):
    grades = Grade.objects.prefetch_related('colaborator', 'coordinators', 'directors')
    return render(request, 'dashboard/grades/list.html', {'grades': grades})


def get_eligible_users_json():
    student_ids = Student.objects.values_list('user_id', flat=True)
    parent_ids = Parent.objects.values_list('user_id', flat=True)
    users = User.objects.exclude(id__in=student_ids).exclude(id__in=parent_ids)
    return json.dumps(list(users.values('id', 'username', 'first_name', 'last_name')), cls=DjangoJSONEncoder)


@login_required
@permission_required('school.add_grade', raise_exception=True)
def grade_create(request):
    users_json = get_eligible_users_json()

    if request.method == "POST":
        grade_name = request.POST.get('name', '').strip()
        coord_ids = request.POST.getlist('coordinators')
        dir_ids = request.POST.getlist('directors')
        colab_ids = request.POST.getlist('colaborators')

        if not grade_name:
            messages.error(request, "O nome da série é obrigatório.")

            context = {
                "users": users_json,
                "form_title": "Nova Série",
                "form_subtitle": "Complete os campos abaixo para cadastrar uma nova série.",
                "current_name": grade_name,
                "selected_coordinators_json": json.dumps(list(User.objects.filter(id__in=coord_ids).values('id', 'username', 'first_name', 'last_name')), cls=DjangoJSONEncoder),
                "selected_directors_json": json.dumps(list(User.objects.filter(id__in=dir_ids).values('id', 'username', 'first_name', 'last_name')), cls=DjangoJSONEncoder),
                "selected_colaborators_json": json.dumps(list(User.objects.filter(id__in=colab_ids).values('id', 'username', 'first_name', 'last_name')), cls=DjangoJSONEncoder),
            }
            return render(request, "dashboard/grades/form.html", context)

        new_grade = Grade.objects.create(name=grade_name)
        new_grade.coordinators.set(User.objects.filter(id__in=coord_ids))
        new_grade.directors.set(User.objects.filter(id__in=dir_ids))
        if hasattr(new_grade, 'colaborator'):
            new_grade.colaborator.set(User.objects.filter(id__in=colab_ids))

        messages.success(request, f"Série '{new_grade.name}' criada com sucesso.")
        return redirect('school:grade_list')

    # GET
    return render(request, "dashboard/grades/form.html", {
        "users": users_json,
        "form_title": "Nova Série",
        "form_subtitle": "Complete os campos abaixo para cadastrar uma nova série.",
        "current_name": "",
        "selected_coordinators_json": "[]",
        "selected_directors_json": "[]",
        "selected_colaborators_json": "[]",
    })


@login_required
@permission_required('school.change_grade', raise_exception=True)
def grade_edit(request, grade_id):
    grade = get_object_or_404(Grade, id=grade_id)
    users_json = get_eligible_users_json()

    if request.method == 'POST':
        grade_name = request.POST.get('name', '').strip()
        coord_ids = request.POST.getlist('coordinators')
        dir_ids = request.POST.getlist('directors')
        colab_ids = request.POST.getlist('colaborators')

        if not grade_name:
            messages.error(request, "O nome da série é obrigatório.")
            return redirect('dashboard:grade_edit', grade_id=grade.id)

        grade.name = grade_name
        grade.coordinators.set(User.objects.filter(id__in=coord_ids))
        grade.directors.set(User.objects.filter(id__in=dir_ids))
        if hasattr(grade, 'colaborator'):
            grade.colaborator.set(User.objects.filter(id__in=colab_ids))
        grade.save()

        messages.success(request, f"Série '{grade.name}' atualizada com sucesso.")
        return redirect('school:grade_list')

    selected_coordinators = list(grade.coordinators.all().values('id', 'username', 'first_name', 'last_name'))
    selected_directors = list(grade.directors.all().values('id', 'username', 'first_name', 'last_name'))
    selected_colaborators = list(grade.colaborator.all().values('id', 'username', 'first_name', 'last_name')) if hasattr(grade, 'colaborator') else []

    return render(request, 'dashboard/grades/form.html', {
        'grade': grade,
        'users': users_json,
        'form_title': f"Editar Série: {grade.name}",
        'form_subtitle': "Atualize os campos abaixo para editar a série.",
        'selected_coordinators_json': json.dumps(selected_coordinators, cls=DjangoJSONEncoder),
        'selected_directors_json': json.dumps(selected_directors, cls=DjangoJSONEncoder),
        'selected_colaborators_json': json.dumps(selected_colaborators, cls=DjangoJSONEncoder),
    })


@login_required
@permission_required('school.delete_grade', raise_exception=True)
def grade_delete(request, grade_id):
    grade = get_object_or_404(Grade, id=grade_id)
    if request.method == "POST":
        grade_name = grade.name
        grade.delete()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f'Série "{grade_name}" excluída com sucesso.'})
        messages.success(request, f'Série "{grade_name}" excluída com sucesso.')
    return redirect('school:grade_list')



@login_required
@permission_required('school.view_grade', raise_exception=True)
def grade_list(request):
    grades = Grade.objects.prefetch_related('colaborator', 'coordinators', 'directors')
    return render(request, 'dashboard/grades/list.html', {'grades': grades})



@login_required
@permission_required('school.view_class', raise_exception=True)
def class_list(request):
    classes = Class.objects.select_related('grade').prefetch_related('teachers')
    return render(request, 'dashboard/classes/list.html', {'classes': classes})

@login_required
@permission_required('school.add_class', raise_exception=True)
def class_create(request):
    grades = Grade.objects.all()
    teachers = get_teacher_users()
    if request.method == "POST":
        name = request.POST.get('name', '').strip()
        grade_id = request.POST.get('grade')
        teacher_ids = request.POST.getlist('teachers')
        academic_year = request.POST.get('academic_year', timezone.now().year)
        is_regular = bool(request.POST.get('is_regular', True))

        if not name or not grade_id:
            messages.error(request, "Nome da turma e série são obrigatórios.")
            return render(request, 'dashboard/classes/form.html', {
                'grades': grades,
                'teachers': teachers,
                'current_name': name,
                'current_grade': grade_id,
                'current_teachers': teacher_ids,
                'current_academic_year': academic_year,
                'current_is_regular': is_regular,
                'form_title': "Nova Turma"
            })

        turma = Class.objects.create(
            name=name,
            grade_id=grade_id,
            academic_year=academic_year,
            is_regular=is_regular
        )
        turma.teachers.set(User.objects.filter(id__in=teacher_ids))
        messages.success(request, f"Turma '{turma.name}' criada com sucesso.")
        return redirect('school:class_list')

    return render(request, 'dashboard/classes/form.html', {
        'grades': grades,
        'teachers': teachers,
        'form_title': "Nova Turma"
    })

@login_required
@permission_required('school.change_class', raise_exception=True)
def class_edit(request, class_id):
    turma = get_object_or_404(Class, id=class_id)
    grades = Grade.objects.all()
    teachers = get_teacher_users()
    if request.method == "POST":
        name = request.POST.get('name', '').strip()
        grade_id = request.POST.get('grade')
        teacher_ids = request.POST.getlist('teachers')
        academic_year = request.POST.get('academic_year', turma.academic_year)
        is_regular = bool(request.POST.get('is_regular', turma.is_regular))

        if not name or not grade_id:
            messages.error(request, "Nome da turma e série são obrigatórios.")
            return redirect('school:class_edit', class_id=turma.id)

        turma.name = name
        turma.grade_id = grade_id
        turma.academic_year = academic_year
        turma.is_regular = is_regular
        turma.teachers.set(User.objects.filter(id__in=teacher_ids))
        turma.save()
        messages.success(request, f"Turma '{turma.name}' atualizada com sucesso.")
        return redirect('school:class_list')

    return render(request, 'dashboard/classes/form.html', {
        'turma': turma,
        'grades': grades,
        'teachers': teachers,
        'current_name': turma.name,
        'current_grade': turma.grade_id,
        'current_teachers': [str(t.id) for t in turma.teachers.all()],
        'current_academic_year': turma.academic_year,
        'current_is_regular': turma.is_regular,
        'form_title': f"Editar Turma: {turma.name}"
    })

@login_required
@permission_required('school.delete_class', raise_exception=True)
def class_delete(request, class_id):
    turma = get_object_or_404(Class, id=class_id)
    if request.method == "POST":
        turma.delete()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        messages.success(request, f"Turma '{turma.name}' excluída com sucesso.")
    return redirect('school:class_list')