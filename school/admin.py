from django.contrib import admin
from .models import Role, Series, Class, Parent, Student, UserRole


# Personalizando o admin para o modelo Role
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'can_send_messages')  # Exibindo can_send_messages
    search_fields = ('name', 'description')
    list_filter = ('can_send_messages',)  # Filtro por permissão de envio de mensagens
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'can_send_messages')
        }),
    )

# Personalizando o admin para o modelo Series
class SeriesAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)
    list_filter = ('name',)

# Personalizando o admin para o modelo Class
class ClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'series', 'teacher', 'student_count')
    search_fields = ('name', 'teacher__username', 'series__name')
    list_filter = ('series', 'teacher')
    filter_horizontal = ('students',)

    # Usado para exibir uma lista de alunos em uma classe específica de forma mais organizada
    def teacher_name(self, obj):
        return obj.teacher.username
    teacher_name.short_description = 'Teacher'

    def student_count(self, obj):
        return obj.students.count()  # Corrigido aqui para contar os alunos relacionados
    student_count.short_description = 'Número de alunos na turma'

# Personalizando o admin para o modelo Parent
class ParentAdmin(admin.ModelAdmin):
    list_display = ('user', 'children_count')
    search_fields = ('user__username',)
    
    # Contagem de filhos
    def children_count(self, obj):
        return obj.children.count()
    children_count.short_description = 'Number of Children'

# Personalizando o admin para o modelo Student
class StudentAdmin(admin.ModelAdmin):
    list_display = ('user', 'series', 'class_count')
    search_fields = ('user__username', 'series__name')
    list_filter = ('series',)
    filter_horizontal = ('classes',)

    # Contagem de turmas
    def class_count(self, obj):
        return obj.classes.count()
    class_count.short_description = 'Number of Classes'

# Registrando os modelos no admin
admin.site.register(Role, RoleAdmin)
admin.site.register(Series, SeriesAdmin)
admin.site.register(Class, ClassAdmin)
admin.site.register(Parent, ParentAdmin)
admin.site.register(Student, StudentAdmin)
admin.site.register(UserRole)

