import base64
import requests
from django.conf import settings


def upload_image_to_imgbb(image):
    url = "https://api.imgbb.com/1/upload"

    image_data = base64.b64encode(
        image.read()
    ).decode("utf-8")

    payload = {
        "key": settings.IMGBB_API_KEY,
        "image": image_data,
    }

    response = requests.post(url, data=payload)

    result = response.json()

    if result.get("success"):
        return result["data"]["url"]

    return None