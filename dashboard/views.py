from django.contrib.auth.decorators import login_required
from .permissions import dashboard_access_required, role_required  # ajuste o nome se for diferente
from school.models import Grade, Class, Student, Parent, Subject, UserRole, Role
from message.models import Message, Event
from django.contrib import messages
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils import timezone
import csv



@role_required(["Diretor", "Coordenador", "Professor"])
def dashboard_home(request):
    user = request.user
    

    user_roles = user.roles.values_list('role__name', flat=True)
    context = {
        'is_director': 'Diretor' in user_roles,
        'is_coordinator': 'Coordenador' in user_roles,
        'is_teacher': 'Professor' in user_roles,
        'is_collaborator': 'Colaborador' in user_roles,
        'total_grades': Grade.objects.count(),
        'total_classes': Class.objects.count(),
        'total_teachers': UserRole.objects.filter(role__name='Professor').count(),
        'total_students': Student.objects.count(),
        'total_parents': Parent.objects.count(),
        'total_grades': Grade.objects.count(),
        'total_subjects': Subject.objects.count(),
        'total_messages': Message.objects.count(),
        'total_events': Event.objects.count(),
        'my_posts': 0,  # Substitua conforme seu modelo de post
        'published_documents': 0,  # Substitua conforme seu modelo de documento
    }
    return render(request, "dashboard/home.html", context)



### import e Export
@role_required(["Diretor", "Coordenador"])
def dashboard_import_users(request):
    actions = []
    if request.method == "POST":
        csv_file = request.FILES.get("csv_file")
        if not csv_file or not csv_file.name.endswith(".csv"):
            messages.error(request, "Selecione um arquivo CSV válido")
            return redirect(request.path)

        decoded_file = csv_file.read().decode("utf-8").splitlines()
        reader = csv.DictReader(decoded_file)

        ROLE_MAP = {
            "aluno": "Aluno",
            "responsavel": "Responsável",
            "professor": "Professor",
            "coordenador": "Coordenador",
            "diretor": "Diretor",
            "colaborador": "Colaborador"
        }

        total_created = 0
        total_updated = 0
        errors = []

        def get_or_create_grade(class_name):
            grade_number = ''.join(filter(str.isdigit, class_name.split()[0]))
            if not grade_number:
                raise ValueError(f"Formato inválido para turma: {class_name}")
            grade_name = f"{grade_number}º Ano"
            grade, _ = Grade.objects.get_or_create(name=grade_name)
            return grade

        def get_or_create_class(class_name):
            try:
                grade = get_or_create_grade(class_name)
                class_obj, _ = Class.objects.get_or_create(
                    name=class_name,
                    grade=grade,
                    defaults={'is_regular': True, 'academic_year': timezone.now().year}
                )
                return class_obj
            except Exception as e:
                raise ValueError(f"Erro ao processar turma: {str(e)}")

        for row_number, row in enumerate(reader, start=2):
            try:
                username = row.get("usuario", "").strip()
                email = row.get("email", "").strip().lower()
                first_name = row.get("nome", "").strip()
                last_name = row.get("sobrenome", "").strip()
                password = row.get("senha", "").strip()
                papel = row.get("papel", "").strip().lower()
                classe_nome = row.get("classe", "").strip()
                serie_nome = row.get("serie", "").strip()
                filhos_str = row.get("filhos", "").strip()

                # NOVO BLOCO: cria série/turma mesmo sem usuário
                if not any([username, email, password, papel]):
                    if serie_nome:
                        grade, created = Grade.objects.get_or_create(name=serie_nome)
                        if created:
                            actions.append(f"Série criada: {serie_nome}")
                    if classe_nome:
                        try:
                            classe = get_or_create_class(classe_nome)
                            actions.append(f"Turma criada: {classe_nome}")
                        except Exception as e:
                            msg = f"Linha {row_number}: {str(e)}"
                            errors.append(msg)
                            actions.append(msg)
                    continue

                if not all([username, email, password]):
                    msg = f"Linha {row_number}: Campos obrigatórios faltando"
                    errors.append(msg)
                    actions.append(msg)
                    continue

                user, created_bool = User.objects.update_or_create(
                    username=username,
                    defaults={
                        'email': email,
                        'first_name': first_name,
                        'last_name': last_name,
                    }
                )

                if created_bool:
                    user.set_password(password)
                    user.save()
                    total_created += 1
                    actions.append(f"Usuário criado: {username}")
                else:
                    total_updated += 1
                    actions.append(f"Usuário atualizado: {username}")

                role_name = ROLE_MAP.get(papel)
                if not role_name:
                    msg = f"Linha {row_number}: Papel inválido '{papel}'"
                    errors.append(msg)
                    actions.append(msg)
                    continue

                role, _ = Role.objects.get_or_create(name=role_name)
                UserRole.objects.get_or_create(user=user, role=role)

                if papel == "aluno":
                    student, _ = Student.objects.get_or_create(user=user)
                    if classe_nome:
                        for class_name in classe_nome.split(';'):
                            class_name = class_name.strip()
                            if class_name:
                                try:
                                    classe = get_or_create_class(class_name)
                                    student.classes_assigned.add(classe)
                                    actions.append(f"Aluno {username} vinculado à turma {class_name}")
                                except ValueError as e:
                                    msg = f"Linha {row_number}: {str(e)}"
                                    errors.append(msg)
                                    actions.append(msg)

                elif papel == "professor":
                    if classe_nome:
                        for class_name in classe_nome.split(';'):
                            class_name = class_name.strip()
                            try:
                                classe = get_or_create_class(class_name)
                                classe.teachers.add(user)
                                actions.append(f"Professor {username} vinculado à turma {class_name}")
                            except ValueError as e:
                                msg = f"Linha {row_number}: {str(e)}"
                                errors.append(msg)
                                actions.append(msg)

                elif papel in ["coordenador", "diretor", "colaborador"]:
                    if serie_nome:
                        for grade_name in serie_nome.split(';'):
                            grade_name = grade_name.strip()
                            try:
                                grade = Grade.objects.get(name__iexact=grade_name)
                                if papel == "coordenador":
                                    grade.coordinators.add(user)
                                elif papel == "diretor":
                                    grade.directors.add(user)
                                elif papel == "colaborador":
                                    grade.colaborator.add(user)
                                actions.append(f"{role_name} {username} vinculado à série {grade_name}")
                            except Grade.DoesNotExist:
                                msg = f"Linha {row_number}: Série '{grade_name}' não encontrada."
                                errors.append(msg)
                                actions.append(msg)

                elif papel == "responsavel":
                    parent, _ = Parent.objects.get_or_create(user=user)
                    if filhos_str:
                        for filho_email in filhos_str.split(';'):
                            filho_email = filho_email.strip()
                            try:
                                filho_user = User.objects.get(email=filho_email)
                                filho_student = Student.objects.get(user=filho_user)
                                parent.children.add(filho_student)
                                actions.append(f"Responsável {username} vinculado ao filho {filho_email}")
                            except (User.DoesNotExist, Student.DoesNotExist):
                                msg = f"Linha {row_number}: Filho com email '{filho_email}' não encontrado."
                                errors.append(msg)
                                actions.append(msg)

            except IntegrityError as e:
                msg = f"Linha {row_number}: Usuário duplicado - {str(e)}"
                errors.append(msg)
                actions.append(msg)
            except Exception as e:
                msg = f"Linha {row_number}: Erro inesperado - {str(e)}"
                errors.append(msg)
                actions.append(msg)

        if total_created or total_updated:
            messages.success(request, f"Importação concluída: {total_created} novos, {total_updated} atualizados")
        if errors:
            for error in errors[:10]:
                messages.error(request, error)

        return render(request, "dashboard/user/import_users.html", {"actions": actions})

    return render(request, "dashboard/user/import_users.html", {"actions": actions})

@role_required(["Diretor", "Coordenador"])
def dashboard_export_users(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="usuarios_exportados.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'usuario', 'email', 'nome', 'sobrenome', 'papel',
        'vinculos', 'filhos', 'ultimo_login'
    ])

    users = User.objects.prefetch_related(
        'roles__role',
        'student__classes_assigned',
        'parent_profile__children__user',
        'classrooms_taught__grade',      # Professores
        'coordinated_grades',            # Coordenadores
        'directed_grades',               # Diretores
        'colaborated_grades'             # Colaboradores
    ).select_related('student', 'parent_profile')

    for user in users:
        # Papel principal
        main_role = user.roles.first().role.name if hasattr(user, 'roles') and user.roles.exists() else ''

        # Vinculos
        vinculos = []
        if main_role == 'Aluno' and hasattr(user, 'student'):
            vinculos = [c.name for c in user.student.classes_assigned.all()]
        elif main_role == 'Professor':
            vinculos = [f"{c.grade.name} - {c.name}" for c in user.classrooms_taught.all()]
        elif main_role == 'Coordenador':
            vinculos = [g.name for g in user.coordinated_grades.all()]
        elif main_role == 'Diretor':
            vinculos = [g.name for g in user.directed_grades.all()]
        elif main_role == 'Colaborador':
            vinculos = [g.name for g in user.colaborated_grades.all()]

        # Filhos
        filhos = []
        if hasattr(user, 'parent_profile'):
            filhos = [child.user.email for child in user.parent_profile.children.all()]

        writer.writerow([
            user.username,
            user.email,
            user.first_name,
            user.last_name,
            main_role,
            ';'.join(vinculos),
            ';'.join(filhos),
            user.last_login.strftime("%d/%m/%Y %H:%M") if user.last_login else ''
        ])

    return response