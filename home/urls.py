from django.contrib import admin
from django.urls import path,include
from home import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('invetory', views.invetory, name='invetory'),
    path('scanner', views.barcode_scanner_page, name='scanner_page'),
    path('scan-barcode', views.process_barcode, name='scan_barcode'),
    path('menu', views.menu, name='menu'),
    path('cart', views.cart, name='cart'),
    path('process-cart', views.process_cart, name='process_cart'),
    path('order', views.order, name='order'),
    path('waste-analysis', views.waste_analysis, name='waste_analysis'),
    path('update-log', views.update_log, name='update_log'),
    path('add-to-waste', views.add_to_waste, name='add_to_waste'),
]