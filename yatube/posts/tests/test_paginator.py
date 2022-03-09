from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Post, Group

User = get_user_model()

FIRST_PAGE_COUNT_POSTS = 10
SECOND_PAGE_COUNT_POSTS = 6
PAGINATOR_NUMBER = 16


class PaginatorViewsTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.bulk_create([
            Post(
                text='Тестовый заголовок',
                author=cls.user,
                group=cls.group
            )
            for i in range(PAGINATOR_NUMBER)
        ])

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_of_index(self):
        response = self.client.get(reverse('posts:index_page'))
        """ Проверка: количество постов на первой странице равно 10. """
        self.assertEqual(
            len(response.context['page_obj']), FIRST_PAGE_COUNT_POSTS
        )

    def test_second_page_of_index(self):
        """ Проверка: на второй странице должно быть 6 постов. """
        response = self.client.get(reverse('posts:index_page') + '?page=2')
        self.assertEqual(
            len(response.context['page_obj']), SECOND_PAGE_COUNT_POSTS
        )

    def test_first_page_of_group_list(self):
        """ Проверка: количество постов на первой странице равно 10. """
        response = self.client.get(reverse(
            'posts:group_list', kwargs={'slug': self.group.slug}
        ))
        self.assertEqual(
            len(response.context['page_obj']), FIRST_PAGE_COUNT_POSTS
        )

    def test_second_page_of_group_list(self):
        """ Проверка: на второй странице должно быть 6 постов. """
        response = self.client.get(reverse(
            'posts:group_list', kwargs={'slug': self.group.slug}) + '?page=2'
        )
        self.assertEqual(
            len(response.context['page_obj']), SECOND_PAGE_COUNT_POSTS
        )

    def test_first_page_of_profile(self):
        """ Проверка: количество постов на первой странице равно 10. """
        response = self.client.get(reverse(
            'posts:profile', kwargs={'username': self.user.username}
        ))
        self.assertEqual(
            len(response.context['page_obj']), FIRST_PAGE_COUNT_POSTS
        )

    def test_second_page_of_profile(self):
        """ Проверка: на второй странице должно быть 6 постов. """
        response = self.client.get(reverse(
            'posts:profile', kwargs={'username': self.user.username})
            + '?page=2'
        )
        self.assertEqual(
            len(response.context['page_obj']), SECOND_PAGE_COUNT_POSTS
        )
