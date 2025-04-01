from django.contrib import admin
from .models import Grade, Class, Role, Parent, Student

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

@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_children')
    search_fields = ('user__username',)

    def get_children(self, obj):
        return ", ".join([child.user.username for child in obj.children.all()])
    get_children.short_description = "Filhos"

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_classes')  # Substitui class_assigned por get_classes
    list_filter = ('classes_assigned',)  # Pode não funcionar, talvez precise de um filtro customizado

    def get_classes(self, obj):
        return ", ".join([c.name for c in obj.classes_assigned.all()])
    get_classes.short_description = "Classes"

