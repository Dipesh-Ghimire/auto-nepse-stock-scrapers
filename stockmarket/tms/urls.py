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
    path("api/open-order/", views.fetch_open_orders, name="fetch_open_orders"),
    path("api/completed-order/", views.fetch_completed_orders, name="fetch_completed_orders"),
    # path("cancel-orderbook/", views.cancel_order_book, name="cancel_order_book"),
]
