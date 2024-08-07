'''
Serializers for recipe APIs
'''
from rest_framework import serializers

from core.models import Recipe


class RecipeSerializers(serializers.ModelSerializer):
    '''Serializers for recipe model'''

    class Meta:
        model = Recipe
        fields = ['id', 'title', 'time_minutes', 'price', 'link']
        read_only_fields = ['id']


class RecipeDetailSerializer(RecipeSerializers):
    '''Serializer for Recipe detail View.'''

    class Meta(RecipeSerializers.Meta):
        fields = RecipeSerializers.Meta.fields = ['description']