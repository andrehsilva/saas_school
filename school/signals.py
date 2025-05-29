from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import Role, Class, Subject  # Adicione Subject aqui

@receiver(post_migrate)
def create_default_roles(sender, **kwargs):
    if sender.name == 'school':
        default_roles = {
            'Diretor': {'can_post': True, 'description': 'Acesso completo de diretor'},
            'Coordenador': {'can_post': True, 'description': 'Coordenador de série'},
            'Colaborador': {'can_post': True, 'description': 'Colaborador de série e turmas'},
            'Professor': {'can_post': True, 'description': 'Professor da turma'},
            'Responsável': {'can_post': False, 'description': 'Responsável por aluno'},
            'Aluno': {'can_post': False, 'description': 'Estudante'}
        }

        for role_name, config in default_roles.items():
            try:
                role_obj, created = Role.objects.get_or_create(
                    name=role_name,
                    defaults=config
                )
                if not created and (role_obj.can_post != config['can_post'] or role_obj.description != config['description']):
                    role_obj.can_post = config['can_post']
                    role_obj.description = config['description']
                    role_obj.save()
            except Exception as e:
                print(f"Erro ao processar papel {role_name}: {str(e)}")

        # Atualiza valor padrão de classes
        Class.objects.filter(is_regular__isnull=True).update(is_regular=True)

        # Disciplinas padrão
        default_subjects = [
            "Língua Portuguesa", "Literatura", "Matemática", "História", "Geografia", "Ciências",
            "Física", "Química", "Biologia", "Gramática", "Redação", "Filosofia", "Sociologia",
            "Arte", "Educação Física", "Inglês", "Espanhol","Interdisciplinar", "Religião", "Atualidades", "Projetos",
            "Outros Idiomas", "Robótica", "Programação", "Pensamento Computacional", "Educação Financeira",
            "Estatística", "Lógica", "Engenharia Júnior", "Sustentabilidade", "Educação Ambiental",
            "Agroecologia", "Teatro", "Música", "Libras", "Comunicação e Expressão", "Mídias Digitais",
            "Direitos Humanos", "Empreendedorismo", "Cidadania Digital", "Ética e Cidadania",
            "Cultura Afro-brasileira e Indígena", "Projeto de Vida", "Educação Socioemocional",
            "Autoconhecimento", "Inteligência Emocional", "Informática", "Design Gráfico", "Administração",
            "Marketing", "Cultura Maker",  "Xadrez", "Jogos Educativos",
            "Preparatório ENEM", "Tutoria", "Leitura Orientada"
        ]

        for subject_name in default_subjects:
            try:
                Subject.objects.get_or_create(name=subject_name)
            except Exception as e:
                print(f"Erro ao criar disciplina '{subject_name}': {str(e)}")
