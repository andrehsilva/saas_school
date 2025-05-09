# support/admin.py
from django.contrib import admin
from .models import SupportTicket, SupportMessage


class SupportMessageInline(admin.TabularInline):
    model = SupportMessage
    extra = 1
    readonly_fields = ("author", "created_at")


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "created_by", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("title", "created_by__username")
    inlines = [SupportMessageInline]
    readonly_fields = ("created_by", "created_at")

