import csv
from django.contrib.auth.models import User

def import_users_from_csv(file_path):
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            username = row['username'].strip()
            email = row['email'].strip()
            first_name = row['first_name'].strip()
            last_name = row['last_name'].strip()
            password = row['password'].strip()

            if User.objects.filter(username=username).exists():
                print(f"Usuário '{username}' já existe. Pulando.")
                continue

            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                password=password
            )
            print(f"Usuário '{username}' criado com sucesso.")

