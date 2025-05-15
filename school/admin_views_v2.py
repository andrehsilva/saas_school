from .models import Role, UserRole, Student, Parent, Class
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

        # Mapeamento entre nomes em português e os nomes de Role no banco
        ROLE_MAP = {
            "aluno": "Student",
            "responsavel": "Parent",
            "professor": "Teacher",
            "coordenador": "Coordinator",
            "diretor": "Director",
        }

        created = 0
        for row in reader:
            username = row.get("usuario")
            email = row.get("email")
            first_name = row.get("nome")
            last_name = row.get("sobrenome")
            password = row.get("senha")
            papel = row.get("papel", "").strip().lower()
            classe_nome = row.get("classe")
            filhos_str = row.get("filhos", "")

            if not username or not email or not password:
                continue

            user, created_user = User.objects.get_or_create(username=username, defaults={
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
            })
            if created_user:
                user.set_password(password)
                user.save()
                created += 1

            # Verifica e atribui o papel
            role_name = ROLE_MAP.get(papel)
            role = Role.objects.filter(name=role_name).first() if role_name else None
            if role and not UserRole.objects.filter(user=user, role=role).exists():
                UserRole.objects.create(user=user, role=role)

            # Lógicas específicas para cada papel
            if papel == "aluno":
                student, _ = Student.objects.get_or_create(user=user)
                if classe_nome:
                    classe = Class.objects.filter(name__iexact=classe_nome.strip()).first()
                    if classe:
                        student.classes_assigned.add(classe)

            elif papel == "responsavel":
                parent, _ = Parent.objects.get_or_create(user=user)
                filhos_emails = [f.strip() for f in filhos_str.split(",") if f.strip()]
                for filho_email in filhos_emails:
                    filho_user = User.objects.filter(email__iexact=filho_email).first()
                    if filho_user:
                        aluno = Student.objects.filter(user=filho_user).first()
                        if aluno:
                            parent.children.add(aluno)

            elif papel == "professor":
                if classe_nome:
                    classe = Class.objects.filter(name__iexact=classe_nome.strip()).first()
                    if classe and user not in classe.teachers.all():
                        classe.teachers.add(user)

            # Para coordenador e diretor, nenhuma lógica adicional por enquanto

        messages.success(request, f"{created} usuário(s) importado(s) com sucesso!")
        return redirect("/admin/auth/user/")

    return render(request, "admin/import_users.html")


User = get_user_model()

def export_users_view(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="usuarios.csv"'

    writer = csv.writer(response)
    writer.writerow(['username', 'email', 'first_name', 'last_name'])

    for user in User.objects.all():
        writer.writerow([user.username, user.email, user.first_name, user.last_name])

    return response