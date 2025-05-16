from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.urls import path
from django.contrib.admin import SimpleListFilter
from django.utils.translation import gettext_lazy as _
from .models import Grade, Class, Role, Parent, Student, UserRole, Subject, GradeCoordinator
from .admin_views import import_users_view
from django.utils import timezone
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

class CustomUserAdmin(UserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Informações Pessoais'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Permissões'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups'),
        }),
        (_('Permissões Específicas'), {  # Nova seção adicionada
            'fields': ('user_permissions',),
        }),
        (_('Datas Importantes'), {'fields': ('last_login', 'date_joined')}),
    )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("import-users/", self.admin_site.admin_view(import_users_view), name="import-users"),
        ]
        return custom_urls + urls

# Substitua o UserAdmin padrão pelo CustomUserAdmin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


class GradeCoordinatorInline(admin.TabularInline):
    model = GradeCoordinator
    extra = 1
    fields = ('user', 'role', 'grade', 'start_date', 'end_date')  # Campo grade adicionado
    autocomplete_fields = ['user', 'grade']  # Para busca rápida

@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ('name', 'current_coordinators')
    inlines = [GradeCoordinatorInline]  # Adiciona as designações como inline
    search_fields = ('name',)

    class Meta:
        permissions = [
            ("global_director_access", "Acesso completo de diretor a todas as séries"),
        ]



# Configuração do GradeCoordinatorAdmin

@admin.register(GradeCoordinator)
class GradeCoordinatorAdmin(admin.ModelAdmin):
    list_display = ('user', 'grade', 'role', 'start_date', 'end_date', 'is_active')
    list_filter = ('grade', 'role')
    search_fields = ('user__username', 'grade__name')
    
    def is_active(self, obj):
        today = timezone.now().date()
        return obj.start_date <= today and (obj.end_date is None or obj.end_date >= today)
    is_active.boolean = True

# Turmas (Classes)
@admin.register(Class)
class SchoolClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'grade', 'teachers_count', 'students_count')
    list_filter = ('grade', 'teachers')
    search_fields = ('name', 'grade__name')
    filter_horizontal = ('teachers',)
    autocomplete_fields = ['grade']
    
    def teachers_count(self, obj):
        return obj.teachers.count()
    teachers_count.short_description = _("Qtd. Professores")
    
    def students_count(self, obj):
        return obj.students.count()
    students_count.short_description = _("Qtd. Alunos")

# Alunos e Responsáveis
class ClassFilter(SimpleListFilter):
    title = _('Turma')
    parameter_name = 'class'

    def lookups(self, request, model_admin):
        return Class.objects.values_list('id', 'name')

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(classes_assigned__id=self.value())

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('user', 'classes_list')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    list_filter = (ClassFilter, 'classes_assigned__grade')
    filter_horizontal = ('classes_assigned',)
    
    def classes_list(self, obj):
        return ", ".join([c.name for c in obj.classes_assigned.all()[:3]])
    classes_list.short_description = _("Turmas")

@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ('user', 'children_list')
    search_fields = ('user__username', 'children__user__username')
    filter_horizontal = ('children',)
    
    def children_list(self, obj):
        return ", ".join([child.user.username for child in obj.children.all()[:3]])
    children_list.short_description = _("Filhos")

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('children__user')

# Disciplinas e Papéis
@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'grade', 'teachers_count')
    search_fields = ('name', 'code')
    list_filter = ('grade',)
    filter_horizontal = ('teachers',)
    
    def teachers_count(self, obj):
        return obj.teachers.count()
    teachers_count.short_description = _("Qtd. Professores")

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'can_post')
    list_filter = ('can_post',)
    search_fields = ('name',)

@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')  # Campo corrigido
    list_filter = ('role', 'user__is_staff')
    search_fields = ('user__username', 'role__name')
    verbose_name = _("Papel do Usuário")
    verbose_name_plural = _("Papéis dos Usuários")

    def assignment_date(self, obj):
        """Data de atribuição do papel (se necessário)"""
        # Implemente esta lógica se tiver um campo de data no modelo
        return "N/A"
    assignment_date.short_description = _("Data de Atribuição")


class CustomPermissionAdmin(admin.ModelAdmin):
    list_display = ('name', 'codename', 'content_type')
    list_filter = ('content_type',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        grade_ct = ContentType.objects.get_for_model(Grade)
        return qs.filter(content_type=grade_ct)

admin.site.register(Permission, CustomPermissionAdmin)