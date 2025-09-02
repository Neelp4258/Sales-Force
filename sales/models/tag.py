"""
Tag model for categorization
"""
from django.db import models


class Tag(models.Model):
    """Tag model for categorization"""
    
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=7, default='#4F46E5')
    description = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'
        ordering = ['name']
    
    def __str__(self):
        return self.name