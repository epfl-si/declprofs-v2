from django.db import models


class Documentation(models.Model):

    class Type(models.TextChoices):
        USER = "user"
        BUSINESS = "business"

    type = models.CharField(max_length=20, choices=Type.choices)
    title = models.CharField(max_length=200)
    content = models.TextField()
    order = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
