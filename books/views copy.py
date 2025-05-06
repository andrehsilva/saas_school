from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.http import FileResponse, Http404, JsonResponse
from django.db.models import Q
from books.models import Document, Category
from school.models import Student, Parent, Class, Grade

@login_required
def my_documents(request):
    user = request.user
    documents = get_accessible_documents(user)
    
    # Filtro por nome (search)
    search_query = request.GET.get('search', '')
    if search_query:
        documents = documents.filter(title__icontains=search_query)
    
    # Filtro por categoria
    category_id = request.GET.get('category', '')
    if category_id:
        documents = documents.filter(categories__id=category_id)
    
    # Obter todas as categorias disponíveis nos documentos acessíveis
    accessible_categories = Category.objects.filter(document__in=documents).distinct()
    
    return render(request, 'books/my_documents.html', {
        'documents': documents,
        'is_parent': hasattr(user, 'parent'),
        'search_query': search_query,
        'categories': accessible_categories,
        'selected_category': int(category_id) if category_id.isdigit() else None
    })

def get_accessible_documents(user):
    """
    Retorna todos os documentos acessíveis pelo usuário (aluno ou pai)
    """
    # Verificar se o usuário é um estudante
    student = Student.objects.filter(user=user).first()

    # Se não for estudante, verificar se é pai/mãe
    if not student:
        parent = Parent.objects.filter(user=user).first()
        if parent:
            students = parent.children.all()  # Filhos do responsável
            student_users = [s.user for s in students]  # Lista de objetos User dos filhos
        else:
            students = Student.objects.none()
            student_users = []
    else:
        students = [student]
        student_users = [user]

    # Buscar turmas e séries associadas
    user_classes = Class.objects.filter(students__in=students).distinct()
    user_grades = Grade.objects.filter(class__in=user_classes).distinct()

    # Documentos direcionados ao usuário ou aos seus filhos
    direct_documents = Document.objects.filter(
        Q(target_users=user) | 
        Q(target_users__in=student_users)  # Corrigido para usar __in com lista de Users
    )

    # Documentos direcionados às turmas e séries
    class_documents = Document.objects.filter(target_classes__in=user_classes)
    grade_documents = Document.objects.filter(target_grades__in=user_grades)

    # Combinar todos os documentos sem duplicatas
    return (
        direct_documents | 
        class_documents | 
        grade_documents
    ).distinct().order_by('-uploaded_at')

@login_required
def view_pdf(request, doc_id):
    """
    Visualização do PDF com verificação de permissões
    """
    doc = get_object_or_404(Document, id=doc_id)
    user = request.user

    if not has_document_access(user, doc):
        raise Http404("Você não tem permissão para acessar este documento.")

    try:
        # Tenta abrir o arquivo em modo binário
        file = doc.file.open('rb')
        response = FileResponse(file, content_type='application/pdf')
        
        # Configura para abrir inline (no navegador) com o nome do arquivo
        response['Content-Disposition'] = f'inline; filename="{doc.file.name}"'
        return response
        
    except Exception as e:
        raise Http404(f"Erro ao abrir o documento: {str(e)}")

def has_document_access(user, document):
    """
    Verifica se o usuário tem acesso ao documento
    """
    # Acesso direto ao usuário
    if document.target_users.filter(id=user.id).exists():
        return True

    # Verifica se é aluno com acesso via turma/série
    student = Student.objects.filter(user=user).first()
    if student:
        if document.target_classes.filter(students=student).exists():
            return True
        if document.target_grades.filter(class__students=student).exists():
            return True

    # Verifica se é pai/mãe com acesso via turma/série dos filhos
    try:
        parent = Parent.objects.get(user=user)
        students = parent.children.all()
        
        if document.target_classes.filter(students__in=students).exists():
            return True
        if document.target_grades.filter(class__students__in=students).exists():
            return True
            
    except Parent.DoesNotExist:
        pass

    return False

@login_required
def document_info(request, doc_id):
    """
    Retorna informações do documento para o modal (AJAX)
    """
    doc = get_object_or_404(Document, id=doc_id)
    
    if not has_document_access(request.user, doc):
        return JsonResponse({'error': 'Acesso negado'}, status=403)

    data = {
        'id': doc.id,
        'title': doc.title,
        'description': doc.description,
        'uploaded_at': doc.uploaded_at.strftime("%d/%m/%Y %H:%M"),
        'categories': [cat.name for cat in doc.categories.all()],
        'target_classes': [cls.name for cls in doc.target_classes.all()],
        'target_grades': [grade.name for grade in doc.target_grades.all()],
        'pdf_url': doc.file.url
    }
    
    return JsonResponse(data)

@login_required
def view_pdf(request, doc_id):
    doc = get_object_or_404(Document, id=doc_id)
    
    if not has_document_access(request.user, doc):
        raise Http404("Você não tem permissão para acessar este documento.")

    # Retorna o template do modal em vez do PDF diretamente
    return render(request, 'books/pdf_modal.html', {
        'document': doc,
        'pdf_url': doc.file.url
    })