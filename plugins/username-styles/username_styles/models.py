
from django.db import models
from misago.users.models import Group

class RoleStyle(models.Model):
    role = models.OneToOneField(
        Group, on_delete=models.CASCADE, related_name='style'
    )
    style_name = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.role.name}: {self.style_name or 'default'}"