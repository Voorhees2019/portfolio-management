from django.contrib import admin
from .models import Industry, Technology, Project, Company


@admin.register(Industry)
class IndustryAdmin(admin.ModelAdmin):
    list_display = ("id", "title")
    list_display_links = ("id", "title")
    search_fields = ("title",)
    list_per_page = 25


@admin.register(Technology)
class TechnologyAdmin(admin.ModelAdmin):
    list_display = ("id", "title")
    list_display_links = ("id", "title")
    search_fields = ("title",)
    list_per_page = 25


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "author", "url", "url_is_active", "is_private", "updated_at")
    list_display_links = ("id", "title")
    raw_id_fields = ("industries", "technologies")
    search_fields = ("title", "author")
    list_per_page = 25


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "founder", "website", "email", "slogan")
    list_display_links = ("id", "name")
    search_fields = ("name", "description", "founder", "email", "slogan")
    list_per_page = 25
