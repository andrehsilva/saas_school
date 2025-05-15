from .models import Role, UserRole, Student, Parent, Class, Grade
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib import messages
import csv
from django.http import HttpResponse
from django.contrib.auth import get_user_model

def import_users_view(request):
    if request.method == "POST":
        csv_file = request.FILES.get("csv_file")
        if not csv_file.name.endswith(".csv"):
            messages.error(request, "O arquivo precisa ser .csv")
            return redirect(request.path)

        decoded_file = csv_file.read().decode("utf-8").splitlines()
        reader = csv.DictReader(decoded_file)

        ROLE_MAP = {
            "aluno": "Student",
            "responsavel": "Parent",
            "professor": "Teacher",
            "coordenador": "Coordinator",
            "diretor": "Director",
        }

        created = 0
        errors = []
        
        # Função para criar série baseada no nome da turma
        def get_or_create_grade(class_name):
            """Cria uma série baseada no primeiro caractere numérico da turma"""
            grade_number = ''.join(filter(str.isdigit, class_name))
            if not grade_number:
                raise ValueError(f"Formato inválido para turma: {class_name}")
            grade_name = f"{grade_number}º Ano"
            grade, _ = Grade.objects.get_or_create(name=grade_name)
            return grade

        # Função para criar turma com série associada
        def get_or_create_class(class_name):
            """Cria ou obtém a turma com sua série correspondente"""
            try:
                grade = get_or_create_grade(class_name)
                classe, _ = Class.objects.get_or_create(
                    name=class_name,
                    defaults={'grade': grade, 'is_regular': True}
                )
                return classe
            except ValueError as e:
                return None

        for row_number, row in enumerate(reader, start=2):
            try:
                # Extração de dados
                username = row.get("usuario", "").strip()
                email = row.get("email", "").strip()
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
                user, user_created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'email': email,
                        'first_name': first_name,
                        'last_name': last_name,
                    }
                )
                if user_created:
                    user.set_password(password)
                    user.save()
                    created += 1

                # Atribuição de Papel
                role_name = ROLE_MAP.get(papel)
                if not role_name:
                    errors.append(f"Linha {row_number}: Papel '{papel}' inválido")
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
                                classe = get_or_create_class(class_name)
                                if classe:
                                    student.classes_assigned.add(classe)
                                else:
                                    errors.append(f"Linha {row_number}: Formato inválido para turma '{class_name}'")

                elif papel == "professor":
                    if classe_nome:
                        for class_name in classe_nome.split(';'):
                            class_name = class_name.strip()
                            if class_name:
                                classe = get_or_create_class(class_name)
                                if classe:
                                    # Correção: usar o campo teachers (ManyToMany)
                                    classe.teachers.add(user)
                                else:
                                    errors.append(f"Linha {row_number}: Formato inválido para turma '{class_name}'")

                # Na função de importação:
                elif papel == "coordenador":
                    if classe_nome:
                        for class_name in classe_nome.split(';'):
                            class_name = class_name.strip()
                            try:
                                grade = get_or_create_grade(class_name)
                                grade.coordinators.add(user)  # Campo correto: coordinators (plural)
                            except ValueError as e:
                                errors.append(f"Linha {row_number}: {str(e)}")

                elif papel == "responsavel":
                    parent, _ = Parent.objects.get_or_create(user=user)
                    if filhos_str:
                        for filho_email in filhos_str.split(';'):
                            filho_email = filho_email.strip()
                            if filho_email:
                                filho_user = User.objects.filter(email__iexact=filho_email).first()
                                if filho_user and hasattr(filho_user, 'student'):
                                    parent.children.add(filho_user.student)
                                else:
                                    errors.append(f"Linha {row_number}: Aluno não encontrado com email '{filho_email}'")

            except Exception as e:
                errors.append(f"Linha {row_number}: Erro inesperado - {str(e)}")

        # Exibição dos resultados
        if errors:
            for error in errors:
                messages.error(request, error)
        if created > 0:
            messages.success(request, f"Importação concluída! {created} novos usuários criados.")
        
        return redirect("/admin/auth/user/")

    return render(request, "admin/import_users.html")

def export_users_view(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="usuarios_exportados.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'usuario', 'email', 'nome', 'sobrenome', 
        'papel', 'classe/turma', 'filhos', 'data_cadastro'
    ])

    # Prefetch com select_related para papel
    users = User.objects.all().prefetch_related(
        'student__classes_assigned',
        'parent_profile__children__user',
        'classes_taught',
        'coordinated_grades',
        'roles__role'  # aqui prefetch UserRole com Role para pegar nome do papel
    )

    for user in users:
        main_role = user.roles.first()
        papel = main_role.role.name.lower() if main_role else ''

        classes = []
        filhos = []

        if hasattr(user, 'student'):
            classes = [c.name for c in user.student.classes_assigned.all()]
        elif hasattr(user, 'parent_profile'):
            filhos = [child.user.email for child in user.parent_profile.children.all()]
        elif user.roles.filter(role__name='Teacher').exists():
            classes = [c.name for c in user.classes_taught.all()]
        elif user.roles.filter(role__name='Coordinator').exists():
            classes = [g.name for g in user.coordinated_grades.all()]

        writer.writerow([
            user.username,
            user.email,
            user.first_name,
            user.last_name,
            papel,
            ';'.join(classes),
            ';'.join(filhos),
            user.date_joined.strftime("%Y-%m-%d %H:%M")
        ])

    return response
