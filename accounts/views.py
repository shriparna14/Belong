from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CampusRegistrationForm, ProfileUpdateForm, EmailOrUsernameAuthenticationForm
from items.models import Item
from claims.models import Claim


def register_view(request):
    if request.user.is_authenticated:
        return redirect('items:index')
    
    if request.method == 'POST':
        form = CampusRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to Belong, {user.first_name or user.username}! Your campus account is ready.")
            return redirect('items:index')
    else:
        form = CampusRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('items:index')
    
    if request.method == 'POST':
        form = EmailOrUsernameAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {user.first_name or user.username}!")
                next_url = request.GET.get('next') or 'items:index'
                return redirect(next_url)
        else:
            messages.error(request, "Invalid email/username or password. Please try again.")
    else:
        form = EmailOrUsernameAuthenticationForm(request)

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out securely.")
    return redirect('items:index')


@login_required
def profile_view(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            user = request.user
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.email = form.cleaned_data['email']
            user.save()
            form.save()
            messages.success(request, "Your campus profile has been updated.")
            return redirect('accounts:profile')
    else:
        initial = {
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
        }
        form = ProfileUpdateForm(instance=request.user.profile, initial=initial)

    return render(request, 'accounts/profile.html', {'form': form})


@login_required
def dashboard_view(request):
    user = request.user
    my_reported_items = Item.objects.filter(reporter=user).order_by('-created_at')
    my_claims = Claim.objects.filter(claimant=user).order_by('-created_at')
    incoming_claims = Claim.objects.filter(item__reporter=user).exclude(claimant=user).order_by('-created_at')

    context = {
        'my_reported_items': my_reported_items,
        'my_claims': my_claims,
        'incoming_claims': incoming_claims,
        'active_tab': request.GET.get('tab', 'items')
    }
    return render(request, 'accounts/dashboard.html', context)


@login_required
def notifications_view(request):
    notifications = request.user.notifications.all()
    return render(request, 'accounts/notifications.html', {'notifications': notifications})


@login_required
def mark_notification_read_view(request, pk):
    notification = get_object_or_404(request.user.notifications, pk=pk)
    notification.is_read = True
    notification.save()
    if notification.link:
        return redirect(notification.link)
    return redirect('accounts:notifications')


@login_required
def mark_all_notifications_read_view(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    messages.success(request, "All notifications marked as read.")
    return redirect('accounts:notifications')


@login_required
def admin_dashboard_view(request):
    if not request.user.is_staff:
        messages.error(request, "Staff authorization required to access the admin dashboard.")
        return redirect('items:index')

    from django.contrib.auth.models import User
    total_users = User.objects.count()
    total_reports = Item.objects.count()
    lost_items = Item.objects.filter(item_type='lost').count()
    found_items = Item.objects.filter(item_type='found').count()
    returned_items = Item.objects.filter(status='returned').count()
    pending_claims = Claim.objects.filter(status='pending').count()
    approved_claims = Claim.objects.filter(status='approved').count()

    recent_reports = Item.objects.select_related('category', 'location', 'reporter').order_by('-created_at')[:8]
    recent_claims = Claim.objects.select_related('item', 'claimant').order_by('-created_at')[:8]

    context = {
        'total_users': total_users,
        'total_reports': total_reports,
        'lost_items': lost_items,
        'found_items': found_items,
        'returned_items': returned_items,
        'pending_claims': pending_claims,
        'approved_claims': approved_claims,
        'recent_reports': recent_reports,
        'recent_claims': recent_claims,
    }
    return render(request, 'accounts/admin_dashboard.html', context)
