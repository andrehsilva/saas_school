from django.db.models import Q
from books.models import Document
from school.models import Student, Parent, Class, Grade, UserRole


def get_accessible_documents(user):
    roles = UserRole.objects.filter(user=user).select_related('role')
    role_names = [r.role.name.lower() for r in roles]

    documents = Document.objects.filter(target_users=user)

    if 'teacher' in role_names:
        classes = Class.objects.filter(teachers=user)
        grades = Grade.objects.filter(class__in=classes)
        documents |= Document.objects.filter(
            Q(target_classes__in=classes) | Q(target_grades__in=grades)
        )

    elif 'coordinator' in role_names or 'director' in role_names:
        documents |= Document.objects.all()

    student = Student.objects.filter(user=user).first()
    if student:
        classes = student.classes_assigned.all()
        grades = Grade.objects.filter(class__in=classes)
        documents |= Document.objects.filter(
            Q(target_classes__in=classes) |
            Q(target_grades__in=grades) |
            Q(target_users=user)
        )

    parent = Parent.objects.filter(user=user).first()
    if parent:
        children = parent.children.all()
        children_users = [c.user for c in children]
        classes = Class.objects.filter(students__in=children).distinct()
        grades = Grade.objects.filter(class__in=classes)
        documents |= Document.objects.filter(
            Q(target_classes__in=classes) |
            Q(target_grades__in=grades) |
            Q(target_users__in=children_users)
        )

    return documents.distinct()


def has_document_access(user, document):
    if document.target_users.filter(id=user.id).exists():
        return True

    student = Student.objects.filter(user=user).first()
    if student:
        if document.target_classes.filter(students=student).exists():
            return True
        if document.target_grades.filter(class__students=student).exists():
            return True

    parent = Parent.objects.filter(user=user).first()
    if parent:
        children = parent.children.all()
        if document.target_classes.filter(students__in=children).exists():
            return True
        if document.target_grades.filter(class__students__in=children).exists():
            return True

    roles = UserRole.objects.filter(user=user).select_related('role')
    role_names = [r.role.name.lower() for r in roles]

    if 'teacher' in role_names:
        if document.target_classes.filter(teachers=user).exists():
            return True
        if document.target_grades.filter(subjects__teachers=user).exists():
            return True

    if 'coordinator' in role_names or 'director' in role_names:
        return True

    return False
