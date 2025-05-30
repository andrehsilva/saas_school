from django.shortcuts import render
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.core.paginator import Paginator

from django.db.models import Q
from blog.models import Blog, Category
from .models import CallToAction
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .forms import BlogForm




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


@login_required
def dashboard_blog_list(request):
    search = request.GET.get('q', '')
    posts = Blog.objects.all().order_by('-created')
    if search:
        posts = posts.filter(name__icontains=search)
    paginator = Paginator(posts, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'dashboard/blog/list.html', {
        'page_obj': page_obj,
        'search': search,
    })

@login_required
def dashboard_blog_create(request):
    if request.method == 'POST':
        form = BlogForm(request.POST, request.FILES)
        selected_categories = request.POST.getlist('categories')
    else:
        form = BlogForm()
        selected_categories = []
    return render(request, 'dashboard/blog/form.html', {
        'form': form,
        'form_title': 'Nova Postagem',
        'selected_categories': selected_categories,
    })

def dashboard_blog_edit(request, pk):
    post = get_object_or_404(Blog, pk=pk)
    if request.method == 'POST':
        form = BlogForm(request.POST, request.FILES, instance=post)
        selected_categories = request.POST.getlist('categories')
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
    if request.method == 'POST':
        post.delete()
        messages.success(request, 'Postagem excluída com sucesso!')
        return redirect('blog:dashboard_blog_list')
    return render(request, 'dashboard/blog/confirm_delete.html', {'post': post})

@login_required
def dashboard_blog_detail(request, pk):
    post = get_object_or_404(Blog, pk=pk)
    return render(request, 'dashboard/blog/detail.html', {'post': post})