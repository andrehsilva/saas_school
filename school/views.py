import json
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.serializers.json import DjangoJSONEncoder
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from school.models import Grade, Class, Subject, Student, Parent
from school.models import Role, UserRole
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Count, Q
import csv

# Importe a função de notificação (caminho já deve estar correto)
from notification.utils import send_notification
from dashboard.permissions import dashboard_access_required, role_required


# --- Funções Auxiliares ---
def get_teacher_users():
    try:
        teacher_role = Role.objects.get(name__iexact="Professor")
        teacher_ids = UserRole.objects.filter(role=teacher_role).values_list('user_id', flat=True)
        return User.objects.filter(id__in=teacher_ids)
    except Role.DoesNotExist:
        return User.objects.none()

def get_eligible_users_json():
    student_ids = Student.objects.values_list('user_id', flat=True)
    parent_ids = Parent.objects.values_list('user_id', flat=True)
    users = User.objects.exclude(id__in=student_ids).exclude(id__in=parent_ids)
    return json.dumps(list(users.values('id', 'username', 'first_name', 'last_name')), cls=DjangoJSONEncoder)

# Nova função auxiliar para obter usuários de cargo
def get_users_by_role_in_grade(grade, role_type):
    """
    Retorna os usuários (coordenadores, diretores, colaboradores) associados a uma série.
    role_type pode ser 'coordinators', 'directors', 'colaborator'.
    """
    if hasattr(grade, role_type):
        return grade.__getattribute__(role_type).all()
    return User.objects.none()

# --- Views de Série (Mantidas como antes, mas incluídas para contexto completo) ---
@staff_member_required
def import_users_view(request):
    return HttpResponse("Importar Usuários - função ainda não implementada")

@login_required
@role_required(["Diretor", "Coordenador", "Professor"])
def grade_list(request):
    name = request.GET.get('name', '').strip()
    grades_qs = Grade.objects.prefetch_related('colaborator', 'coordinators', 'directors').order_by('name')
    if name:
        grades_qs = grades_qs.filter(name__icontains=name)
    paginator = Paginator(grades_qs, 10)  # 10 por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'dashboard/grades/list.html', {
        'grades': page_obj.object_list,
        'page_obj': page_obj,
        'current_name': name,
    })

@login_required
@role_required(["Diretor"])
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
                "users": users_json, "form_title": "Nova Série", "form_subtitle": "Complete os campos abaixo para cadastrar uma nova série.",
                "current_name": grade_name,
                "selected_coordinators_json": json.dumps(list(User.objects.filter(id__in=coord_ids).values('id', 'username', 'first_name', 'last_name')), cls=DjangoJSONEncoder),
                "selected_directors_json": json.dumps(list(User.objects.filter(id__in=dir_ids).values('id', 'username', 'first_name', 'last_name')), cls=DjangoJSONEncoder),
                "selected_colaborators_json": json.dumps(list(User.objects.filter(id__in=colab_ids).values('id', 'username', 'first_name', 'last_name')), cls=DjangoJSONEncoder),
            }
            return render(request, "dashboard/grades/form.html", context)
        new_grade = Grade.objects.create(name=grade_name)
        new_grade.coordinators.set(User.objects.filter(id__in=coord_ids))
        new_grade.directors.set(User.objects.filter(id__in=dir_ids))
        new_grade.colaborator.set(User.objects.filter(id__in=colab_ids))
        new_grade.save()

        grade_url = request.build_absolute_uri(reverse('school:grade_edit', args=[new_grade.id]))
        notified_users = set()

        if request.user.is_authenticated and request.user.id not in notified_users:
            send_notification(recipients=request.user, title=f"Série Criada: {new_grade.name}", message=f"Você criou a nova série '{new_grade.name}'.", url=grade_url)
            notified_users.add(request.user.id)
        
        for user_list, role_name in [(new_grade.coordinators.all(), "Coordenador"),
                                     (new_grade.directors.all(), "Diretor"),
                                     (new_grade.colaborator.all(), "Colaborador")]:
            for user in user_list:
                if user.id not in notified_users:
                    send_notification(recipients=user, title=f"Atribuição: {new_grade.name}", message=f"Você foi atribuído como {role_name} na série '{new_grade.name}'.", url=grade_url)
                    notified_users.add(user.id)

        messages.success(request, f"Série '{new_grade.name}' criada com sucesso.")
        return redirect('school:grade_list')
    return render(request, "dashboard/grades/form.html", {
        "users": users_json, "form_title": "Nova Série", "form_subtitle": "Complete os campos abaixo para cadastrar uma nova série.",
        "current_name": "", "selected_coordinators_json": "[]", "selected_directors_json": "[]", "selected_colaborators_json": "[]",
    })

@login_required
@role_required(["Diretor"])
def grade_edit(request, grade_id):
    grade = get_object_or_404(Grade, id=grade_id)
    users_json = get_eligible_users_json()

    old_coordinators = set(grade.coordinators.all().values_list('id', flat=True))
    old_directors = set(grade.directors.all().values_list('id', flat=True))
    old_colaborators = set(grade.colaborator.all().values_list('id', flat=True)) if hasattr(grade, 'colaborator') else set()
    old_name = grade.name

    if request.method == 'POST':
        grade_name = request.POST.get('name', '').strip()
        coord_ids = [int(i) for i in request.POST.getlist('coordinators')]
        dir_ids = [int(i) for i in request.POST.getlist('directors')]
        colab_ids = [int(i) for i in request.POST.getlist('colaborators')]

        if not grade_name:
            messages.error(request, "O nome da série é obrigatório.")
            selected_coordinators = list(User.objects.filter(id__in=coord_ids).values('id', 'username', 'first_name', 'last_name'))
            selected_directors = list(User.objects.filter(id__in=dir_ids).values('id', 'username', 'first_name', 'last_name'))
            selected_colaborators = list(User.objects.filter(id__in=colab_ids).values('id', 'username', 'first_name', 'last_name'))
            return render(request, 'dashboard/grades/form.html', {
                'grade': grade, 'users': users_json, 'form_title': f"Editar Série: {grade.name}",
                'form_subtitle': "Atualize os campos abaixo para editar a série.",
                'selected_coordinators_json': json.dumps(selected_coordinators, cls=DjangoJSONEncoder),
                'selected_directors_json': json.dumps(selected_directors, cls=DjangoJSONEncoder),
                'selected_colaborators_json': json.dumps(selected_colaborators, cls=DjangoJSONEncoder),
                'current_name': grade_name,
            })

        grade.name = grade_name
        grade.coordinators.set(User.objects.filter(id__in=coord_ids))
        grade.directors.set(User.objects.filter(id__in=dir_ids))
        grade.colaborator.set(User.objects.filter(id__in=colab_ids))
        grade.save()

        grade_url = request.build_absolute_uri(reverse('school:grade_edit', args=[grade.id]))
        notified_users = set()

        if request.user.is_authenticated and request.user.id not in notified_users:
            send_notification(recipients=request.user, title=f"Série Atualizada: {grade.name}", message=f"Você atualizou a série '{grade.name}'.", url=grade_url)
            notified_users.add(request.user.id)
        
        if old_name != grade_name:
            all_involved_ids = old_coordinators.union(old_directors).union(old_colaborators).union(set(coord_ids)).union(set(dir_ids)).union(set(colab_ids))
            for user_id in all_involved_ids:
                if user_id not in notified_users:
                    user = User.objects.get(id=user_id)
                    send_notification(recipients=user, title=f"Nome da Série Alterado: {old_name} para {grade_name}", message=f"A série que você está envolvido, '{old_name}', foi renomeada para '{grade.name}'.", url=grade_url)
                    notified_users.add(user_id)

        current_coordinators = set(coord_ids)
        current_directors = set(dir_ids)
        current_colaborators = set(colab_ids)

        added_coordinators = current_coordinators - old_coordinators
        for user_id in added_coordinators:
            if user_id not in notified_users:
                user = User.objects.get(id=user_id)
                send_notification(recipients=user, title=f"Nova Atribuição: Coordenador em '{grade.name}'", message=f"Você foi adicionado como Coordenador da série '{grade.name}'.", url=grade_url)
                notified_users.add(user_id)
        
        removed_coordinators = old_coordinators - current_coordinators
        for user_id in removed_coordinators:
            if user_id not in notified_users:
                user = User.objects.get(id=user_id)
                send_notification(recipients=user, title=f"Atribuição Removida: Coordenador em '{grade.name}'", message=f"Você foi removido como Coordenador da série '{grade.name}'.", url=grade_url)
                notified_users.add(user_id)
        
        added_directors = current_directors - old_directors
        for user_id in added_directors:
            if user_id not in notified_users:
                user = User.objects.get(id=user_id)
                send_notification(recipients=user, title=f"Nova Atribuição: Diretor em '{grade.name}'", message=f"Você foi adicionado como Diretor da série '{grade.name}'.", url=grade_url)
                notified_users.add(user_id)
        
        removed_directors = old_directors - current_directors
        for user_id in removed_directors:
            if user_id not in notified_users:
                user = User.objects.get(id=user_id)
                send_notification(recipients=user, title=f"Atribuição Removida: Diretor em '{grade.name}'", message=f"Você foi removido como Diretor da série '{grade.name}'.", url=grade_url)
                notified_users.add(user_id)

        added_colaborators = current_colaborators - old_colaborators
        for user_id in added_colaborators:
            if user_id not in notified_users:
                user = User.objects.get(id=user_id)
                send_notification(recipients=user, title=f"Nova Atribuição: Colaborador em '{grade.name}'", message=f"Você foi adicionado como Colaborador da série '{grade.name}'.", url=grade_url)
                notified_users.add(user_id)
        
        removed_colaborators = old_colaborators - current_colaborators
        for user_id in removed_colaborators:
            if user_id not in notified_users:
                user = User.objects.get(id=user_id)
                send_notification(recipients=user, title=f"Atribuição Removida: Colaborador em '{grade.name}'", message=f"Você foi removido como Colaborador da série '{grade.name}'.", url=grade_url)
                notified_users.add(user_id)

        messages.success(request, f"Série '{grade.name}' atualizada com sucesso.")
        return redirect('school:grade_list')

    selected_coordinators = list(grade.coordinators.all().values('id', 'username', 'first_name', 'last_name'))
    selected_directors = list(grade.directors.all().values('id', 'username', 'first_name', 'last_name'))
    selected_colaborators = list(grade.colaborator.all().values('id', 'username', 'first_name', 'last_name')) if hasattr(grade, 'colaborator') else []

    return render(request, 'dashboard/grades/form.html', {
        'grade': grade, 'users': users_json, 'form_title': f"Editar Série: {grade.name}",
        'form_subtitle': "Atualize os campos abaixo para editar a série.",
        'selected_coordinators_json': json.dumps(selected_coordinators, cls=DjangoJSONEncoder),
        'selected_directors_json': json.dumps(selected_directors, cls=DjangoJSONEncoder),
        'selected_colaborators_json': json.dumps(selected_colaborators, cls=DjangoJSONEncoder),
    })

@login_required
@role_required(["Diretor"])
def grade_delete(request, grade_id):
    grade = get_object_or_404(Grade, id=grade_id)
    grade_name = grade.name
    
    involved_users_ids = set()
    involved_users_ids.update(grade.coordinators.all().values_list('id', flat=True))
    involved_users_ids.update(grade.directors.all().values_list('id', flat=True))
    if hasattr(grade, 'colaborator'):
        involved_users_ids.update(grade.colaborator.all().values_list('id', flat=True))

    if request.method == "POST":
        grade.delete()
        
        if request.user.is_authenticated:
            send_notification(recipients=request.user, title=f"Série Excluída: {grade_name}", message=f"Você excluiu a série '{grade_name}'.", url=reverse('school:grade_list'))
        
        for user_id in involved_users_ids:
            if user_id != request.user.id:
                user = User.objects.get(id=user_id)
                send_notification(recipients=user, title=f"Série Removida: {grade_name}", message=f"A série '{grade_name}' da qual você fazia parte foi removida do sistema.", url=reverse('school:grade_list'))

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f'Série "{grade_name}" excluída com sucesso.'})
        messages.success(request, f'Série "{grade_name}" excluída com sucesso.')
    return redirect('school:grade_list')


# --- VIEWS DE CLASSE (TURMA) - COM NOTIFICAÇÕES MELHORADAS ---



@login_required
@role_required(["Diretor", "Coordenador", "Professor"])
def class_list(request):
    name = request.GET.get('name', '').strip()
    grade_id = request.GET.get('grade', '')
    academic_year = request.GET.get('academic_year', '').strip()

    classes_qs = Class.objects.select_related('grade').prefetch_related('teachers').order_by('name')

    if name:
        classes_qs = classes_qs.filter(name__icontains=name)
    if grade_id:
        classes_qs = classes_qs.filter(grade_id=grade_id)
    if academic_year:
        classes_qs = classes_qs.filter(academic_year=academic_year)

    # Anotações para contagem de alunos e outros usuários
    classes_qs = classes_qs.annotate(
        student_count=Count('students', distinct=True),  # Ajuste 'students' para o related_name correto
    )

    grades = Grade.objects.all().order_by('name')
    years = Class.objects.values_list('academic_year', flat=True).distinct().order_by('-academic_year')

    paginator = Paginator(classes_qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'dashboard/classes/list.html', {
        'classes': page_obj.object_list,
        'page_obj': page_obj,
        'grades': grades,
        'years': years,
        'current_name': name,
        'current_grade': grade_id,
        'current_year': academic_year,
        
    })

@login_required
@role_required(["Diretor", "Coordenador"])
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
                'grades': grades, 'teachers': teachers, 'current_name': name,
                'current_grade': grade_id, 'current_teachers': teacher_ids,
                'current_academic_year': academic_year, 'current_is_regular': is_regular,
                'form_title': "Nova Turma"
            })

        turma = Class.objects.create(
            name=name,
            grade_id=grade_id,
            academic_year=academic_year,
            is_regular=is_regular
        )
        turma.teachers.set(User.objects.filter(id__in=teacher_ids))
        turma.save()

        # --- NOTIFICAÇÕES PARA CRIAÇÃO DE TURMA ---
        class_url = request.build_absolute_uri(reverse('school:class_edit', args=[turma.id]))
        notified_users = set()

        # 1. Notificar o usuário que criou a turma
        if request.user.is_authenticated and request.user.id not in notified_users:
            send_notification(recipients=request.user, title=f"Turma Criada: {turma.name}", message=f"Você criou a nova turma '{turma.name}' na série '{turma.grade.name}'.", url=class_url)
            notified_users.add(request.user.id)

        # 2. Notificar professores atribuídos
        for teacher in turma.teachers.all():
            if teacher.id not in notified_users:
                send_notification(recipients=teacher, title=f"Nova Atribuição: Turma '{turma.name}'", message=f"Você foi atribuído como professor na turma '{turma.name}' ({turma.grade.name}).", url=class_url)
                notified_users.add(teacher.id)
        
        # 3. Notificar Diretores e Coordenadores da SÉRIE associada à turma
        # Se a turma tiver uma série associada (que é o esperado)
        if turma.grade:
            # Pega todos os usuários (diretores, coordenadores, colaboradores) da série desta turma
            grade_roles = ['coordinators', 'directors', 'colaborator']
            for role_type in grade_roles:
                for user in get_users_by_role_in_grade(turma.grade, role_type):
                    if user.id not in notified_users and user != request.user: # Não notifica o próprio usuário novamente
                        send_notification(
                            recipients=user,
                            title=f"Nova Turma Criada: {turma.name}",
                            message=f"Uma nova turma '{turma.name}' foi criada na série '{turma.grade.name}'.",
                            url=class_url
                        )
                        notified_users.add(user.id)
        # --- FIM DAS NOTIFICAÇÕES ---

        messages.success(request, f"Turma '{turma.name}' criada com sucesso.")
        return redirect('school:class_list')

    return render(request, 'dashboard/classes/form.html', {
        'grades': grades, 'teachers': teachers, 'form_title': "Nova Turma"
    })

@login_required
@role_required(["Diretor"])
def class_edit(request, class_id):
    turma = get_object_or_404(Class, id=class_id)
    grades = Grade.objects.all()
    teachers = get_teacher_users()

    old_teachers = set(turma.teachers.all().values_list('id', flat=True))
    old_name = turma.name
    old_grade = turma.grade # Captura o objeto Grade antigo
    old_academic_year = turma.academic_year
    old_is_regular = turma.is_regular

    if request.method == "POST":
        name = request.POST.get('name', '').strip()
        grade_id = request.POST.get('grade')
        teacher_ids = [int(i) for i in request.POST.getlist('teachers')]
        academic_year = int(request.POST.get('academic_year', turma.academic_year)) # Converte para int
        is_regular = bool(request.POST.get('is_regular', False))

        if not name or not grade_id:
            messages.error(request, "Nome da turma e série são obrigatórios.")
            return render(request, 'dashboard/classes/form.html', {
                'turma': turma, 'grades': grades, 'teachers': teachers,
                'current_name': name, 'current_grade': grade_id,
                'current_teachers': [str(t_id) for t_id in teacher_ids],
                'current_academic_year': academic_year, 'current_is_regular': is_regular,
                'form_title': f"Editar Turma: {turma.name}"
            })

        turma.name = name
        turma.grade_id = grade_id
        turma.academic_year = academic_year
        turma.is_regular = is_regular
        turma.teachers.set(User.objects.filter(id__in=teacher_ids))
        turma.save()

        # --- NOTIFICAÇÕES PARA EDIÇÃO DE TURMA ---
        class_url = request.build_absolute_uri(reverse('school:class_edit', args=[turma.id]))
        notified_users = set()

        # 1. Notificar o usuário que editou a turma
        if request.user.is_authenticated and request.user.id not in notified_users:
            send_notification(recipients=request.user, title=f"Turma Atualizada: {turma.name}", message=f"Você atualizou a turma '{turma.name}'.", url=class_url)
            notified_users.add(request.user.id)
        
        # 2. Notificar professores que foram ADICIONADOS ou REMOVIDOS
        current_teachers = set(teacher_ids)
        
        added_teachers = current_teachers - old_teachers
        for user_id in added_teachers:
            if user_id not in notified_users:
                user = User.objects.get(id=user_id)
                send_notification(recipients=user, title=f"Nova Atribuição: Turma '{turma.name}'", message=f"Você foi adicionado como professor na turma '{turma.name}' ({turma.grade.name}).", url=class_url)
                notified_users.add(user_id)
        
        removed_teachers = old_teachers - current_teachers
        for user_id in removed_teachers:
            if user_id not in notified_users:
                user = User.objects.get(id=user_id)
                send_notification(recipients=user, title=f"Atribuição Removida: Turma '{turma.name}'", message=f"Você foi removido como professor da turma '{turma.name}' ({turma.grade.name}).", url=class_url)
                notified_users.add(user_id)

        # 3. Notificar Diretores e Coordenadores da SÉRIE (antiga e nova, se mudou)
        # Reúne todos os diretores/coordenadores/colaboradores da série antiga e da nova série
        users_to_notify_about_grade_change = set()
        
        # Add users from old grade
        if old_grade:
            for role_type in ['coordinators', 'directors', 'colaborator']:
                for user in get_users_by_role_in_grade(old_grade, role_type):
                    users_to_notify_about_grade_change.add(user)
        
        # Add users from current grade
        if turma.grade: # turma.grade já é o objeto Grade atualizado
            for role_type in ['coordinators', 'directors', 'colaborator']:
                for user in get_users_by_role_in_grade(turma.grade, role_type):
                    users_to_notify_about_grade_change.add(user)

        # Notify these users about the change
        if old_name != name: # Notifica se o nome da turma mudou
            message_text = f"O nome da turma '{old_name}' na série '{turma.grade.name}' foi alterado para '{name}'."
        elif old_grade.id != turma.grade.id: # Notifica se a série da turma mudou
            message_text = f"A turma '{name}' foi movida da série '{old_grade.name}' para '{turma.grade.name}'."
        elif old_academic_year != turma.academic_year or old_is_regular != turma.is_regular:
            message_text = f"Detalhes da turma '{turma.name}' (Série: {turma.grade.name}) foram atualizados (Ano Acadêmico ou Regularidade)."
        else:
            message_text = None # Nenhuma mudança que exija notificação específica para diretores/coordenadores

        if message_text:
            for user in users_to_notify_about_grade_change:
                if user.id not in notified_users and user != request.user:
                    send_notification(
                        recipients=user,
                        title=f"Turma Atualizada: {turma.name}",
                        message=message_text,
                        url=class_url
                    )
                    notified_users.add(user.id)
        
        # --- FIM DAS NOTIFICAÇÕES DE EDIÇÃO ---

        messages.success(request, f"Turma '{turma.name}' atualizada com sucesso.")
        return redirect('school:class_list')

    return render(request, 'dashboard/classes/form.html', {
        'turma': turma, 'grades': grades, 'teachers': teachers,
        'current_name': turma.name, 'current_grade': turma.grade_id,
        'current_teachers': list(turma.teachers.values_list('id', flat=True)),
        #'current_teachers': [str(t.id) for t in turma.teachers.all()],
        'current_academic_year': turma.academic_year, 'current_is_regular': turma.is_regular,
        'form_title': f"Editar Turma: {turma.name}"
    })

@login_required
@role_required(["Diretor"])
def class_delete(request, class_id):
    turma = get_object_or_404(Class, id=class_id)
    turma_name = turma.name
    turma_grade_name = turma.grade.name if turma.grade else "Sem Série"
    turma_grade = turma.grade # Captura o objeto Grade antes de deletar

    # Captura os professores envolvidos antes da exclusão
    involved_teachers_ids = set(turma.teachers.all().values_list('id', flat=True))

    # Captura os Diretores/Coordenadores da série da turma
    involved_grade_users = set()
    if turma_grade:
        for role_type in ['coordinators', 'directors', 'colaborator']:
            for user in get_users_by_role_in_grade(turma_grade, role_type):
                involved_grade_users.add(user)

    if request.method == "POST":
        turma.delete()
        
        # --- NOTIFICAÇÕES PARA EXCLUSÃO DE TURMA ---
        notified_users = set()
        # 1. Notificar o usuário que excluiu a turma
        if request.user.is_authenticated and request.user.id not in notified_users:
            send_notification(recipients=request.user, title=f"Turma Excluída: {turma_name}", message=f"Você excluiu a turma '{turma_name}' (Série: {turma_grade_name}).", url=reverse('school:class_list'))
            notified_users.add(request.user.id)
        
        # 2. Notificar todos os professores que estavam envolvidos com a turma excluída
        for user_id in involved_teachers_ids:
            if user_id not in notified_users:
                user = User.objects.get(id=user_id)
                send_notification(recipients=user, title=f"Turma Removida: {turma_name}", message=f"A turma '{turma_name}' (Série: {turma_grade_name}) da qual você era professor foi removida do sistema.", url=reverse('school:class_list'))
                notified_users.add(user_id)

        # 3. Notificar Diretores e Coordenadores da SÉRIE da turma
        for user in involved_grade_users:
            if user.id not in notified_users:
                send_notification(
                    recipients=user,
                    title=f"Turma Removida: {turma_name}",
                    message=f"A turma '{turma_name}' (Série: {turma_grade_name}) da qual você estava envolvido foi removida do sistema.",
                    url=reverse('school:class_list')
                )
                notified_users.add(user.id)
        # --- FIM DAS NOTIFICAÇÕES ---

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f"Turma '{turma_name}' excluída com sucesso."})
        messages.success(request, f"Turma '{turma_name}' excluída com sucesso.")
    return redirect('school:class_list')



def class_users_view(request, class_id):
    turma = get_object_or_404(Class, id=class_id)
    # Alunos da turma
    alunos = turma.students.all()
    # Professores da turma
    professores = turma.teachers.all()
    # Responsáveis dos alunos (evita duplicados)
    responsaveis = set()
    for aluno in alunos:
        responsaveis.update(aluno.parents.all())
    # Outros perfis da série
    coordenadores = turma.grade.coordinators.all()
    diretores = turma.grade.directors.all()
    colaboradores = turma.grade.colaborator.all()
    return render(request, 'dashboard/classes/class_users.html', {
        'turma': turma,
        'alunos': alunos,
        'professores': professores,
        'responsaveis': responsaveis,
        'coordenadores': coordenadores,
        'diretores': diretores,
        'colaboradores': colaboradores,
    })

def class_users_export(request, class_id):
    turma = get_object_or_404(Class, id=class_id)
    alunos = turma.students.all()
    professores = turma.teachers.all()
    responsaveis = set()
    for aluno in alunos:
        responsaveis.update(aluno.parents.all())
    coordenadores = turma.grade.coordinators.all()
    diretores = turma.grade.directors.all()
    colaboradores = turma.grade.colaborator.all()

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename=turma_{turma.id}_usuarios.csv'

    writer = csv.writer(response)
    writer.writerow(['Perfil', 'Nome', 'Email'])

    for aluno in alunos:
        writer.writerow(['Aluno', aluno.user.get_full_name(), aluno.user.email])
    for prof in professores:
        writer.writerow(['Professor', prof.get_full_name(), prof.email])
    for resp in responsaveis:
        writer.writerow(['Responsável', resp.user.get_full_name(), resp.user.email])
    for coord in coordenadores:
        writer.writerow(['Coordenador', coord.get_full_name(), coord.email])
    for dir in diretores:
        writer.writerow(['Diretor', dir.get_full_name(), dir.email])
    for colab in colaboradores:
        writer.writerow(['Colaborador', colab.get_full_name(), colab.email])

    return response