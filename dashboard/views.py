from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from school.models import Class, Student, Role, UserRole
from school.utils import get_user_visibility_context

class DashboardHomeView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        visibility = get_user_visibility_context(user)

        # Flags de papel
        user_roles = set(user.roles.values_list('role__name', flat=True))
        context['is_director'] = 'Diretor' in user_roles
        context['is_coordinator'] = 'Coordenador' in user_roles
        context['is_teacher'] = 'Professor' in user_roles
        context['is_collaborator'] = 'Colaborador' in user_roles

        # Dados dinâmicos
        if context['is_director'] or context['is_coordinator']:
            context['total_classes'] = visibility['user_classes'].count()
            context['total_teachers'] = UserRole.objects.filter(role__name='Professor').count()
        if context['is_teacher'] or context['is_collaborator']:
            # Exemplo: buscar postagens do usuário
            context['my_posts'] = user.post_set.count() if hasattr(user, 'post_set') else 0
        if context['is_director']:
            # Exemplo: buscar documentos publicados
            context['published_documents'] = user.documents_published.count() if hasattr(user, 'documents_published') else 0

        return context