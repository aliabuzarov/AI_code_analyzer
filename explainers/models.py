"""
Models for the explainers app.
"""
from django.db import models


class CodeExplanation(models.Model):
    """Model to store code explanations (optional, for future use)."""
    language = models.CharField(max_length=10)
    code = models.TextField()
    explanation = models.TextField()
    errors = models.TextField()
    improved_code = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

