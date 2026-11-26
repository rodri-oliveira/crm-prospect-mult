"""Menu alerts use the same pending-return lists as the agenda page."""
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

try:
    BUSINESS_TZ = ZoneInfo('America/Sao_Paulo')
except ZoneInfoNotFoundError:
    # Windows can lack the IANA database. São Paulo currently uses UTC-3.
    BUSINESS_TZ = timezone(timedelta(hours=-3))


def business_now():
    return datetime.now(BUSINESS_TZ)


def business_today():
    return business_now().date().isoformat()


def get_return_alerts(repo, now=None):
    now = now or business_now()
    now = now.replace(tzinfo=BUSINESS_TZ) if now.tzinfo is None else now.astimezone(BUSINESS_TZ)
    today = now.date()
    deadline = now + timedelta(hours=1)
    view = repo.get_view_data(today.isoformat(), mostrar_todos=False)
    groups = [
        ('prospeccao', view.retornos_hoje + view.retornos_atrasados),
        ('lead', view.retornos_leads_hoje + view.retornos_leads_atrasados),
    ]
    if deadline.date() != today:
        tomorrow = repo.get_view_data(deadline.date().isoformat(), mostrar_todos=False)
        groups += [('prospeccao', tomorrow.retornos_hoje), ('lead', tomorrow.retornos_leads_hoje)]
    stats = dict(hoje=0, atrasados=0, urgentes=0, sem_horario=0, total=0, mostrar_futuros=False)
    seen = set()
    for source, rows in groups:
        for row in rows:
            key = (source, row['id'])
            if key in seen:
                continue
            seen.add(key)
            try:
                day = datetime.strptime(str(row.get('data_retorno') or '')[:10], '%Y-%m-%d').date()
            except ValueError:
                continue
            hour = str(row.get('hora_retorno') or '').strip()
            try:
                due = datetime.combine(day, time.fromisoformat(hour), BUSINESS_TZ) if hour else None
            except ValueError:
                due = None
            if day > today and (due is None or due > deadline):
                continue
            stats['total'] += 1
            if day > today:
                stats['mostrar_futuros'] = True
            if day == today:
                stats['hoje'] += 1
            if day < today or (due is not None and due <= now):
                stats['atrasados'] += 1
            elif due is not None and due <= deadline:
                stats['urgentes'] += 1
            elif day == today and due is None:
                stats['sem_horario'] += 1
    stats['nivel'] = ('atrasado' if stats['atrasados'] else 'urgente' if stats['urgentes']
                      else 'hoje' if stats['total'] else 'normal')
    parts = []
    if stats['atrasados']:
        parts.append(f"Atrasados: {stats['atrasados']}")
    if stats['urgentes']:
        parts.append(f"Em até 1h: {stats['urgentes']}")
    stats['resumo'] = ' · '.join(parts) or (f"Hoje: {stats['hoje']}" if stats['total'] else '')
    return stats
