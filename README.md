A DRF serializer-aware N+1 detector. This week's goal: reproduce the N+1 problem in a toy blog project and build minimal middleware that counts SQL queries per request.

## Setup

```bash
cd /home/ahmed/Desktop/drf_nplus_project
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python manage.py migrate
python manage.py shell < seed.py
python manage.py runserver
```

## Try it

In another terminal:

```bash
# The unoptimized endpoint — should print ~201 queries
curl -s http://127.0.0.1:8000/posts/ > /dev/null

# The optimized endpoint — should print ~3 queries
curl -s http://127.0.0.1:8000/posts-optimized/ > /dev/null
```

Watch the `runserver` terminal for lines like:

```
[drf-nplus] GET /posts/ → 201 queries in 340.2ms | 2 repeated SQL templates (possible N+1)
[drf-nplus] GET /posts-optimized/ → 3 queries in 22.1ms
```

The gap between those two numbers is the problem this library will solve.

## What's next (Week 2)

- Monkey-patch `Serializer.to_representation` and `Field.get_attribute`
- Maintain a `ContextVar` stack of the current serializer field path
- Tag each captured query with the field path that triggered it
- Output: `PostSerializer.author: 100 queries (all identical template)`

## Project layout

```
drf_nplus_project/
├── config/            # Django project (settings, urls, wsgi)
├── blog/              # Toy blog app with the N+1 problem
│   ├── models.py      # Post, Author (FK), Tag (M2M)
│   ├── serializers.py # Nested PostSerializer — the source of N+1
│   ├── views.py       # Unoptimized + optimized viewsets side-by-side
│   └── urls.py
├── drf_nplus/         # The library being built
│   └── middleware.py  # v0.1: query counter using connection.execute_wrapper
├── seed.py            # Populate 100 posts / 20 authors / 15 tags
├── manage.py
└── requirements.txt
```
