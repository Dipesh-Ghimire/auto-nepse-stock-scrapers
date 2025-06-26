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
    
    path("api/sell-full-portfolio/", views.sell_full_portfolio, name="sell_full_portfolio"),
    path("api/sell-half-portfolio/", views.sell_half_portfolio, name="sell_half_portfolio"),

    path("tms/portfolio/", views.my_dp_holdings, name="my_dp_holdings"),
    
    path("tms/accounts/", views.tms_account_list, name="tms_account_list"),
    path("tms/accounts/create/", views.tms_account_create, name="tms_account_create"),
    path("tms/accounts/<int:pk>/update/", views.tms_account_update, name="tms_account_update"),
    path("tms/accounts/<int:pk>/delete/", views.tms_account_delete, name="tms_account_delete"),

    path("tms/login/<int:pk>/", views.tms_account_login, name="tms_account_login"),
    path("tms/api/primary-login/", views.tms_primary_login_api, name="tms_primary_login_api"),
]
