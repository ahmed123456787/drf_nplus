import pytest

from blog.models import Author, Post, Tag


@pytest.fixture
def seeded_blog(db):
    authors = [Author.objects.create(name=f"Author {i}") for i in range(3)]
    tags = [Tag.objects.create(name=f"tag-{i}") for i in range(3)]
    posts = []
    for i in range(5):
        post = Post.objects.create(
            title=f"Post {i}",
            body=f"Body {i}",
            author=authors[i % len(authors)],
        )
        post.tags.set(tags[: (i % len(tags)) + 1])
        posts.append(post)
    return {"authors": authors, "tags": tags, "posts": posts}
