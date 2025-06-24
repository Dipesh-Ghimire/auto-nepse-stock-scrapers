import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .meroshare_client.client import MeroShareClient
from .models import MeroShareAccount
from .forms import MeroShareAccountForm
from django.http import JsonResponse
import logging
logger = logging.getLogger("meroshare")

@login_required
def account_list(request):
    accounts = MeroShareAccount.objects.filter(owner=request.user)
    return render(request, 'meroshare/account_list.html', {'accounts': accounts})

@login_required
def account_create(request):
    if request.method == 'POST':
        form = MeroShareAccountForm(request.POST)
        if form.is_valid():
            account = form.save(commit=False)
            account.owner = request.user
            account.save()
            return redirect('meroshare:account_list')
    else:
        form = MeroShareAccountForm()
    return render(request, 'meroshare/account_form.html', {'form': form})

@login_required
def account_update(request, pk):
    account = get_object_or_404(MeroShareAccount, pk=pk, owner=request.user)
    if request.method == 'POST':
        form = MeroShareAccountForm(request.POST, instance=account)
        if form.is_valid():
            form.save()
            return redirect('meroshare:account_list')
    else:
        form = MeroShareAccountForm(instance=account)
    return render(request, 'meroshare/account_form.html', {'form': form})

@login_required
def account_delete(request, pk):
    account = get_object_or_404(MeroShareAccount, pk=pk, owner=request.user)
    if request.method == 'POST':
        account.delete()
        return redirect('meroshare:account_list')

@login_required
def toggle_auto_ipo(request, pk):
    if request.method == 'POST':
        account = get_object_or_404(MeroShareAccount, pk=pk, owner=request.user)
        account.auto_ipo_apply = not account.auto_ipo_apply
        account.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)

@require_POST
@login_required
def apply_ipo(request):
    try:
        data = json.loads(request.body)
        username = data.get('username')
        number_of_shares = data.get('number_of_shares')
    except (json.JSONDecodeError, KeyError, TypeError):
        return JsonResponse({'success': False, 'message': 'Invalid request data.'}, status=400)

    if not username or not number_of_shares:
        return JsonResponse({'success': False, 'message': 'Username and number_of_shares are required.'}, status=400)

    accounts = MeroShareAccount.objects.filter(owner=request.user)
    account = None
    for acc in accounts:
        if acc.username == username:
            account = acc
            break
    if not account:
        return JsonResponse({'success': False, 'message': 'Account not found.'}, status=404)

    logger.info(f"Applying for IPO for account: {username}")
    client = MeroShareClient(account)
    issues = client.get_filtered_issues()
    logger.info(f"Found {len(issues)} issues for {username}")

    for issue in issues:
        try:
            if issue.is_reapply:
                logger.info(f"Reapplying for {issue.company_name}")
                client.reapply(issue.company_share_id, number_of_shares)
            else:
                logger.info(f"Applying for {issue.company_name}")
                client.apply(issue.company_share_id, number_of_shares)
        except Exception as e:
            logger.info(f"Error applying for {issue.company_name}: {e}")

    client.logout()
    return JsonResponse({'success': True, 'message': 'IPO application completed.'})

@require_POST
@login_required
def apply_bulk_ipo(request):
    accounts = MeroShareAccount.objects.filter(owner=request.user)

    if not accounts.exists():
        return JsonResponse({'success': False, 'message': 'No accounts with owner found.'}, status=404)

    results = []

    for account in accounts:
        logger.info(f"Applying for IPO for account: {account.username}")
        client = MeroShareClient(account)

        try:
            issues = client.get_filtered_issues()
            logger.info(f"Found {len(issues)} issues for {account.username}")

            for issue in issues:
                try:
                    client.apply(issue.company_share_id, account.default_share_count)
                    results.append({
                        'username': account.username,
                        'company': issue.company_name,
                        'status': 'applied'
                    })
                except Exception as e:
                    logger.info(f"Error applying for {issue.company_name}: {e}")
                    results.append({
                        'username': account.username,
                        'company': issue.company_name,
                        'status': f'error: {str(e)}'
                    })
        finally:
            client.logout()

    return JsonResponse({'success': True, 'results': results})
