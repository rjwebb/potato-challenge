from django.test import Client, TestCase
from django.contrib.auth import get_user_model

from django.test.client import RequestFactory

from .views import project_list_view, create_project_view
from .models import Project, Ticket


User = get_user_model()

"""
# add a bunch of users
self.user1 = User.objects.create_user('user1', 'user1@example.com')
self.user2 = User.objects.create_user('user2', 'user2@example.com')
self.user3 = User.objects.create_user('user3', 'user3@example.com')
self.user4 = User.objects.create_user('user4', 'user4@example.com')

# add a bunch of projects
self.project1 = Project.objects.create(

# add a bunch of tickets
"""

class BaseTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()


class ProjectListViewTest(BaseTestCase):
    def test_view_no_projects(self):
        req = self.factory.get('/')
        resp = project_list_view(req)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(list(resp.context_data['project_list']), [])

    def test_view_one_project(self):
        user = User.objects.create_user('cool guy', 'coolguy@example.com')
        proj = Project.objects.create(title='Library Thinger', created_by=user)

        req = self.factory.get('/')
        resp = project_list_view(req)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(list(resp.context_data['project_list']), [proj])


class ProjectCreateViewTest(BaseTestCase):
    def setUp(self):
        super(ProjectCreateViewTest, self).setUp()

        self.user = User.objects.create_user('cool guy', 'coolguy@example.com')

    def test_create_project_success(self):
        req = self.factory.post('/', {'title':'Burping Competition'})
        req.user = self.user
        resp = create_project_view(req)

        # 302 because it redirects to the project list page on success
        self.assertEqual(resp.status_code, 302)

        # get the created project
        proj = Project.objects.get(title='Burping Competition')

        self.assertEqual(proj.created_by, self.user)
        self.assertEqual(list(Project.objects.all()), [proj])

    def test_create_project_no_title(self):
        req = self.factory.post('/', {})
        req.user = self.user
        resp = create_project_view(req)

        # 200 means failure because if it was a success,
        # it would redirect to the project list page
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(list(Project.objects.all()), [])

    def test_create_project_no_user(self):
        req = self.factory.post('/', {'title':'Burping Competition'})
        # don't add the user

        # this should raise an error
        with self.assertRaises(AttributeError):
            resp = create_project_view(req)

