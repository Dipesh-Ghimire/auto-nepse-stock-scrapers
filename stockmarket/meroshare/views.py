from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import MeroShareAccount
from .forms import MeroShareAccountForm
from django.http import JsonResponse

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