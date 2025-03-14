## Foodgram
Foodgram - сайт с авторскими рецептами.

### Описание
*  Зарегистрированные пользователи имеют возможность публиковать свои рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов
*  При добавлении рецепта необходимо указать название, описание, время приготовления, а также прикрепить изображение. Обязательно нужно выбрать как минимум по одному ингредиенту и тегу. 
*  Пополнять список ингредиентов и тегов может только администратор.
*  Зарегистрированным пользователям доступен сервис «Список покупок». Он позволяет создавать список продуктов, которые нужно купить для приготовления выбранных блюд.
*  Имеется возможность скачать составленный список покупок в формате .txt.

### Как запустить проект:
1. Клонировать репозиторий и перейти в него в командной строке:

```
git clone git@github.com:VasiliyKovalev/foodgram.git
```

```
cd foodgram
```

2. Создать файл .env:

```
touch .env
```

3. Указать переменные окружения в файле .env по примеру файла .env.example:

```
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=foodgram_password
POSTGRES_DB=foodgram
DB_HOST=foodgram
DB_PORT=5432
SECRET_KEY=
ALLOWED_HOSTS=127.0.0.1, localhost, foodgram_example.com
DEBUG = 
BD_IS_SQLITE =
```

4. Запустить Docker Compose:

```
docker compose up
```

5. Выполнить миграции:

```
docker compose exec backend python manage.py migrate
```

6. Собрать статику:

```
docker compose exec backend python manage.py collectstatic
```

### После запуска проект будет доступен по адресу:
http://127.0.0.1:8000/

### Технологии:
1. Python 3.9
2. Django
3. DRF
4. Djoser
5. Simple JWT
6. Nginx
7. Docker
8. PostgreSQL

### Наполнение базы данных ингредиентами
В директории ``` /backend/data ``` подготовлен файл в формате json с контентом для ресурса Ingredient.
Чтобы загрузить данные из файла json в базу данных подготовлена собственная management-команда load_ingredients.
Для использования в командную строку нужно прописать:
```
docker compose exec backend python manage.py load_ingredients
```

### После запуска проекта документация будет доступна по адресу:
http://127.0.0.1:8000/redoc/

### Ресурсы API Foodgram:
* Пользователи
* Теги
* Рецепты
* Список покупок
* Избранное
* Подписки
* Ингредиенты

### Примеры запросов к API:
* Регистрация нового пользователя.
```
POST /api/users/
```
* Получение токена авторизации.
```
POST /api/auth/token/login/
```
* Получение данных своей учетной записи.
```
GET /api/users/me/
```
* Получение списка всех тегов.
```
GET /api/tags/
```
* Получение списка всех рецептов.
```
GET /api/recipes/
```
* Добавление нового рецепта.
```
POST /api/recipes/
```
* Получение короткой ссылки на рецепт.
```
GET /api/recipes/{id}/get-link/
```
* Скачивание списка покупок.
```
GET /api/recipes/download_shopping_cart/
```
* Добавление рецепта в список покупок.
```
POST /api/recipes/shopping_cart/
```
* Добавление рецепта в избранное.
```
POST /api/recipes/{id}/favorite/
```
* Получение списка всех своих подписок.
```
GET /api/users/subscriptions/
```
* Создание подписки на пользователя.
```
POST /api/users/{id}/subscribe/
```
* Получение списка всех ингредиентов.
```
GET /api/ingredients/
```

### Автор проекта:
*  [Василий Ковалев](https://github.com/VasiliyKovalev)
