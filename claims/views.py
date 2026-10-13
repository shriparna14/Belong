from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse
from .models import Claim, HandoffOTP, HandoffAuditLog
from .forms import ClaimForm, OTPVerificationForm
from items.models import Item
from accounts.models import Notification


@login_required
def create_claim_view(request, item_id):
    item = get_object_or_404(Item, pk=item_id)

    # Validations
    if item.reporter == request.user:
        messages.warning(request, "You cannot file a claim on an item you reported yourself.")
        return redirect('items:detail', pk=item.pk)

    if item.item_type != 'found':
        messages.error(request, "Claims can only be filed against items reported as Found.")
        return redirect('items:detail', pk=item.pk)

    if item.status in ['returned', 'archived']:
        messages.error(request, "This item is no longer available for claims.")
        return redirect('items:detail', pk=item.pk)

    # Check existing claim
    existing_claim = Claim.objects.filter(item=item, claimant=request.user).first()
    if existing_claim:
        messages.info(request, "You already submitted a claim for this item.")
        return redirect('claims:detail', pk=existing_claim.pk)

    if request.method == 'POST':
        form = ClaimForm(request.POST, request.FILES)
        if form.is_valid():
            claim = form.save(commit=False)
            claim.item = item
            claim.claimant = request.user
            claim.save()

            # Update item status if it was active
            if item.status == 'active':
                item.status = 'claim_pending'
                item.save()

            # Notify the item reporter
            Notification.objects.create(
                recipient=item.reporter,
                title="New claim filed on your item",
                message=f"{request.user.get_full_name() or request.user.username} submitted an ownership claim on '{item.title}'.",
                notification_type='claim_submitted',
                link=reverse('claims:detail', args=[claim.pk])
            )

            messages.success(request, "Your ownership claim has been submitted! The finder/desk officer will review your evidence.")
            return redirect('claims:detail', pk=claim.pk)
    else:
        form = ClaimForm()

    return render(request, 'claims/create.html', {'form': form, 'item': item})


@login_required
def claim_detail_view(request, pk):
    claim = get_object_or_404(Claim.objects.select_related('item', 'claimant', 'item__reporter'), pk=pk)
    user = request.user
    
    is_claimant = (claim.claimant == user)
    is_finder = (claim.item.reporter == user)
    is_desk = user.is_staff or getattr(getattr(user, 'profile', None), 'role', '') == 'desk_admin'

    if not (is_claimant or is_finder or is_desk):
        messages.error(request, "You are not authorized to view this claim.")
        return redirect('items:index')

    otp = getattr(claim, 'handoff_otp', None)
    verify_form = OTPVerificationForm() if (is_finder or is_desk) and claim.status == 'approved' else None

    context = {
        'claim': claim,
        'item': claim.item,
        'is_claimant': is_claimant,
        'is_finder': is_finder,
        'is_desk': is_desk,
        'otp': otp,
        'verify_form': verify_form,
    }
    return render(request, 'claims/detail.html', context)


@login_required
def review_claim_view(request, pk):
    claim = get_object_or_404(Claim, pk=pk)
    user = request.user
    is_finder = (claim.item.reporter == user)
    is_desk = user.is_staff or getattr(getattr(user, 'profile', None), 'role', '') == 'desk_admin'

    if not (is_finder or is_desk):
        messages.error(request, "You are not authorized to review this claim.")
        return redirect('items:detail', pk=claim.item.pk)

    if request.method == 'POST':
        action = request.POST.get('action')
        notes = request.POST.get('review_notes', '').strip()

        claim.review_notes = notes
        claim.reviewed_by = user
        claim.reviewed_at = timezone.now()

        if action == 'approve':
            claim.status = 'approved'
            claim.save()
            
            # Update item status
            claim.item.status = 'handoff_ready'
            claim.item.save()

            # Generate OTP for claimant
            otp = HandoffOTP.generate_for_claim(claim)
            
            # Notify claimant
            Notification.objects.create(
                recipient=claim.claimant,
                title="Claim Approved - OTP Ready!",
                message=f"Your claim for '{claim.item.title}' was approved! Present your 6-digit OTP code during pickup.",
                notification_type='claim_approved',
                link=reverse('claims:detail', args=[claim.pk])
            )
            messages.success(request, f"Claim approved! A 6-digit secure handoff OTP has been generated for {claim.claimant.username}.")
        elif action == 'reject':
            claim.status = 'rejected'
            claim.save()

            # If there are no other pending claims, set item back to active
            remaining_claims = Claim.objects.filter(item=claim.item, status__in=['pending', 'approved']).exclude(pk=claim.pk).exists()
            if not remaining_claims:
                claim.item.status = 'active'
                claim.item.save()

            # Notify claimant
            Notification.objects.create(
                recipient=claim.claimant,
                title="Claim Not Approved",
                message=f"Your claim for '{claim.item.title}' was reviewed and not approved.",
                notification_type='claim_rejected',
                link=reverse('claims:detail', args=[claim.pk])
            )
            messages.info(request, "Claim has been marked as rejected.")

        return redirect('claims:detail', pk=claim.pk)

    return redirect('claims:detail', pk=claim.pk)


@login_required
def verify_otp_view(request, pk):
    claim = get_object_or_404(Claim, pk=pk)
    user = request.user
    is_finder = (claim.item.reporter == user)
    is_desk = user.is_staff or getattr(getattr(user, 'profile', None), 'role', '') == 'desk_admin'

    if not (is_finder or is_desk):
        messages.error(request, "You are not authorized to verify handoff.")
        return redirect('claims:detail', pk=claim.pk)

    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            entered_otp = form.cleaned_data['otp_code'].strip()
            notes = form.cleaned_data.get('notes', '')

            otp = getattr(claim, 'handoff_otp', None)
            if not otp:
                messages.error(request, "No OTP found for this claim.")
                return redirect('claims:detail', pk=claim.pk)

            if otp.is_used:
                messages.error(request, "This OTP has already been used.")
                return redirect('claims:detail', pk=claim.pk)

            if otp.is_expired:
                messages.error(request, "This OTP has expired. Please regenerate a new OTP.")
                return redirect('claims:detail', pk=claim.pk)

            if otp.otp_code != entered_otp:
                messages.error(request, "Incorrect OTP code. Please ask claimant to verify their active code.")
                return redirect('claims:detail', pk=claim.pk)

            # Verification successful!
            otp.is_used = True
            otp.verified_at = timezone.now()
            otp.verified_by = user
            otp.save()

            claim.status = 'completed'
            claim.save()

            claim.item.status = 'returned'
            claim.item.save()

            # Record audit log
            HandoffAuditLog.objects.create(
                item=claim.item,
                claim=claim,
                returned_to=claim.claimant,
                confirmed_by=user,
                notes=notes or "OTP physically verified upon pickup."
            )

            # Notify claimant
            Notification.objects.create(
                recipient=claim.claimant,
                title="Item Reunited!",
                message=f"'{claim.item.title}' was verified and returned to you. Welcome back to your belonging!",
                notification_type='item_returned',
                link=reverse('items:detail', args=[claim.item.pk])
            )
            # If reporter is someone else, notify them too
            if claim.item.reporter != user:
                Notification.objects.create(
                    recipient=claim.item.reporter,
                    title="Handoff Completed",
                    message=f"'{claim.item.title}' handoff has been completed successfully.",
                    notification_type='item_returned',
                    link=reverse('items:detail', args=[claim.item.pk])
                )

            messages.success(request, f"🎉 Verification Successful! '{claim.item.title}' is officially returned to {claim.claimant.get_full_name() or claim.claimant.username}.")
            return redirect('claims:detail', pk=claim.pk)
        else:
            messages.error(request, "Please enter a valid 6-digit numeric OTP.")

    return redirect('claims:detail', pk=claim.pk)


@login_required
def regenerate_otp_view(request, pk):
    claim = get_object_or_404(Claim, pk=pk)
    user = request.user
    is_claimant = (claim.claimant == user)
    is_finder = (claim.item.reporter == user)
    is_desk = user.is_staff or getattr(getattr(user, 'profile', None), 'role', '') == 'desk_admin'

    if not (is_claimant or is_finder or is_desk):
        messages.error(request, "Not authorized.")
        return redirect('items:index')

    if claim.status != 'approved':
        messages.error(request, "OTP can only be regenerated for approved claims.")
        return redirect('claims:detail', pk=claim.pk)

    otp = HandoffOTP.generate_for_claim(claim)
    messages.success(request, f"A fresh OTP ({otp.otp_code}) has been generated with a new validity window.")
    return redirect('claims:detail', pk=claim.pk)
