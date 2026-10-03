from html.parser import HTMLParser

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from django.utils.html import escape

from .models import Comment, MainContent


class FormParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.forms = []
        self.current = None
        self.nested = False

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if tag == 'form':
            self.nested = self.nested or self.current is not None
            self.current = {'attrs': attrs, 'inputs': []}
            self.forms.append(self.current)
        elif tag == 'input' and self.current is not None:
            self.current['inputs'].append(attrs)

    def handle_endtag(self, tag):
        if tag == 'form':
            self.current = None


class ContentAndCommentTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_user(username='owner')
        cls.other = get_user_model().objects.create_user(username='other')
        cls.content = MainContent.objects.create(
            title='Example content', content='The actual content body',
            pub_date=timezone.now(),
        )
        cls.other_content = MainContent.objects.create(
            title='Other content', content='Another body', pub_date=timezone.now(),
        )

    def setUp(self):
        self.detail_url = reverse('detail', args=[self.content.pk])
        self.create_url = reverse('comment_create', args=[self.content.pk])

    def make_comment(self):
        return Comment.objects.create(
            author=self.owner, content_list=self.content, content='Original comment',
        )

    def test_detail_renders_content_body(self):
        response = self.client.get(self.detail_url)
        self.assertContains(response, self.content.content)
        self.assertNotContains(response, '{{content_list.content}')

    def test_detail_escapes_content(self):
        self.content.content = '<script>alert("example")</script>'
        self.content.save()
        response = self.client.get(self.detail_url)
        self.assertContains(response, '&lt;script&gt;')
        self.assertNotContains(response, '<script>')

    def test_missing_content_returns_404(self):
        response = self.client.get(reverse('detail', args=[999999]))
        self.assertEqual(response.status_code, 404)

    def test_comment_text_is_escaped_in_detail_and_update_form(self):
        comment = self.make_comment()
        comment.content = '</textarea><script>alert("example")</script>'
        comment.save()
        self.client.force_login(self.owner)
        for url in (self.detail_url, reverse('comment_update', args=[comment.pk])):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertContains(response, escape(comment.content))
                self.assertNotContains(response, '<script>')

    def test_anonymous_create_requires_login_without_mutation(self):
        for method in ('get', 'post'):
            with self.subTest(method=method):
                data = {'content': 'Attempt'} if method == 'post' else {}
                response = getattr(self.client, method)(self.create_url, data)
                self.assertRedirects(
                    response, reverse('accounts:login') + '?next=' + self.create_url,
                    fetch_redirect_response=False,
                )
                self.assertEqual(Comment.objects.count(), 0)

    def test_create_get_displays_form_without_mutation(self):
        self.client.force_login(self.owner)
        response = self.client.get(self.create_url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['form'].is_bound)
        self.assertEqual(Comment.objects.count(), 0)

    def test_valid_create_binds_author_and_parent(self):
        self.client.force_login(self.owner)
        response = self.client.post(self.create_url, {
            'content': 'New comment', 'author': self.other.pk,
            'content_list': self.other_content.pk,
        })
        self.assertRedirects(response, self.detail_url)
        comment = Comment.objects.get()
        self.assertEqual(comment.author, self.owner)
        self.assertEqual(comment.content_list, self.content)
        self.assertEqual(comment.content, 'New comment')

    def test_invalid_create_preserves_bound_errors_without_mutation(self):
        self.client.force_login(self.owner)
        for value in ('', '   '):
            with self.subTest(value=value):
                response = self.client.post(self.create_url, {'content': value})
                self.assertEqual(response.status_code, 200)
                form = response.context['form']
                self.assertTrue(form.is_bound)
                self.assertIn('content', form.errors)
                self.assertEqual(form.data['content'], value)
                self.assertContains(response, str(form.errors['content'][0]))
                self.assertEqual(Comment.objects.count(), 0)

    def test_missing_create_parent_returns_404(self):
        self.client.force_login(self.owner)
        response = self.client.post(reverse('comment_create', args=[999999]), {'content': 'Attempt'})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Comment.objects.count(), 0)

    def test_create_rejects_unsupported_method(self):
        self.client.force_login(self.owner)
        response = self.client.put(self.create_url, 'content=Attempt')
        self.assertEqual(response.status_code, 405)
        self.assertEqual(Comment.objects.count(), 0)

    def test_owner_update_get_prefills_form_and_action(self):
        comment = self.make_comment()
        before = comment.modify_date
        self.client.force_login(self.owner)
        url = reverse('comment_update', args=[comment.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form']['content'].value(), comment.content)
        self.assertContains(response, f'action="{url}"')
        self.assertNotContains(response, '{% url')
        comment.refresh_from_db()
        self.assertEqual(comment.modify_date, before)
        self.assertEqual(comment.content, 'Original comment')

    def test_owner_update_post_preserves_author_and_parent(self):
        comment = self.make_comment()
        self.client.force_login(self.owner)
        response = self.client.post(reverse('comment_update', args=[comment.pk]), {
            'content': 'Updated comment', 'author': self.other.pk,
            'content_list': self.other_content.pk,
        })
        self.assertRedirects(response, self.detail_url)
        comment.refresh_from_db()
        self.assertEqual(comment.content, 'Updated comment')
        self.assertEqual(comment.author, self.owner)
        self.assertEqual(comment.content_list, self.content)
        self.assertEqual(Comment.objects.count(), 1)

    def test_invalid_update_preserves_bound_errors_without_mutation(self):
        comment = self.make_comment()
        before = comment.modify_date
        self.client.force_login(self.owner)
        for value in ('', '   '):
            with self.subTest(value=value):
                response = self.client.post(reverse('comment_update', args=[comment.pk]), {'content': value})
                self.assertEqual(response.status_code, 200)
                form = response.context['form']
                self.assertTrue(form.is_bound)
                self.assertEqual(form.data['content'], value)
                self.assertIn('content', form.errors)
                self.assertContains(response, str(form.errors['content'][0]))
                comment.refresh_from_db()
                self.assertEqual(comment.content, 'Original comment')
                self.assertEqual(comment.modify_date, before)

    def test_other_user_cannot_update(self):
        comment = self.make_comment()
        before = comment.modify_date
        self.client.force_login(self.other)
        for method in ('get', 'post'):
            with self.subTest(method=method):
                response = getattr(self.client, method)(reverse('comment_update', args=[comment.pk]), {'content': 'Attempt'})
                self.assertEqual(response.status_code, 403)
                comment.refresh_from_db()
                self.assertEqual(comment.content, 'Original comment')
                self.assertEqual(comment.modify_date, before)

    def test_anonymous_update_requires_login_without_mutation(self):
        comment = self.make_comment()
        url = reverse('comment_update', args=[comment.pk])
        for method in ('get', 'post'):
            with self.subTest(method=method):
                data = {'content': 'Attempt'} if method == 'post' else {}
                response = getattr(self.client, method)(url, data)
                self.assertRedirects(response, reverse('accounts:login') + '?next=' + url, fetch_redirect_response=False)
                comment.refresh_from_db()
                self.assertEqual(comment.content, 'Original comment')

    def test_missing_update_returns_404(self):
        self.client.force_login(self.owner)
        for method in ('get', 'post'):
            with self.subTest(method=method):
                response = getattr(self.client, method)(reverse('comment_update', args=[999999]), {'content': 'Attempt'})
                self.assertEqual(response.status_code, 404)

    def test_update_rejects_unsupported_method_without_mutation(self):
        comment = self.make_comment()
        self.client.force_login(self.owner)
        response = self.client.put(reverse('comment_update', args=[comment.pk]), 'content=Attempt')
        self.assertEqual(response.status_code, 405)
        comment.refresh_from_db()
        self.assertEqual(comment.content, 'Original comment')

    def test_owner_delete_post_deletes_only_target(self):
        comment = self.make_comment()
        survivor = Comment.objects.create(author=self.owner, content_list=self.content, content='Keep this')
        self.client.force_login(self.owner)
        response = self.client.post(reverse('comment_delete', args=[comment.pk]))
        self.assertRedirects(response, self.detail_url)
        self.assertFalse(Comment.objects.filter(pk=comment.pk).exists())
        self.assertTrue(Comment.objects.filter(pk=survivor.pk).exists())

    def test_delete_get_and_head_do_not_mutate(self):
        comment = self.make_comment()
        self.client.force_login(self.owner)
        for method in ('get', 'head', 'put'):
            with self.subTest(method=method):
                response = getattr(self.client, method)(reverse('comment_delete', args=[comment.pk]))
                self.assertEqual(response.status_code, 405)
                self.assertTrue(Comment.objects.filter(pk=comment.pk).exists())

    def test_other_user_cannot_delete(self):
        comment = self.make_comment()
        self.client.force_login(self.other)
        response = self.client.post(reverse('comment_delete', args=[comment.pk]))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Comment.objects.filter(pk=comment.pk).exists())

    def test_anonymous_delete_requires_login_without_mutation(self):
        comment = self.make_comment()
        url = reverse('comment_delete', args=[comment.pk])
        response = self.client.post(url)
        self.assertRedirects(response, reverse('accounts:login') + '?next=' + url, fetch_redirect_response=False)
        self.assertTrue(Comment.objects.filter(pk=comment.pk).exists())

    def test_missing_delete_returns_404(self):
        self.client.force_login(self.owner)
        response = self.client.post(reverse('comment_delete', args=[999999]))
        self.assertEqual(response.status_code, 404)

    def test_detail_uses_owner_only_delete_post_form(self):
        comment = self.make_comment()
        url = reverse('comment_delete', args=[comment.pk])
        self.client.force_login(self.owner)
        response = self.client.get(self.detail_url)
        self.assertContains(response, f'action="{url}"')
        self.assertNotContains(response, f'href="{url}"')
        self.assertContains(response, 'name="csrfmiddlewaretoken"')
        self.assertContains(response, self.owner.username)
        self.assertContains(response, comment.content)
        parser = FormParser()
        parser.feed(response.content.decode())
        self.assertFalse(parser.nested)
        delete_forms = [form for form in parser.forms if form['attrs'].get('action') == url]
        self.assertEqual(len(delete_forms), 1)
        self.assertEqual(delete_forms[0]['attrs'].get('method'), 'post')
        csrf_inputs = [field for field in delete_forms[0]['inputs'] if field.get('name') == 'csrfmiddlewaretoken']
        self.assertEqual(len(csrf_inputs), 1)
        self.assertTrue(csrf_inputs[0].get('value'))
        self.client.force_login(self.other)
        self.assertNotContains(self.client.get(self.detail_url), f'action="{url}"')
        self.client.logout()
        self.assertNotContains(self.client.get(self.detail_url), f'action="{url}"')

    def test_create_requires_csrf_and_accepts_valid_token(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.owner)
        response = client.post(self.create_url, {'content': 'Attempt'})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Comment.objects.count(), 0)
        client.get(self.detail_url)
        response = client.post(self.create_url, {
            'content': 'With token', 'csrfmiddlewaretoken': client.cookies['csrftoken'].value,
        })
        self.assertRedirects(response, self.detail_url)
        self.assertEqual(Comment.objects.get().author, self.owner)

    def test_update_requires_csrf_and_accepts_valid_token(self):
        comment = self.make_comment()
        url = reverse('comment_update', args=[comment.pk])
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.owner)
        self.assertEqual(client.post(url, {'content': 'Attempt'}).status_code, 403)
        comment.refresh_from_db()
        self.assertEqual(comment.content, 'Original comment')
        client.get(url)
        response = client.post(url, {
            'content': 'With token', 'csrfmiddlewaretoken': client.cookies['csrftoken'].value,
        })
        self.assertRedirects(response, self.detail_url)
        comment.refresh_from_db()
        self.assertEqual(comment.content, 'With token')

    def test_delete_requires_csrf_and_accepts_valid_token(self):
        comment = self.make_comment()
        url = reverse('comment_delete', args=[comment.pk])
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.owner)
        self.assertEqual(client.post(url).status_code, 403)
        self.assertTrue(Comment.objects.filter(pk=comment.pk).exists())
        client.get(self.detail_url)
        response = client.post(url, {'csrfmiddlewaretoken': client.cookies['csrftoken'].value})
        self.assertRedirects(response, self.detail_url)
        self.assertFalse(Comment.objects.filter(pk=comment.pk).exists())

    def test_admin_comment_search_uses_author_username(self):
        comment = self.make_comment()
        staff = get_user_model().objects.create_superuser(username='audit-admin')
        self.client.force_login(staff)
        response = self.client.get(reverse('admin:product_comment_changelist'), {'q': self.owner.username})
        self.assertContains(response, comment.content)
