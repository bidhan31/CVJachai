from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse
from .models import Profile

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'location', 'profession', 'company_name')
    search_fields = ('user__username', 'user__email', 'location', 'profession')
    list_filter = ('profession',)

# Customize User Admin to add a direct Delete button
admin.site.unregister(User)

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'delete_button')

    class Media:
        css = {
            'all': ('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css',)
        }

    def delete_button(self, obj):
        # Only show for non-superusers or allow for all if owner desires
        # Here we point to the confirmation page for deleting the user
        url = reverse('admin:auth_user_delete', args=[obj.pk])
        return format_html(
            '<a href="{}" style="color: #ef4444; font-weight: bold; text-decoration: none;"><i class="fas fa-trash"></i> Delete</a>',
            url
        )
    
    delete_button.short_description = 'Actions'
    delete_button.allow_tags = True
