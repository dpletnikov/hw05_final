from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms
import shutil
import tempfile
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from posts.models import Post, Group, Comment, Follow

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostPagesTests(TestCase):

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
            author=PostPagesTests.user
        )
        cls.post_view = 'posts:post_create'
        cls.post_edit_view = 'posts:post_edit'
        cls.post_comment = 'posts:add_comment'
        cls.public_views = (
            ('posts:index_page', 'posts/index.html'),
            ('posts:group_list', 'posts/group_list.html'),
            ('posts:profile', 'posts/profile.html'),
            ('posts:post_detail', 'posts/post_detail.html'),
        )
        cls.private_views = (
            (cls.post_view, 'posts/create_post.html'),
            (cls.post_edit_view, 'posts/create_post.html')
        )

    def setUp(self):
        self.guest_client = Client()
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTests.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse(PostPagesTests.public_views[0][0]):
                PostPagesTests.public_views[0][1],
            reverse(
                PostPagesTests.public_views[1][0],
                kwargs={'slug': self.group.slug}
            ): PostPagesTests.public_views[1][1],
            reverse(
                PostPagesTests.public_views[2][0],
                kwargs={'username': self.user.username}
            ): PostPagesTests.public_views[2][1],
            reverse(
                PostPagesTests.public_views[3][0],
                kwargs={'post_id': self.post.pk}
            ): PostPagesTests.public_views[3][1],
            reverse(PostPagesTests.post_view):
                PostPagesTests.private_views[0][1],
            reverse(
                PostPagesTests.post_edit_view, kwargs={'post_id': self.post.pk}
            ): PostPagesTests.private_views[1][1],
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            PostPagesTests.public_views[0][0])
        )
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author
        self.assertEqual(post_text_0, 'Тестовый заголовок')
        self.assertEqual(post_author_0, self.user)

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = (self.guest_client.get(reverse(
            PostPagesTests.public_views[1][0],
            kwargs={'slug': self.group.slug}))
        )
        self.assertEqual(
            response.context.get('group').title, 'Тестовая группа')

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = (self.guest_client.get(reverse(
            PostPagesTests.public_views[2][0],
            kwargs={'username': self.user.username})))
        self.assertEqual(response.context.get('author').username, 'auth')

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = (self.guest_client.get(reverse(
            PostPagesTests.public_views[3][0],
            kwargs={'post_id': self.post.pk}))
        )
        self.assertEqual(response.context.get('post').pk, self.post.pk)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                PostPagesTests.post_edit_view,
                kwargs={'post_id': self.post.pk})
        )
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(PostPagesTests.post_view)
        )
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_index_image(self):
        """Image передается в context index page."""
        response = self.guest_client.get(
            reverse(PostPagesTests.public_views[0][0])
        )
        obj = response.context['page_obj'][0]
        self.assertEqual(obj.image, self.post.image)

    def test_post_detail_image(self):
        """Image передается в context post_detail."""
        response = self.guest_client.get(
            reverse(
                PostPagesTests.public_views[3][0],
                kwargs={"post_id": self.post.id})
        )
        obj = response.context['post']
        self.assertEqual(obj.image, self.post.image)

    def test_profile_image(self):
        """Image передается в context profile."""
        response = self.guest_client.get(
            reverse(
                PostPagesTests.public_views[2][0],
                kwargs={'username': self.user.username})
        )
        obj = response.context['page_obj'][0]
        self.assertEqual(obj.image, self.post.image)

    def test_comment_post_detail_view(self):
        """Комментарий появляется на странице поста."""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Текст комментария'
        }
        response = self.authorized_client.post(
            reverse(PostPagesTests.post_comment, args=({self.post.id})),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            PostPagesTests.public_views[3][0],
            kwargs={'post_id': self.post.pk})
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertTrue(
            Comment.objects.filter(
                text='Текст комментария'
            ).exists()
        )

    def test_comment_guest_client(self):
        """Guest не может оставлять комментарии к постам."""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Текст комментария'
        }
        response = self.guest_client.post(
            reverse(PostPagesTests.post_comment, args=({self.post.id})),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            f'/auth/login/?next=/posts/{self.post.id}/comment/'
        )
        self.assertEqual(Comment.objects.count(), comments_count)
        self.assertFalse(
            Comment.objects.filter(
                text='Текст комментария'
            ).exists()
        )


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostImagesTests(TestCase):
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
            author=cls.user,
            text='Тестовый текст',
            group=cls.group
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_image_context_profile(self):
        """Проверка image на создание в БД."""
        post_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response,
                             reverse('posts:profile', kwargs={
                                 'username': self.user.username}))
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                group=self.group.id,
                text='Тестовый текст',
                image=self.post.image
            ).exists()
        )


class FollowTest(TestCase):
    """Проверка работы системы подписок."""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(
            username='Author'
        )
        cls.follower = User.objects.create(
            username='User'
        )

    def test_create_follow_from_follower_to_author(self):
        """Проверка создания подписки."""
        self.assertEqual(Follow.objects.count(), 0)
        client_follower = Client()
        client_follower.force_login(FollowTest.follower)
        client_follower.get(
            reverse(
                'posts:profile_follow',
                args=(FollowTest.author.username,)
            )
        )
        self.assertEqual(Follow.objects.count(), 1)
        follow_obj = Follow.objects.first()
        self.assertEqual(follow_obj.author, FollowTest.author)
        self.assertEqual(follow_obj.user, FollowTest.follower)
        # Повторная подписка не должна пройти
        client_follower.get(
            reverse(
                'posts:profile_follow',
                args=(FollowTest.author.username,)
            )
        )
        self.assertEqual(Follow.objects.count(), 1)
        follows = Follow.objects.filter(
            author=FollowTest.author,
            user=FollowTest.follower)
        self.assertEqual(len(follows), 1)

    def test_delete_follow_from_follower_to_author(self):
        """Проверка удаления подписки."""
        self.assertEqual(Follow.objects.count(), 0)
        Follow.objects.create(
            author=FollowTest.author,
            user=FollowTest.follower
        )
        self.assertEqual(Follow.objects.count(), 1)
        client_follower = Client()
        client_follower.force_login(FollowTest.follower)
        client_follower.get(
            reverse(
                'posts:profile_unfollow',
                args=(FollowTest.author.username,)
            )
        )
        self.assertEqual(Follow.objects.count(), 0)
        follows = Follow.objects.filter(
            author=FollowTest.author,
            user=FollowTest.follower)
        self.assertFalse(follows)
