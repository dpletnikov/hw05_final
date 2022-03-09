from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from posts.models import Post, Group

User = get_user_model()


class Post404Tests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый заголовок',
            author=Post404Tests.user
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(Post404Tests.user)

    def test_404(self):
        """Страница 404 использует правильный шаблон."""
        response = self.authorized_client.get('/unknown/')
        self.assertTemplateUsed(response, 'core/404.html')
