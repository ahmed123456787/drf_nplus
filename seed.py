"""
Seed the toy blog with 100 posts, each with an author and 3 tags.

Run with:
    python manage.py shell < seed.py
or:
    python -c "import os, django; os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings'); django.setup(); exec(open('seed.py').read())"
"""

import random

from blog.models import Author, Post, Tag

Post.objects.all().delete()
Author.objects.all().delete()
Tag.objects.all().delete()

authors = [Author.objects.create(name=f"Author {i}") for i in range(20)]
tags = [Tag.objects.create(name=f"tag-{i}") for i in range(15)]

for i in range(100):
    post = Post.objects.create(
        title=f"Post {i}",
        body=f"Body of post {i}",
        author=random.choice(authors),
    )
    post.tags.set(random.sample(tags, k=3))

print(f"Seeded {Post.objects.count()} posts, {Author.objects.count()} authors, {Tag.objects.count()} tags.")
