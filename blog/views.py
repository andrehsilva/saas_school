from django.shortcuts import render
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.core.paginator import Paginator
from django.shortcuts import render
from django.db.models import Q
from blog.models import Blog, Category
from .models import CallToAction


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
    

        
