from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from ..models import Post, Group
from django.core.cache import cache

User = get_user_model()


class PostURLTests(TestCase):

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
            author=PostURLTests.user
        )
        cls.post_url = f'/posts/{cls.post.id}/'
        cls.post_edit_url = f'/posts/{cls.post.id}/edit/'
        cls.public_urls = (
            ('/', 'posts/index.html'),
            (f'/group/{cls.group.slug}/', 'posts/group_list.html'),
            (f'/profile/{cls.user.username}/', 'posts/profile.html'),
            (cls.post_url, 'posts/post_detail.html'),
        )
        cls.private_urls = (
            ('/create/', 'posts/create_post.html'),
            (cls.post_edit_url, 'posts/create_post.html')
        )

    def setUp(self):
        self.guest_client = Client()
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostURLTests.user)

    def test_index_page(self):
        """Проверка главной страницы"""
        response = self.guest_client.get(PostURLTests.public_urls[0][0])
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_group_list(self):
        """Проверка страницы групп"""
        response = self.guest_client.get(PostURLTests.public_urls[1][0])
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_profile(self):
        """Проверка страницы профиля"""
        response = self.guest_client.get(PostURLTests.public_urls[2][0])
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_detail(self):
        """Проверка страницы поста"""
        response = self.guest_client.get(PostURLTests.post_url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit(self):
        """Проверка страницы редактирования поста"""
        response = self.authorized_client.get(PostURLTests.post_edit_url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create(self):
        """Страница /create/ перенаправит анонимного
        пользователя на страницу логина.
        """
        response = self.guest_client.get(
            PostURLTests.private_urls[0][0], follow=True
        )
        self.assertRedirects(
            response, '/auth/login/?next=/create/'
        )

    def test_create_user(self):
        """Страница /create/ для авторизованного пользователя"""
        response = self.authorized_client.get(PostURLTests.private_urls[0][0])
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexiting_page(self):
        """Проверка несуществующей страницы"""
        response = self.guest_client.get('/_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            PostURLTests.public_urls[0][0]: PostURLTests.public_urls[0][1],
            PostURLTests.public_urls[1][0]: PostURLTests.public_urls[1][1],
            PostURLTests.public_urls[2][0]: PostURLTests.public_urls[2][1],
            PostURLTests.post_url: PostURLTests.public_urls[3][1],
            PostURLTests.private_urls[0][0]: PostURLTests.private_urls[0][1],
            PostURLTests.post_edit_url: PostURLTests.private_urls[1][1],
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
