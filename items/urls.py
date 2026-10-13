from django.urls import path
from . import views

app_name = 'items'

urlpatterns = [
    path('', views.index_view, name='index'),
    path('item/<int:pk>/', views.item_detail_view, name='detail'),
    path('report/', views.item_create_view, name='create'),
    path('item/<int:pk>/edit/', views.item_edit_view, name='edit'),
    path('item/<int:pk>/delete/', views.item_delete_view, name='delete'),
    path('desk/', views.campus_desk_view, name='desk'),
]
