from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.urls import path, reverse
from django.utils.html import format_html
from django.http import HttpResponseRedirect
from django.db.models import Count

from .models import (
    Role,
    UserRole,
    Grade,
    Class,
    Student,
    Parent,
    Subject,
)
from .admin_views import import_users_view, export_users_view

# —————————————————————————————————————————————
# 1) Registre seu Role ANTES de usá‑lo em autocomplete_fields
# —————————————————————————————————————————————
@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display    = ('name', 'description', 'can_post')
    search_fields   = ('name',)
    ordering        = ('name',)


# —————————————————————————————————————————————
# 2) Inlines para o UserAdmin
# —————————————————————————————————————————————
class UserRoleInline(admin.TabularInline):
    model = UserRole
    extra = 0
    autocomplete_fields = ['role']  # agora funciona sem erro


class StudentInline(admin.StackedInline):
    model = Student
    fk_name = 'user'
    extra = 0
    max_num = 1
    filter_horizontal = ['classes_assigned']


class ParentInline(admin.StackedInline):
    model = Parent
    fk_name = 'user'
    extra = 0
    max_num = 1
    filter_horizontal = ['children']


# —————————————————————————————————————————————
# 3) Custom UserAdmin com botões Import/Export
# —————————————————————————————————————————————
class CustomUserAdmin(BaseUserAdmin):
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'import-users/',
                self.admin_site.admin_view(import_users_view),
                name='import-users'
            ),
            path(
                'export-users/',
                self.admin_site.admin_view(export_users_view),
                name='export-users'
            ),
        ]
        return custom_urls + urls

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context.update({
            'has_import_export': True,
            'import_url': reverse('admin:import-users'),
            'export_url': reverse('admin:export-users')
        })
        return super().changelist_view(request, extra_context=extra_context)

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


# —————————————————————————————————————————————
# 4) Admins dos demais modelos
# —————————————————————————————————————————————
@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display        = ('user', 'role')
    list_filter         = ('role',)
    autocomplete_fields = ['user', 'role']
    search_fields       = ('user__username', 'role__name')
    list_select_related = ('user', 'role')


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display        = ('name', 'coordinators_count', 'directors_count', 'colaborator_count')
    filter_horizontal   = ('coordinators', 'directors', 'colaborator')
    search_fields       = ('name',)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _coordinators = Count('coordinators'),
            _directors    = Count('directors'),
            _colaborators = Count('colaborator'),
        )

    def coordinators_count(self, obj): return obj._coordinators
    def directors_count(self,   obj): return obj._directors
    def colaborator_count(self,  obj): return obj._colaborators

    coordinators_count.admin_order_field = '_coordinators'
    directors_count.admin_order_field    = '_directors'
    colaborator_count.admin_order_field  = '_colaborators'

    coordinators_count.short_description = "Coordenadores"
    directors_count.short_description    = "Diretores"
    colaborator_count.short_description  = "Colaboradores"


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display        = ('name', 'grade', 'academic_year', 'is_regular', 'teachers_count')
    list_filter         = ('grade', 'academic_year', 'is_regular')
    filter_horizontal   = ('teachers',)
    autocomplete_fields = ['grade']
    search_fields       = ('name', 'grade__name')
    list_select_related = ('grade',)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _teachers = Count('teachers')
        )
    def teachers_count(self, obj): return obj._teachers

    teachers_count.admin_order_field = '_teachers'
    teachers_count.short_description    = "Professores"


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display        = ('user', 'classes_count')
    raw_id_fields       = ('user',)
    filter_horizontal   = ('classes_assigned',)
    search_fields       = ('user__username',)
    list_select_related = ('user',)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _classes = Count('classes_assigned')
        )
    def classes_count(self, obj): return obj._classes

    classes_count.admin_order_field = '_classes'
    classes_count.short_description    = "Turmas"


@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display        = ('user', 'children_list')
    raw_id_fields       = ('user',)
    filter_horizontal   = ('children',)
    search_fields       = ('user__username', 'children__user__username')
    list_select_related = ('user',)

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('children__user')
    def children_list(self, obj):
        return ", ".join([c.user.username for c in obj.children.all()])

    children_list.short_description = "Filhos"



@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)