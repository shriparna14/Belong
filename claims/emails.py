from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def send_otp_email(claim, otp_code):
    """
    Sends the 6-digit handover OTP to claimant's verified email.
    """
    recipient_email = getattr(claim.claimant, 'email', None)
    if not recipient_email:
        return False

    subject = f"Campus Lost & Found: Pickup OTP for '{claim.item.title}'"
    message = (
        f"Hello {claim.claimant.get_full_name() or claim.claimant.username},\n\n"
        f"Great news! Your claim for the item '{claim.item.title}' has been approved.\n\n"
        f"Your 6-Digit Pickup Verification Code is:\n"
        f"----------------------------------------\n"
        f"         >>>  {otp_code}  <<<\n"
        f"----------------------------------------\n\n"
        f"Please present this OTP code to the finder or Campus Security Desk officer during physical handover.\n"
        f"This code will expire in {getattr(settings, 'OTP_EXPIRY_MINUTES', 15)} minutes.\n\n"
        f"Campus Lost & Found Team"
    )

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@campus.edu'),
            recipient_list=[recipient_email],
            fail_silently=True,
        )
        return True
    except Exception as e:
        logger.warning(f"Could not send OTP email: {e}")
        return False
