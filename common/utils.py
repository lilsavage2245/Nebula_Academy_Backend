# common/utils.py
import string
import random
from django.utils.text import slugify

def generate_unique_slug(instance, value, slug_field_name='slug', max_length=100):
    """
    Generates a unique slug for a model instance.
    
    Parameters:
    - instance: the model instance being saved
    - value: the base string to slugify (e.g., name or title)
    - slug_field_name: the name of the slug field (default is 'slug')
    - max_length: max allowed length for the slug field
    """
    slug = original_slug = slugify(value)[:max_length]
    ModelClass = instance.__class__
    slug_field = slug_field_name

    counter = 2
    while ModelClass.objects.filter(**{slug_field: slug}).exclude(pk=instance.pk).exists():
        suffix = f"-{counter}"
        # Trim slug to ensure it doesn't exceed max_length
        slug = f"{original_slug[:max_length - len(suffix)]}{suffix}"
        counter += 1

    return slug

