import uuid

from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .models import CompletionScope, Game, Lifecycle, PlaytimeAggregateRevision, normalize_alias

MAX_QUERY_LENGTH = 100


def _error(code: str, status: int) -> JsonResponse:
    return JsonResponse(
        {
            "contract": "public-api/v1",
            "error": {"code": code, "correlation_id": str(uuid.uuid4())},
        },
        status=status,
    )


def _validated_filters(request):
    platform = request.GET.get("platform", "").strip().casefold()
    scope = request.GET.get("scope", "").strip()
    if scope and scope not in CompletionScope.values:
        return None, None, _error("invalid_completion_scope", 400)
    if len(platform) > 40:
        return None, None, _error("invalid_platform", 400)
    return platform, scope, None


@require_GET
def game_search(request):
    query = request.GET.get("query", "")
    normalized = normalize_alias(query)
    if not normalized or len(normalized) > MAX_QUERY_LENGTH:
        return _error("invalid_search_query", 400)
    platform, scope, error = _validated_filters(request)
    if error:
        return error

    games = Game.objects.filter(lifecycle=Lifecycle.ACTIVE).filter(
        Q(aliases__normalized_text__icontains=normalized)
        | Q(korean_title__icontains=query.strip())
        | Q(original_title__icontains=query.strip())
    )
    if platform:
        games = games.filter(aggregate_keys__platform__code=platform)
    if scope:
        games = games.filter(aggregate_keys__completion_scope=scope)
    results = [
        {
            "id": str(game.id),
            "slug": game.slug,
            "korean_title": game.korean_title,
            "original_title": game.original_title,
        }
        for game in games.distinct().order_by("korean_title", "id")[:20]
    ]
    return JsonResponse({"contract": "public-api/v1", "results": results})


@require_GET
def game_detail(request, game_id):
    platform, scope, error = _validated_filters(request)
    if error:
        return error
    try:
        game = Game.objects.get(pk=game_id, lifecycle=Lifecycle.ACTIVE)
    except Game.DoesNotExist:
        return _error("game_not_found", 404)

    keys = game.aggregate_keys.select_related("platform", "current_revision").order_by(
        "platform__code", "completion_scope"
    )
    if platform:
        keys = keys.filter(platform__code=platform)
    if scope:
        keys = keys.filter(completion_scope=scope)
    aggregates = []
    for key in keys:
        base = {
            "platform": {
                "id": str(key.platform_id),
                "code": key.platform.code,
                "label": key.platform.display_label,
            },
            "completion_scope": key.completion_scope,
        }
        revision = key.current_revision
        if not revision or revision.state != PlaytimeAggregateRevision.State.CURRENT:
            aggregates.append({**base, "status": "insufficient_data"})
            continue
        aggregates.append(
            {
                **base,
                "status": "published",
                "median_minutes": revision.median_minutes,
                "sample_count": revision.sample_count,
                "rule_revision": revision.rule_revision,
                "revision_id": str(revision.id),
                "revision_number": revision.revision_number,
            }
        )
    return JsonResponse(
        {
            "contract": "public-api/v1",
            "game": {
                "id": str(game.id),
                "slug": game.slug,
                "korean_title": game.korean_title,
                "original_title": game.original_title,
            },
            "aggregates": aggregates,
        }
    )
