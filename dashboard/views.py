from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from school.models import Grade, Class, Student, Parent, Subject, UserRole, Role
from django.urls import reverse_lazy


class DashboardHomeView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        user_roles = user.roles.values_list('role__name', flat=True)
        context['is_director'] = 'Diretor' in user_roles
        context['is_coordinator'] = 'Coordenador' in user_roles
        context['is_teacher'] = 'Professor' in user_roles
        context['is_collaborator'] = 'Colaborador' in user_roles

        context['total_classes'] = Class.objects.count()
        context['total_teachers'] = UserRole.objects.filter(role__name='Professor').count()
        context['total_students'] = Student.objects.count()
        context['total_parents'] = Parent.objects.count()
        context['total_grades'] = Grade.objects.count()
        context['total_subjects'] = Subject.objects.count()

        context['my_posts'] = 0  # Substitua conforme seu modelo de post
        context['published_documents'] = 0  # Substitua conforme seu modelo de documento

        return context


from django.shortcuts import render

