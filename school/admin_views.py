from django.contrib import admin, messages
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils import timezone
import csv
from .models import Role, UserRole, Student, Parent, Class, Grade, Subject

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

                if not all([username, email, password]):
                    errors.append(f"Linha {row_number}: Campos obrigatórios faltando")
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
                else:
                    total_updated += 1

                role_name = ROLE_MAP.get(papel)
                if not role_name:
                    errors.append(f"Linha {row_number}: Papel inválido '{papel}'")
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
                            except Grade.DoesNotExist:
                                errors.append(f"Linha {row_number}: Série '{grade_name}' não encontrada.")

                elif papel == "responsavel":
                    parent, _ = Parent.objects.get_or_create(user=user)
                    if filhos_str:
                        for filho_email in filhos_str.split(';'):
                            filho_email = filho_email.strip()
                            try:
                                filho_user = User.objects.get(email=filho_email)
                                filho_student = Student.objects.get(user=filho_user)
                                parent.children.add(filho_student)
                            except (User.DoesNotExist, Student.DoesNotExist):
                                errors.append(f"Linha {row_number}: Filho com email '{filho_email}' não encontrado.")

            except IntegrityError as e:
                errors.append(f"Linha {row_number}: Usuário duplicado - {str(e)}")
            except Exception as e:
                errors.append(f"Linha {row_number}: Erro inesperado - {str(e)}")

        if total_created or total_updated:
            messages.success(request, f"Importação concluída: {total_created} novos, {total_updated} atualizados")
        if errors:
            for error in errors[:10]:
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
        main_role = user.roles.first().role.name if user.roles.exists() else ''

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
