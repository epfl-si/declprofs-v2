from django.core.files.storage import default_storage
from django.http import JsonResponse
from django.views.decorators.http import require_POST


@require_POST
def tinymce_upload_image(request):
    image = request.FILES.get("file")

    if not image:
        return JsonResponse(
            {"error": "No image received"},
            status=400,
        )

    path = default_storage.save(
        f"tinymce/{image.name}",
        image,
    )

    return JsonResponse({
        "location": default_storage.url(path),
    })
