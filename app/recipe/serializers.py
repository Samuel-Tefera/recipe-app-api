'''
Serializers for recipe APIs
'''
from rest_framework import serializers

from core.models import Recipe


class RecipeSerializers(serializers.ModelSerializer):
    '''Serializers for recipe model'''

    class Meta:
        model = Recipe
        fields = ['id', 'title', 'time_minutes', 'price', 'description']
        read_only_fields = ['id']
        