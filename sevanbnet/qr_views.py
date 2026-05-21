import io

import qrcode
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render

from .models import QRRedirect, Scan


# ── Image generation helpers ──────────────────────────────────────────────────

def _hex_to_rgb(hex_str):
    h = hex_str.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _make_qr_pil(qr_obj, fg, bg, style, radius, transparent):
    """
    Returns a PIL Image for the given QR code object and style settings.
    Styles: square | rounded | circle | gapped
    Transparency is applied as a post-process (replaces bg-coloured pixels).
    """
    from PIL import Image as PILImage

    fg_rgb = _hex_to_rgb(fg)
    bg_rgb = _hex_to_rgb(bg)

    if style in ('rounded', 'circle', 'gapped'):
        try:
            from qrcode.image.styledpil import StyledPilImage
            from qrcode.image.styles.colormasks import SolidFillColorMask  # plural
            from qrcode.image.styles.moduledrawers.pil import (
                RoundedModuleDrawer, CircleModuleDrawer, GappedSquareModuleDrawer,
            )
            if style == 'rounded':
                drawer = RoundedModuleDrawer(radius_ratio=min(max(float(radius), 0.0), 1.0))
            elif style == 'circle':
                drawer = CircleModuleDrawer()
            else:
                drawer = GappedSquareModuleDrawer()
            mask = SolidFillColorMask(front_color=fg_rgb, back_color=bg_rgb)
            pil = qr_obj.make_image(
                image_factory=StyledPilImage,
                module_drawer=drawer,
                eye_drawer=drawer,
                color_mask=mask,
            ).get_image()
        except Exception as e:
            # Graceful fallback to square
            pil = qr_obj.make_image(fill_color=fg, back_color=bg).get_image()
    else:
        pil = qr_obj.make_image(fill_color=fg, back_color=bg).get_image()

    if transparent:
        pil = pil.convert('RGBA')
        r_bg, g_bg, b_bg = bg_rgb
        pixels = pil.load()
        w, h_px = pil.size
        thresh = 35
        for y in range(h_px):
            for x in range(w):
                px = pixels[x, y]
                pr, pg, pb = px[0], px[1], px[2]
                if abs(pr - r_bg) < thresh and abs(pg - g_bg) < thresh and abs(pb - b_bg) < thresh:
                    pixels[x, y] = (pr, pg, pb, 0)

    return pil


# ── Views ─────────────────────────────────────────────────────────────────────

def qr_redirect(request, code):
    """Public redirect endpoint. Logs a Scan and issues a 301."""
    try:
        qrr = QRRedirect.objects.get(short_code=code)
    except QRRedirect.DoesNotExist:
        raise Http404("Link not found.")

    if not qrr.is_active:
        return render(request, 'qr_inactive.html', {'label': qrr.label}, status=410)

    # Log silently — never let a DB hiccup break the redirect
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
    """Returns a styled QR code PNG. All params fall back to stored values."""
    qrr = get_object_or_404(QRRedirect, id=redirect_id)

    fg          = request.GET.get('fg',          qrr.fg_color)       or qrr.fg_color
    bg          = request.GET.get('bg',          qrr.bg_color)       or qrr.bg_color
    style       = request.GET.get('style',       qrr.qr_style)       or qrr.qr_style
    radius      = float(request.GET.get('radius', qrr.qr_radius)     or qrr.qr_radius)
    transparent = request.GET.get('transparent', str(qrr.bg_transparent)).lower() in ('1', 'true', 'yes')

    base_url = getattr(settings, 'QR_BASE_URL', 'http://127.0.0.1:8000')
    qr_url   = f"{base_url}/r/{qrr.short_code}/"

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_url)
    qr.make(fit=True)

    pil = _make_qr_pil(qr, fg, bg, style, radius, transparent)

    buf = io.BytesIO()
    pil.save(buf, format='PNG')
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
