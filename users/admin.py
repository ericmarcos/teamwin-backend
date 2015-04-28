from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import DareyooUserProfile, Device

admin.site.unregister(User)

class DareyooUserProfileInline(admin.StackedInline):
    model = DareyooUserProfile
    fk_name = 'user'

class DeviceInline(admin.StackedInline):
    model = Device

class UserProfileAdmin(UserAdmin):
    inlines = [DareyooUserProfileInline, DeviceInline, ]

admin.site.register(User, UserProfileAdmin)