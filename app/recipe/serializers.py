'''
Serializers for recipe APIs
'''
from rest_framework import serializers

from core.models import Recipe, Tag


class TagSerializers(serializers.ModelSerializer):
    '''Serializer for tag model.'''

    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id']


class RecipeSerializers(serializers.ModelSerializer):
    '''Serializers for recipe model'''
    tags = TagSerializers(many=True, required=False)

    class Meta:
        model = Recipe
        fields = ['id', 'title', 'time_minutes', 'price', 'link', 'tags']
        read_only_fields = ['id']

    def create(self, validated_data):
        '''Creata a recipe.'''
        tags = validated_data.pop('tags', [])
        recipe = Recipe.objects.create(**validated_data)
        auth_user = self.context['request'].user
        for tag in tags:
            tag_obj, created = Tag.objects.get_or_create(
                user=auth_user,
                **tag,
            )
            recipe.tags.add(tag_obj)
        return recipe


class RecipeDetailSerializer(RecipeSerializers):
    '''Serializer for Recipe detail View.'''

    class Meta(RecipeSerializers.Meta):
        fields = RecipeSerializers.Meta.fields + ['description']
