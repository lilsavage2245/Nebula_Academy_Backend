# base.py
from django.db import models

class SoftDeleteModelMixin(models.Model):
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        self.is_active = False
        self.save()
