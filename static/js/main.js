// Belong — Campus Lost & Found
// Interactive Client-Side Utilities

document.addEventListener('DOMContentLoaded', () => {
  // 1. Password Visibility Toggle
  const toggleButtons = document.querySelectorAll('.password-toggle-btn');
  toggleButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetId = btn.getAttribute('data-target');
      const input = document.getElementById(targetId);
      if (input) {
        if (input.type === 'password') {
          input.type = 'text';
          btn.textContent = 'Hide';
          btn.setAttribute('aria-label', 'Hide password');
        } else {
          input.type = 'password';
          btn.textContent = 'Show';
          btn.setAttribute('aria-label', 'Show password');
        }
      }
    });
  });

  // 2. Copy OTP to clipboard
  const copyOtpBtn = document.getElementById('copyOtpBtn');
  if (copyOtpBtn) {
    copyOtpBtn.addEventListener('click', () => {
      const otpCode = copyOtpBtn.dataset.otp;
      if (otpCode) {
        navigator.clipboard.writeText(otpCode).then(() => {
          const originalText = copyOtpBtn.innerText;
          copyOtpBtn.innerText = 'Copied! ✓';
          setTimeout(() => {
            copyOtpBtn.innerText = originalText;
          }, 2500);
        });
      }
    });
  }

  // 3. Image upload preview
  const fileInputs = document.querySelectorAll('input[type="file"]');
  fileInputs.forEach(input => {
    input.addEventListener('change', (e) => {
      const file = e.target.files[0];
      const previewContainer = document.getElementById(input.id + '_preview') || document.querySelector('.image-preview-box');
      if (file && previewContainer) {
        const reader = new FileReader();
        reader.onload = (event) => {
          previewContainer.innerHTML = `
            <img src="${event.target.result}" style="max-height: 200px; border-radius: 6px; object-fit: contain; width: 100%; border: 1px solid #E5E3DA;" alt="Selected Preview" />
          `;
          previewContainer.style.display = 'block';
        };
        reader.readAsDataURL(file);
      }
    });
  });

  // 4. Auto-submit filter selects
  const filterSelects = document.querySelectorAll('.auto-submit-select');
  filterSelects.forEach(select => {
    select.addEventListener('change', () => {
      select.closest('form').submit();
    });
  });

  // 5. Countdown timer for OTP
  const otpCountdownEl = document.getElementById('otpCountdown');
  if (otpCountdownEl) {
    const expiresTimestamp = parseInt(otpCountdownEl.dataset.expires, 10);
    if (expiresTimestamp) {
      const updateCountdown = () => {
        const now = Math.floor(Date.now() / 1000);
        const diff = expiresTimestamp - now;
        if (diff <= 0) {
          otpCountdownEl.innerHTML = '<span style="color: #A6533B; font-weight: 700;">Expired! Please regenerate OTP.</span>';
          const regenBtn = document.getElementById('regenOtpContainer');
          if (regenBtn) regenBtn.style.display = 'block';
        } else {
          const minutes = Math.floor(diff / 60);
          const seconds = diff % 60;
          otpCountdownEl.innerHTML = `Expires in <strong>${minutes}m ${seconds < 10 ? '0' : ''}${seconds}s</strong>`;
        }
      };
      updateCountdown();
      setInterval(updateCountdown, 1000);
    }
  }

  // 6. Alert dismissal
  const dismissAlertBtns = document.querySelectorAll('.alert-dismiss');
  dismissAlertBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const alert = btn.closest('.alert');
      if (alert) alert.remove();
    });
  });

  // 7. Prevent accidental duplicate form submissions
  const forms = document.querySelectorAll('form:not([data-no-disable])');
  forms.forEach(form => {
    form.addEventListener('submit', (e) => {
      // If form is valid or checkValidity passes
      if (form.checkValidity && !form.checkValidity()) {
        return;
      }
      const submitBtn = form.querySelector('button[type="submit"]');
      if (submitBtn && !submitBtn.disabled) {
        setTimeout(() => {
          submitBtn.disabled = true;
          submitBtn.setAttribute('aria-disabled', 'true');
          const originalText = submitBtn.textContent.trim();
          submitBtn.dataset.originalText = originalText;
          submitBtn.textContent = 'Submitting...';
        }, 0);
      }
    });
  });
});
