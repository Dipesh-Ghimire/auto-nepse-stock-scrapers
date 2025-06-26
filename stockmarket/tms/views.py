from decimal import Decimal
from django.shortcuts import render, redirect
from django.http import JsonResponse
import json
import os
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from stockmarket import settings
from .forms import TMSLoginForm
from .selenium_client import SeleniumTMSClient
from .models import TMSAccount
from .forms import TMSLoginForm, TMSAccountForm
import logging
from .utility import filter_stock_data
logger = logging.getLogger("tms")

# TEMPORARY session cache (not production-safe)
session_cache = {}

@login_required
def tms_login_view(request):
    if request.method == "POST":
        form = TMSLoginForm(request.POST)
        if form.is_valid():
            broker = form.cleaned_data['broker_number']
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            # order_data = {
            #     "script_name": form.cleaned_data['script_name'],
            #     "transaction_type": form.cleaned_data['transaction_type'],
            #     "price": str(form.cleaned_data['price']),
            #     "quantity": str(form.cleaned_data['quantity']),
            #     "price_threshold": str(form.cleaned_data['price_threshold'])
            # }
            # request.session['order_data'] = order_data
            client = SeleniumTMSClient(broker, False)
            client.open_login_page()
            captcha_img = client.get_captcha_base64()

            client.fill_credentials(username, password)
            session_cache["client"] = client  # store client for next step
            session_cache["broker"] = broker
            session_cache["captcha_img"] = captcha_img
            # return render(request, "tms/enter_captcha.html", {
            #     "captcha_img": captcha_img,
            #     "broker": broker,
            # })
            return redirect("tms_captcha_page")
    else:
        form = TMSLoginForm()
        # if client exists in session, close it
        client = session_cache.get("client")
        if client:
            client.close()
            session_cache.pop("client", None)
    return render(request, "tms/login_form.html", {"form": form})
@login_required
def tms_captcha_page(request):
    client: SeleniumTMSClient = session_cache.get("client")
    broker = session_cache.get("broker")
    captcha_img = session_cache.get("captcha_img")
    
    if not client or not broker or not captcha_img:
        return redirect("tms_login")

    # Refresh the captcha every time this page is loaded
    captcha_img = client.get_new_captcha()
    return render(request, "tms/enter_captcha.html", {
        "captcha_img": captcha_img,
        "broker": broker,
    })


@csrf_exempt 
@login_required
def submit_captcha(request):
    if request.method == "POST":
        captcha_text = request.POST.get("captcha")
        broker = request.POST.get("broker")
        
        # order_data = request.session.get('order_data')
        # order_data['price'] = Decimal(order_data['price'])
        # order_data['quantity'] = Decimal(order_data['quantity'])
        # order_data['price_threshold'] = Decimal(order_data['price_threshold'])

        client:SeleniumTMSClient = session_cache.get("client")
        if not client:
            return render(request, "tms/login_form.html", {
                "form": TMSLoginForm(),
                "error": "Session expired. Please try again."
            })

        client.submit_login(captcha_text)
        client.order_entry_visited = False
        if client.login_successful():
            session_cache["client"] = client  # store client for next step
            # return render(request, "tms/live_market_depth.html")
            return redirect('live_market_depth_page')

        else:
            # Refresh captcha and retry
            captcha_img = client.get_new_captcha()
            return render(request, "tms/enter_captcha.html", {
                "captcha_img": captcha_img,
                "broker": broker,
                "error": "Login failed. Please try again."
            })
    
def live_market_depth_page(request):
    symbols_path = os.path.join(settings.BASE_DIR, 'tms', 'static_data', 'symbols.json')
    with open(symbols_path, 'r') as f:
        scripts = json.load(f)

    if session_cache.get("client") is None:
        return redirect("tms_login")
    else:
        return render(request, "tms/live_market_depth.html",{'scripts': scripts})

@csrf_exempt
def live_market_depth_view(request):
    """
    Returns top buyer/seller price + quantity for multiple stocks in JSON.
    Assumes login and navigation to order page already done.
    """
    client: SeleniumTMSClient = session_cache.get("client")
    try:
        if client:
            if client.order_entry_visited == False:
                client.go_to_order_entry()
                client.order_entry_visited = True
            
            if request.method == "POST":
                body = json.loads(request.body)
                should_scrape = body.get("scrape", False)
                watchlist = body.get("watchlist", [])

            # Only scrape if explicitly requested
            if should_scrape:
                client.scrape_multiple_stocks(watchlist)
                filtered_data = filter_stock_data(client.latest_scraped_data)
                return JsonResponse(filtered_data, safe=False)
            else:
                return JsonResponse({"message": "Scraping not triggered"}, status=200)
        else:
            return redirect("tms_login")
    except Exception as e:
        logger.exception("Error scraping market depth")
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def place_order(request):
    """
    Places an order based on the provided script name, price, quantity, and transaction type.
    Returns a JSON response indicating success or failure.
    """
    client: SeleniumTMSClient = session_cache.get("client")
    if not client:
        return redirect("tms_login")
    if request.method == "POST":
        try:
            client.stop_scraping_flag = True # stop scraping thread
            data = json.loads(request.body)
            script = data.get("script_name")
            try:
                price = float(data.get("price", 0))
                quantity = int(data.get("quantity", 0))
            except (ValueError, TypeError):
                return JsonResponse({"error": "Invalid price or quantity"}, status=400)
            txn_type = data.get("transaction_type")

            client.go_to_place_order(script_name=script,transaction=txn_type)
            client.execute_trade(script_name=script, price=price, quantity=quantity, transaction=txn_type)
            client.stop_scraping_flag = False # resume scraping thread
            
            return JsonResponse({"success": True, "message": "Order Placed successfully."}, status=200)
        except Exception as e:
            logger.exception("Error executing trade")
            return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def fetch_open_orders(request):
    """
    Fetches the order book for the logged-in user.
    Returns a JSON response with the order book data.
    """
    client: SeleniumTMSClient = session_cache.get("client")
    if not client:
        return redirect("tms_login")
    
    try:
        order_book = client.scrape_open_orders()
        return JsonResponse(order_book, safe=False, status=200)
    except Exception as e:
        logger.exception("Error fetching order book")
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def fetch_completed_orders(request):
    """
    Fetches the completed orders for the logged-in user.
    Returns a JSON response with the completed orders data.
    """
    client: SeleniumTMSClient = session_cache.get("client")
    if not client:
        return redirect("tms_login")
    
    try:
        completed_orders = client.scrape_completed_orders()
        return JsonResponse(completed_orders, safe=False, status=200)
    except Exception as e:
        logger.exception("Error fetching completed orders")
        return JsonResponse({"error": str(e)}, status=500)
    
@csrf_exempt
def cancel_order_book(request):
    """
    Cancels an order based on the provided order ID.
    Returns a JSON response indicating success or failure.
    """
    client: SeleniumTMSClient = session_cache.get("client")
    if not client:
        return redirect("tms_login")
    
    try:
        client.cancel_all_open_orders()
        return JsonResponse({"success": True, "message": "All open orders cancelled successfully."}, status=200)
    except Exception as e:
        logger.exception("Error cancelling order book")
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def sell_full_portfolio(request):
    """
    Sells all stocks in the portfolio.
    Returns a JSON response indicating success or failure.
    """
    client: SeleniumTMSClient = session_cache.get("client")
    if not client:
        return redirect("tms_login")
    
    try:
        result = client.sell_full_portfolio()
        return JsonResponse(result, status=200)
    except Exception as e:
        logger.exception("Error selling full portfolio")
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def sell_half_portfolio(request):
    """
    Sells half of the eligible stocks in the portfolio.
    Returns a JSON response indicating success or failure.
    """
    client: SeleniumTMSClient = session_cache.get("client")
    if not client:
        return redirect("tms_login")
    
    try:
        result = client.sell_half_portfolio()
        return JsonResponse(result, status=200)
    except Exception as e:
        logger.exception("Error selling half portfolio")
        return JsonResponse({"error": str(e)}, status=500) 
    
@csrf_exempt
@login_required
def my_dp_holdings(request):
    """
    Fetches the Demat holdings for the logged-in user.
    Returns a django template response with the Demat holdings data.
    """
    client: SeleniumTMSClient = session_cache.get("client")
    if not client:
        return redirect("tms_login")
    
    try:
        if not client.portfolio_data:
            # If portfolio data is not already fetched, scrape it
            client.scrape_dp_holding()
        return render(request, "tms/portfolio.html", {"dp_holdings": client.portfolio_data})
    except Exception as e:
        logger.exception("Error fetching Demat holdings")
        return render(request, "error.html", {"error": str(e)}, status=500)
    
@csrf_exempt
@login_required
def tms_account_list(request):
    """
    Displays the list of TMS accounts for the logged-in user.
    """
    accounts = TMSAccount.objects.filter(user=request.user)
    hit_client_api = True # Check if the client is already in session_cache
    if session_cache.get("client"):
        hit_client_api = False
    return render(request, "tms/account_list.html", {"accounts": accounts, "hit_client_api": hit_client_api})

@csrf_exempt
@login_required
def tms_account_create(request):
    """
    Creates a new TMS account for the logged-in user.
    """
    if request.method == "POST":
        form = TMSAccountForm(request.POST)
        if form.is_valid():
            account = form.save(commit=False)
            account.user = request.user
            account.save()
            return redirect("tms_account_list")
    else:
        form = TMSAccountForm()
    return render(request, "tms/account_form.html", {"form": form})

@csrf_exempt
@login_required
def tms_account_update(request, pk):
    """
    Updates an existing TMS account for the logged-in user.
    """
    account = TMSAccount.objects.get(pk=pk, user=request.user)
    if request.method == "POST":
        form = TMSAccountForm(request.POST, instance=account)
        if form.is_valid():
            form.save()
            return redirect("tms_account_list")
    else:
        form = TMSAccountForm(instance=account)
    return render(request, "tms/account_form.html", {"form": form})

@csrf_exempt
@login_required
def tms_account_delete(request, pk):
    """
    Deletes a TMS account for the logged-in user.
    """
    account = TMSAccount.objects.get(pk=pk, user=request.user)
    if request.method == "POST":
        account.delete()
        return redirect("tms_account_list")
    return render(request, "tms/account_confirm_delete.html", {"account": account})

@csrf_exempt
@login_required
def tms_account_login(request, pk):
    """
    Logs in to the primary TMS account for the logged-in user.
    """
    client = session_cache.get("client")
    account = TMSAccount.objects.filter(user=request.user, pk=pk).first()
    if not account:
        return JsonResponse({"error": "No primary account found."}, status=404)
    if client and session_cache["captcha_img"] is not None:
        client.fill_credentials(account.username, account.password)
        return redirect("tms_captcha_page")
    
    
    if session_cache.get("client"):
        client = session_cache["client"]
    else:
        client = SeleniumTMSClient(account.broker_number, False)

    client.open_login_page()
    captcha_img = client.get_captcha_base64()
    client.fill_credentials(account.username, account.password)
    session_cache["client"] = client  # store client for next step
    session_cache["broker"] = account.broker_number
    session_cache["captcha_img"] = captcha_img
    return redirect("tms_captcha_page")

@login_required
def tms_primary_login_api(request):
    """
    API endpoint to log in to the primary TMS account for the logged-in user.
    """
    try:
        primary_account = TMSAccount.objects.filter(user=request.user, is_primary=True).first()
        if not primary_account:
            return JsonResponse({"error": "No primary account found."}, status=404)
        if session_cache.get("client"):
            client = session_cache["client"]
        else:
            client = SeleniumTMSClient(primary_account.broker_number, False)
        client.open_login_page()
        captcha_img = client.get_captcha_base64()
        client.fill_credentials(primary_account.username, primary_account.password)
        session_cache["client"] = client  # store client for next step
        session_cache["broker"] = primary_account.broker_number
        session_cache["captcha_img"] = captcha_img
        
        return JsonResponse({
            "success": True,
            "message": "Primary account login initiated.",
            "captcha_img": captcha_img,
            "broker": primary_account.broker_number
        }, status=200)
    except TMSAccount.DoesNotExist:
        return JsonResponse({"error": "Primary account does not exist."}, status=404)