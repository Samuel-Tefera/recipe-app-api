'''
URL mapping for recipe app.
'''

from django.urls import path, include

from rest_framework.routers import DefaultRouter

from recipe import views

router = DefaultRouter()
router.register('recipe', views.RecipeViewSets)
router.register('tags', views.TagViewSet)
router.register('ingredients', views.IngredinetViewSet)

app_name = 'recipe'

urlpatterns = [
    path('', include(router.urls))
]
