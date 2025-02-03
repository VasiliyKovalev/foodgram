import json
import os

from django.core.management.base import BaseCommand, CommandError
from django.db.utils import IntegrityError

from recipes.models import Ingredient
from foodgram_backend.settings import BASE_DIR


class Command(BaseCommand):
    help = 'Loading ingredients from data'

    def handle(self, *args, **options):
        try:
            with open(
                os.path.join(
                    BASE_DIR,
                    'data/ingredients.json'
                ),
                'r',
                encoding='utf-8'
            ) as data:
                data = json.load(data)
                for ingredient in data:
                    try:
                        Ingredient.objects.create(
                            name=ingredient['name'],
                            measurement_unit=ingredient['measurement_unit']
                        )
                    except IntegrityError:
                        pass
        except FileNotFoundError:
            raise CommandError('Файл ingredients.json не найден!')
