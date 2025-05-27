from decimal import Decimal
from django.shortcuts import render
from django.http import JsonResponse
import json
from django.views.decorators.csrf import csrf_exempt
from .forms import TMSLoginForm
from .selenium_client import SeleniumTMSClient
import logging
from .utility import filter_stock_data
logger = logging.getLogger("stocks")

# TEMPORARY session cache (not production-safe)
session_cache = {}

def tms_login_view(request):
    if request.method == "POST":
        form = TMSLoginForm(request.POST)
        if form.is_valid():
            broker = form.cleaned_data['broker_number']
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            order_data = {
                "script_name": form.cleaned_data['script_name'],
                "transaction_type": form.cleaned_data['transaction_type'],
                "price": str(form.cleaned_data['price']),
                "quantity": str(form.cleaned_data['quantity']),
                "price_threshold": str(form.cleaned_data['price_threshold'])
            }
            request.session['order_data'] = order_data
            client = SeleniumTMSClient(broker)
            client.open_login_page()
            captcha_img = client.get_captcha_base64()

            client.fill_credentials(username, password)
            session_cache["client"] = client  # store client for next step

            return render(request, "tms/enter_captcha.html", {
                "captcha_img": captcha_img,
                "broker": broker,
            })
    else:
        form = TMSLoginForm()
        # if client exists in session, close it
        client = session_cache.get("client")
        if client:
            client.close()
            session_cache.pop("client", None)
    return render(request, "tms/login_form.html", {"form": form})



@csrf_exempt
def submit_captcha(request):
    if request.method == "POST":
        captcha_text = request.POST.get("captcha")
        broker = request.POST.get("broker")
        
        order_data = request.session.get('order_data')
        order_data['price'] = Decimal(order_data['price'])
        order_data['quantity'] = Decimal(order_data['quantity'])
        order_data['price_threshold'] = Decimal(order_data['price_threshold'])

        client:SeleniumTMSClient = session_cache.get("client")
        if not client:
            return render(request, "tms/login_form.html", {
                "form": TMSLoginForm(),
                "error": "Session expired. Please try again."
            })

        client.submit_login(captcha_text)
        client.order_entry_visited = False
        if client.login_successful():
            # dashboard_data = client.scrape_dashboard_stats()
            # collateral_data = client.scrape_collateral()
            # # html_table = client.get_market_depth_html(instrument_type="EQ", script_name="MEN")
            # client.go_to_place_order(script_name=order_data['script_name'],transaction=order_data['transaction_type'])
            # client.execute_trade(script_name=order_data['script_name'],price=order_data['price'], quantity=order_data['quantity'], transaction=order_data['transaction_type'])
            # client.close()
            # return render(request, "tms/login_success.html", {"dashboard_data": dashboard_data, "collateral_data": collateral_data})
            # # return render(request, "tms/market_depth.html", {"table_html": html_table})
            session_cache["client"] = client  # store client for next step
            return render(request, "tms/live_market_depth.html")

        else:
            # Refresh captcha and retry
            captcha_img = client.get_new_captcha()
            return render(request, "tms/enter_captcha.html", {
                "captcha_img": captcha_img,
                "broker": broker,
                "error": "Login failed. Please try again."
            })

@csrf_exempt
def live_market_depth_view(request):
    """
    Returns top buyer/seller price + quantity for multiple stocks in JSON.
    Assumes login and navigation to order page already done.
    """
    client: SeleniumTMSClient = session_cache.get("client")
    if not client:
        return JsonResponse({"error": "Session expired. Please log in again."}, status=400)
    try:
        if client:
            if client.order_entry_visited == False:
                client.go_to_order_entry()
                client.order_entry_visited = True

            # Only scrape if explicitly requested
            should_scrape = request.GET.get("scrape") == "true"
            if should_scrape:
                client.scrape_multiple_stocks()
                filtered_data = filter_stock_data(client.latest_scraped_data)
                return JsonResponse(filtered_data, safe=False)
            else:
                return JsonResponse({"message": "Scraping not triggered"}, status=200)
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
        return JsonResponse({"error": "Session expired. Please log in again."}, status=400)
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