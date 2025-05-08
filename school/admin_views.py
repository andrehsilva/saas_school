# school/admin_views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
import csv

def import_users_view(request):
    if request.method == "POST":
        csv_file = request.FILES.get("csv_file")
        if not csv_file.name.endswith(".csv"):
            messages.error(request, "O arquivo precisa ser .csv")
            return redirect(request.path)

        decoded_file = csv_file.read().decode("utf-8").splitlines()
        reader = csv.DictReader(decoded_file)

        created = 0
        for row in reader:
            username = row.get("nome_de_usuario")
            email = row.get("email")
            first_name = row.get("nome")
            last_name = row.get("sobrenome")
            password = row.get("senha")
            if username and email and password and first_name and last_name:
                if not User.objects.filter(username=username).exists():
                    User.objects.create_user(username=username, email=email, password=password, first_name=first_name, last_name=last_name)
                    created += 1

        messages.success(request, f"{created} usuário(s) importado(s) com sucesso!")
        return redirect("/admin/auth/user/")

    return render(request, "admin/import_users.html")
