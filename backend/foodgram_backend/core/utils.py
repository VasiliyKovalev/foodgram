from rest_framework import status
from rest_framework.views import exception_handler


def custom_exception_handler404(exc, context):
    response = exception_handler(exc, context)
    if response.status_code == status.HTTP_404_NOT_FOUND:
        response.data['detail'] = 'Страница не найдена.'
    return response
