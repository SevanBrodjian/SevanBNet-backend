import json
from datetime import date, timedelta

from django.db.models import Count
from django.db.models.functions import TruncDate
from django.http import JsonResponse
from django.utils import timezone

from .models import QRRedirect, Scan


def _require_staff(view_func):
    """Returns JSON 403 for unauthenticated / non-staff requests."""
    def wrapper(request, *args, **kwargs):
        if not (request.user.is_authenticated and request.user.is_staff):
            return JsonResponse({'error': 'Forbidden'}, status=403)
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


def _serialize(qrr, include_chart=True):
    d = {
        'id':            qrr.id,
        'short_code':    qrr.short_code,
        'label':         qrr.label,
        'target_url':    qrr.target_url,
        'is_active':     qrr.is_active,
        'created_at':    qrr.created_at.isoformat(),
        'fg_color':      qrr.fg_color,
        'bg_color':      qrr.bg_color,
        'qr_style':      qrr.qr_style,
        'qr_radius':     qrr.qr_radius,
        'bg_transparent': qrr.bg_transparent,
        'total_scans':   qrr.scans.count(),
    }
    if include_chart:
        end   = timezone.now().date()
        start = end - timedelta(days=13)
        rows  = (
            qrr.scans.filter(timestamp__date__gte=start)
            .annotate(day=TruncDate('timestamp'))
            .values('day')
            .annotate(count=Count('id'))
            .order_by('day')
        )
        scan_map = {r['day'].isoformat(): r['count'] for r in rows}
        days, cur = [], start
        while cur <= end:
            days.append({'date': cur.isoformat(), 'count': scan_map.get(cur.isoformat(), 0)})
            cur += timedelta(days=1)
        d['scans_14d'] = days
    return d


@_require_staff
def redirects_list(request):
    if request.method == 'GET':
        qs = QRRedirect.objects.all()
        return JsonResponse([_serialize(r) for r in qs], safe=False)

    if request.method == 'POST':
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        for field in ('short_code', 'label', 'target_url'):
            if not body.get(field, '').strip():
                return JsonResponse({'error': f'"{field}" is required.'}, status=400)

        if QRRedirect.objects.filter(short_code=body['short_code']).exists():
            return JsonResponse({'error': 'That short code is already taken.'}, status=409)

        qrr = QRRedirect.objects.create(
            short_code=body['short_code'].strip(),
            label=body['label'].strip(),
            target_url=body['target_url'].strip(),
            is_active=body.get('is_active', True),
            fg_color=body.get('fg_color', '#000000'),
            bg_color=body.get('bg_color', '#ffffff'),
            qr_style=body.get('qr_style', 'square'),
            qr_radius=float(body.get('qr_radius', 0.5)),
            bg_transparent=bool(body.get('bg_transparent', False)),
        )
        return JsonResponse(_serialize(qrr), status=201)

    return JsonResponse({'error': 'Method not allowed'}, status=405)


@_require_staff
def redirect_detail(request, pk):
    try:
        qrr = QRRedirect.objects.get(pk=pk)
    except QRRedirect.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)

    if request.method == 'PATCH':
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        for field in ('label', 'target_url', 'is_active',
                      'fg_color', 'bg_color',
                      'qr_style', 'qr_radius', 'bg_transparent'):
            if field in body:
                setattr(qrr, field, body[field])
        qrr.save()
        return JsonResponse(_serialize(qrr))

    if request.method == 'DELETE':
        qrr.delete()
        return JsonResponse({'ok': True})

    return JsonResponse({'error': 'Method not allowed'}, status=405)


@_require_staff
def redirect_scans(request, pk):
    """Returns 30-day daily scan counts — for future detailed analytics view."""
    try:
        qrr = QRRedirect.objects.get(pk=pk)
    except QRRedirect.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)

    end   = timezone.now().date()
    start = end - timedelta(days=29)
    rows  = (
        qrr.scans.filter(timestamp__date__gte=start)
        .annotate(day=TruncDate('timestamp'))
        .values('day')
        .annotate(count=Count('id'))
        .order_by('day')
    )
    scan_map = {r['day'].isoformat(): r['count'] for r in rows}
    days, cur = [], start
    while cur <= end:
        days.append({'date': cur.isoformat(), 'count': scan_map.get(cur.isoformat(), 0)})
        cur += timedelta(days=1)

    return JsonResponse({'total': qrr.scans.count(), 'days': days})
