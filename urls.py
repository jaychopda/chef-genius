from django.urls import path
from home import views

urlpatterns = [

    # Inventory and scanning
    path('invetory/', views.invetory, name='invetory'),
    path('scan/', views.scan, name='scan'),

    # Cart and menu
    path('menu/', views.menu, name='menu'),
    path('cart/', views.cart, name='cart'),
    path('process-cart/', views.process_cart, name='process_cart'),

    # New pages
    path('dashboard/', views.dashboard, name='dashboard'),
    path('orders/', views.orders, name='orders'),
    path('waste-analysis/', views.waste_analysis, name='waste_analysis'),
    path('menu-optimization/', views.menu_optimization, name='menu_optimization'),
]