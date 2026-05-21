import io

import qrcode
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render

from .models import QRRedirect, Scan


def qr_redirect(request, code):
    """Public redirect endpoint. Logs a Scan and issues a 301."""
    try:
        qrr = QRRedirect.objects.get(short_code=code)
    except QRRedirect.DoesNotExist:
        raise Http404("Link not found.")

    if not qrr.is_active:
        return render(request, 'qr_inactive.html', {'label': qrr.label}, status=410)

    # Log the scan — wrapped so a DB hiccup never breaks the redirect
    try:
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
        ip = x_forwarded.split(',')[0].strip() if x_forwarded else request.META.get('REMOTE_ADDR')
        Scan.objects.create(
            redirect=qrr,
            ip_address=ip or None,
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
            referrer=request.META.get('HTTP_REFERER', '')[:500],
        )
    except Exception:
        pass

    return HttpResponseRedirect(qrr.target_url)


def qr_code_image(request, redirect_id):
    """Returns a QR code PNG. Accepts ?fg= &bg= overrides and ?download=1."""
    qrr = get_object_or_404(QRRedirect, id=redirect_id)

    fg = request.GET.get('fg', qrr.fg_color) or qrr.fg_color
    bg = request.GET.get('bg', qrr.bg_color) or qrr.bg_color

    base_url = getattr(settings, 'QR_BASE_URL', 'http://127.0.0.1:8000')
    qr_url = f"{base_url}/r/{qrr.short_code}/"

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color=fg, back_color=bg)

    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)

    disposition = 'attachment' if request.GET.get('download') else 'inline'
    response = HttpResponse(buf.read(), content_type='image/png')
    response['Content-Disposition'] = f'{disposition}; filename="qr-{qrr.short_code}.png"'
    response['Cache-Control'] = 'no-cache'
    return response


@staff_member_required(login_url='/admin/login/')
def qr_dashboard(request):
    qr_base = getattr(settings, 'QR_BASE_URL', 'http://127.0.0.1:8000')
    return render(request, 'qr_dashboard.html', {'qr_base_url': qr_base})
