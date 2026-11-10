def notification_stats(request):
    """
    Context processor to provide unread notification count and recent notifications.
    """
    if request.user.is_authenticated:
        unread_count = request.user.notifications.filter(is_read=False).count()
        recent_notifications = request.user.notifications.all().order_by('-created_at')[:5]
        return {
            'unread_notification_count': unread_count,
            'recent_notifications': recent_notifications,
            'SITE_NAME': 'LifeDrop BD',
            'SITE_TAGLINE': 'Every Drop Counts. Every Life Matters.',
            'DEFAULT_CURRENCY': 'BDT',
        }
    return {
        'unread_notification_count': 0,
        'recent_notifications': [],
        'SITE_NAME': 'LifeDrop BD',
        'SITE_TAGLINE': 'Every Drop Counts. Every Life Matters.',
        'DEFAULT_CURRENCY': 'BDT',
    }
