from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.urls import path
from .models import Grade, Class, Role, Parent, Student, UserRole, Subject
from .admin_views import import_users_view

from django.contrib.auth.models import User


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Class)
class SchoolClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'grade', 'get_teachers')
    list_filter = ('grade',)
    search_fields = ('name',)

    def get_teachers(self, obj):
        return ", ".join([t.username for t in obj.teachers.all()])
    get_teachers.short_description = "Professores"

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(UserRole)
class RoleUserAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')
    list_filter = ('role',)
    search_fields = ('user__username', 'role__name')
    verbose_name = "Papel do Usuário"
    verbose_name_plural = "Papéis dos Usuários"

@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_children')
    search_fields = ('user__username',)

    def get_children(self, obj):
        return ", ".join([child.user.username for child in obj.children.all()])
    get_children.short_description = "Filhos"

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    list_display = ('user', 'get_classes')  # Substitui class_assigned por get_classes
    list_filter = ('classes_assigned',)  # Pode não funcionar, talvez precise de um filtro customizado

    def get_classes(self, obj):
        return ", ".join([c.name for c in obj.classes_assigned.all()])
    get_classes.short_description = "Classes"


class CustomUserAdmin(UserAdmin):
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("import-users/", self.admin_site.admin_view(import_users_view), name="import-users"),
        ]
        return custom_urls + urls

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'grade')
    search_fields = ('name', 'code')
    list_filter = ('grade',)