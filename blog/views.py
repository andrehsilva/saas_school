from django.shortcuts import render
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.core.paginator import Paginator

from django.db.models import Q
from blog.models import Blog, Category
from .models import CallToAction
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .forms import BlogForm, CategoryForm




class ListBlog(ListView):
    template_name = 'blog.html'
    model = Blog
    context_object_name = 'blog'
    paginate_by = 9

    def get_queryset(self):
        queryset = super().get_queryset().filter(active=True).order_by('-created') # Apenas posts ativos
        search_query = self.request.GET.get('search_query', '')
        category_id = self.request.GET.get('category', '')

        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query)
            )

        if category_id:
            queryset = queryset.filter(categories__id=category_id)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['selected_category'] = self.request.GET.get('category', '')
        context['search_query'] = self.request.GET.get('search_query', '')
        context['blog_latest'] = Blog.objects.filter(star=True, active=True).order_by('-created')[:3]
        context['no_results'] = not context['blog'].exists()
        cta = CallToAction.objects.filter(active=True).last()
        if cta:
            context['cta'] = cta  # Apenas adiciona se existir
        return context
        
    

    
class ArticleDetailView(DetailView):
    model = Blog
    template_name = 'article.html'
    context_object_name = 'article'
    




############dashboard


from django.shortcuts import render
from .models import Blog, Category

def dashboard_blog_list(request):
    search = request.GET.get('q', '')
    category_id = request.GET.get('category', '')
    active = request.GET.get('active', '')

    posts = Blog.objects.all().order_by('-created')

    if search:
        posts = posts.filter(name__icontains=search)

    if category_id:
        posts = posts.filter(categories__id=category_id)

    if active == '1':
        posts = posts.filter(active=True)
    elif active == '0':
        posts = posts.filter(active=False)

    from django.core.paginator import Paginator
    paginator = Paginator(posts, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    categories = Category.objects.all()

    context = {
        'page_obj': page_obj,
        'search': search,
        'categories': categories,
        'current_category': category_id,
        'current_active': active,
    }
    return render(request, 'dashboard/blog/list.html', context)

@login_required
def dashboard_blog_create(request):
    if request.method == 'POST':
        # Corrige checkboxes: se não vierem, define como False
        post_data = request.POST.copy()
        if 'star' not in post_data:
            post_data['star'] = False
        if 'active' not in post_data:
            post_data['active'] = False

        form = BlogForm(post_data, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.owner = request.user
            post.save()
            form.save_m2m()  # Salva categorias
            messages.success(request, 'Postagem criada com sucesso!')
            return redirect('blog:dashboard_blog_list')
        else:
            messages.error(request, 'Corrija os erros abaixo.')
        selected_categories = post_data.getlist('categories')
    else:
        form = BlogForm()
        selected_categories = []
    return render(request, 'dashboard/blog/form.html', {
        'form': form,
        'form_title': 'Nova Postagem',
        'selected_categories': selected_categories,
    })

@login_required
def dashboard_blog_edit(request, pk):
    post = get_object_or_404(Blog, pk=pk)
    if request.method == 'POST':
        post_data = request.POST.copy()
        if 'star' not in post_data:
            post_data['star'] = False
        if 'active' not in post_data:
            post_data['active'] = False

        form = BlogForm(post_data, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, 'Postagem atualizada com sucesso!')
            return redirect('blog:dashboard_blog_list')
        else:
            messages.error(request, 'Corrija os erros abaixo.')
        selected_categories = post_data.getlist('categories')
    else:
        form = BlogForm(instance=post)
        selected_categories = [str(cat.id) for cat in post.categories.all()]
    return render(request, 'dashboard/blog/form.html', {
        'form': form,
        'form_title': 'Editar Postagem',
        'selected_categories': selected_categories,
    })

@login_required
def dashboard_blog_delete(request, pk):
    post = get_object_or_404(Blog, pk=pk)
    if request.method == "POST" and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        post.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)

@login_required
def dashboard_blog_detail(request, pk):
    post = get_object_or_404(Blog, pk=pk)
    return render(request, 'dashboard/blog/detail.html', {'post': post})





############ dashboard categoria
@login_required
def dashboard_category_list(request):
    search = request.GET.get('q', '')
    categories = Category.objects.all().order_by('name')
    if search:
        categories = categories.filter(name__icontains=search)
    paginator = Paginator(categories, 20)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'dashboard/blog/category_list.html', {
        'page_obj': page_obj,
        'search': search,
    })

@login_required
def dashboard_category_create(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoria criada com sucesso!')
            return redirect('blog:dashboard_category_list')
    else:
        form = CategoryForm()
    return render(request, 'dashboard/blog/category_form.html', {
        'form': form,
        'form_title': 'Nova Categoria',
    })

@login_required
def dashboard_category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Categoria atualizada com sucesso!')
            return redirect('blog:dashboard_category_list')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'dashboard/blog/category_form.html', {
        'form': form,
        'form_title': 'Editar Categoria',
    })

from django.http import JsonResponse

@login_required
def dashboard_category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == "POST" and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        category.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)