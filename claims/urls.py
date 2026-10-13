from django.urls import path
from . import views

app_name = 'claims'

urlpatterns = [
    path('item/<int:item_id>/claim/', views.create_claim_view, name='create'),
    path('claim/<int:pk>/', views.claim_detail_view, name='detail'),
    path('claim/<int:pk>/review/', views.review_claim_view, name='review'),
    path('claim/<int:pk>/verify-otp/', views.verify_otp_view, name='verify_otp'),
    path('claim/<int:pk>/regenerate-otp/', views.regenerate_otp_view, name='regenerate_otp'),
]
