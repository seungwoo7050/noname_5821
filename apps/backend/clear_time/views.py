from django.db import connection
from django.http import JsonResponse
from django.views.decorators.http import require_GET


@require_GET
def viability(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT current_database(), current_setting('server_version')")
        database_name, server_version = cursor.fetchone()

    return JsonResponse(
        {
            "contract": "public-api/v1",
            "database": "postgresql",
            "database_name": database_name,
            "postgresql_version": server_version,
            "status": "ready",
        }
    )
