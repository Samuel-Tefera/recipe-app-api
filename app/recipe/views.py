'''
Views for recipe APIs.
'''

from rest_framework import viewsets, mixins
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import Recipe, Tag, Ingredient
from recipe import serializers


class RecipeViewSets(viewsets.ModelViewSet):
    '''View for manage recipe APIs.'''

    serializer_class = serializers.RecipeDetailSerializer
    queryset = Recipe.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        '''Retrieve recipe for authenticated user.'''
        return self.queryset.filter(user=self.request.user).order_by('-id')

    def get_serializer_class(self):
        '''Return serializer class for request.'''
        if self.action == 'list':
            return serializers.RecipeSerializers

        return self.serializer_class

    def perform_create(self, serializer):
        '''Create a new recipe.'''
        serializer.save(user=self.request.user)


class TagViewSet(mixins.UpdateModelMixin,
                 mixins.ListModelMixin,
                 mixins.DestroyModelMixin,
                 viewsets.GenericViewSet):
    '''Manage tags in the datatbase.'''
    serializer_class = serializers.TagSerializers
    queryset = Tag.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        '''Filter query user for authenticated user.'''
        return self.queryset.filter(user=self.request.user).order_by('-name')


class IngredinetViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    '''Manage ingredients in the database'''
    serializer_class = serializers.IngredientSerializer
    queryset = Ingredient.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user).order_by('-name')
