from django.urls import path
from . import views

urlpatterns = [
    # Other URL patterns...
    path('tms/', views.tms_login_view, name='tms_login'),
    path('submit-captcha/', views.submit_captcha, name='submit_captcha'),
    path("tms/live/", views.live_market_depth_page, name="live_market_depth_page"),
    path('tms/captcha/', views.tms_captcha_page, name='tms_captcha_page'),
    path("api/live-depth/", views.live_market_depth_view, name="live_market_depth"),
    path("api/place-order/", views.place_order, name="place_order"),
]
