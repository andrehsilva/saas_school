from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils import timezone
import csv
from .models import Role, UserRole, Student, Parent, Class, Grade, Subject

def import_users_view(request):
    # Sua lógica de importação aqui
    return render(request, 'admin/import_users.html')

def export_users_view(request):
    # Sua lógica de exportação aqui
    return HttpResponse(content_type='text/csv')

def import_users_view(request):
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

        created = 0
        updated = 0
        errors = []
        
        def get_or_create_grade(class_name):
            """Cria série baseada no número da turma"""
            grade_number = ''.join(filter(str.isdigit, class_name.split()[0]))
            if not grade_number:
                raise ValueError(f"Formato inválido para turma: {class_name}")
            grade_name = f"{grade_number}º Ano"
            grade, _ = Grade.objects.get_or_create(name=grade_name)
            return grade

        def get_or_create_class(class_name):
            """Cria turma com série associada"""
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
                # Extração e normalização dos dados
                username = row.get("usuario", "").strip()
                email = row.get("email", "").strip().lower()
                first_name = row.get("nome", "").strip()
                last_name = row.get("sobrenome", "").strip()
                password = row.get("senha", "").strip()
                papel = row.get("papel", "").strip().lower()
                classe_nome = row.get("classe", "").strip()
                filhos_str = row.get("filhos", "").strip()

                # Validação básica
                if not all([username, email, password]):
                    errors.append(f"Linha {row_number}: Campos obrigatórios faltando")
                    continue

                # Criação/Atualização do usuário
                user, created = User.objects.update_or_create(
                    username=username,
                    defaults={
                        'email': email,
                        'first_name': first_name,
                        'last_name': last_name,
                    }
                )
                
                if created:
                    user.set_password(password)
                    user.save()
                    created += 1
                else:
                    updated += 1

                # Atribuição de Papel
                role_name = ROLE_MAP.get(papel)
                if not role_name:
                    errors.append(f"Linha {row_number}: Papel inválido '{papel}'")
                    continue
                
                role, _ = Role.objects.get_or_create(name=role_name)
                UserRole.objects.get_or_create(user=user, role=role)

                # Processamento específico por papel
                if papel == "aluno":
                    student, _ = Student.objects.get_or_create(user=user)
                    if classe_nome:
                        for class_name in classe_nome.split(';'):
                            class_name = class_name.strip()
                            if class_name:
                                try:
                                    classe = get_or_create_class(class_name)
                                    student.classes_assigned.add(classe)
                                except ValueError as e:
                                    errors.append(f"Linha {row_number}: {str(e)}")

                elif papel == "professor":
                    if classe_nome:
                        for class_name in classe_nome.split(';'):
                            class_name = class_name.strip()
                            try:
                                classe = get_or_create_class(class_name)
                                classe.teachers.add(user)
                            except ValueError as e:
                                errors.append(f"Linha {row_number}: {str(e)}")

                elif papel in ["coordenador", "diretor", "colaborador"]:
                    if classe_nome:
                        for class_name in classe_nome.split(';'):
                            class_name = class_name.strip()
                            try:
                                grade = get_or_create_grade(class_name)
                                if papel == "coordenador":
                                    grade.coordinators.add(user)
                                elif papel == "diretor":
                                    grade.directors.add(user)
                                elif papel == "colaborador":
                                    grade.colaborador.add(user)
                            except ValueError as e:
                                errors.append(f"Linha {row_number}: {str(e)}")

                elif papel == "responsavel":
                    parent, _ = Parent.objects.get_or_create(user=user)
                    if filhos_str:
                        for filho_email in filhos_str.split(';'):
                            filho_email = filho_email.strip().lower()
                            if filho_email:
                                try:
                                    filho_user = User.objects.get(email__iexact=filho_email)
                                    if hasattr(filho_user, 'student'):
                                        parent.children.add(filho_user.student)
                                    else:
                                        errors.append(f"Linha {row_number}: Usuário {filho_email} não é aluno")
                                except User.DoesNotExist:
                                    errors.append(f"Linha {row_number}: Aluno não encontrado: {filho_email}")

            except IntegrityError as e:
                errors.append(f"Linha {row_number}: Usuário duplicado - {str(e)}")
            except Exception as e:
                errors.append(f"Linha {row_number}: Erro inesperado - {str(e)}")

        # Resultado da importação
        if created or updated:
            msg = f"Importação concluída: {created} novos, {updated} atualizados"
            messages.success(request, msg)
        if errors:
            for error in errors[:10]:  # Mostra apenas os primeiros 10 erros
                messages.error(request, error)

        return redirect("/admin/auth/user/")

    return render(request, "admin/import_users.html")

def export_users_view(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="usuarios_exportados.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'usuario', 'email', 'nome', 'sobrenome', 'papel',
        'vinculos', 'filhos', 'ultimo_login'
    ])

    # Otimização de queries
    users = User.objects.prefetch_related(
        'roles__role',
        'student__classes_assigned',
        'parent_profile__children__user',
        'classes_taught__grade',
        'coordinated_grades',
        'directed_grades',
        'colaborated_grades'
    ).select_related('student', 'parent_profile')

    for user in users:
        # Determinar papel principal
        main_role = user.roles.first().role.name if user.roles.exists() else ''

        # Determinar vínculos
        vinculos = []
        if main_role == 'Aluno':
            vinculos = [c.name for c in user.student.classes_assigned.all()]
        elif main_role == 'Professor':
            vinculos = [f"{c.grade.name} - {c.name}" for c in user.classes_taught.all()]
        elif main_role == 'Coordenador':
            vinculos = [g.name for g in user.coordinated_grades.all()]
        elif main_role == 'Diretor':
            vinculos = [g.name for g in user.directed_grades.all()]
        elif main_role == 'Colaborador':
            vinculos = [g.name for g in user.colaborated_grades.all()]

        # Determinar filhos para responsáveis
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