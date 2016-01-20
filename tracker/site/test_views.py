from django.contrib.auth import get_user_model
from django.http import Http404
from django.test import TestCase
from django.test.client import RequestFactory

from .models import Project, Ticket
from .views import (
    project_list_view,
    create_project_view,
    update_project_view,
    project_view,

    my_tickets_view,
    create_ticket_view,
    update_ticket_view,
    delete_ticket_view,
)


User = get_user_model()


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

        # this should raise an error since it is an
        # invalid request
        with self.assertRaises(AttributeError):
            create_project_view(req)


class ProjectUpdateViewTest(BaseTestCase):
    def setUp(self):
        super(ProjectUpdateViewTest, self).setUp()

        self.user = User.objects.create_user('cool guy', 'coolguy@example.com')

        self.user2 = User.objects.create_user('nice person', 'niceperson@example.com')

        self.project = Project.objects.create(
            title='Library Thinger',
            created_by=self.user
        )

    def test_success(self):
        # test correctly updating a project
        project_id = self.project.pk

        req = self.factory.post('/', {'title':'Burping Competition'})
        req.user = self.user2

        resp = update_project_view(req, project_id=project_id)

        # redirect to project list page
        self.assertEqual(resp.status_code, 302)

        # assert that the object was changed
        p = Project.objects.get(pk=project_id)
        self.assertEqual(p.title, 'Burping Competition')
        self.assertEqual(p.created_by, self.user2)

    def test_no_title(self):
        project_id = self.project.pk

        req = self.factory.post('/', {})
        req.user = self.user2

        resp = update_project_view(req, project_id=project_id)

        # 200 means failure because if it was a success,
        # it would redirect to the project list page
        self.assertEqual(resp.status_code, 200)

        # assert that the object wasn't changed
        p = Project.objects.get(pk=project_id)
        self.assertEqual(p.title, 'Library Thinger')
        self.assertEqual(p.created_by, self.user)

    def test_no_user(self):
        project_id = self.project.pk

        req = self.factory.post('/', {})

        with self.assertRaises(AttributeError):
            update_project_view(req, project_id=project_id)


class ProjectViewTest(BaseTestCase):
    def setUp(self):
        super(ProjectViewTest, self).setUp()

        self.user = User.objects.create_user('cool guy', 'coolguy@example.com')

        self.project = Project.objects.create(
            title='Library Thinger',
            created_by=self.user
        )

    def test_success(self):
        project_id = self.project.pk

        req = self.factory.get('/')
        req.user = self.user

        resp = project_view(req, project_id=project_id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.project, resp.context_data['project'])

    def test_project_not_found(self):
        project_id = self.project.pk

        self.project.delete()

        req = self.factory.get('/')
        req.user = self.user

        with self.assertRaises(Http404):
            project_view(req, project_id=project_id)


class MyTicketsViewTest(BaseTestCase):

    # This test creates three tickets, and three users
    # It then tests that the right tickets are visible to each user

    def setUp(self):
        super(MyTicketsViewTest, self).setUp()

        self.user1 = User.objects.create_user('first user', 'user1@example.com')
        self.user2 = User.objects.create_user('second user', 'user2@example.com')
        self.user3 = User.objects.create_user('third user', 'user3@example.com')

        # create a project
        self.project = Project.objects.create(
            title='Library Thinger',
            created_by=self.user1
        )

        # create some tickets
        self.ticket1 = Ticket.objects.create(
            title='ticket 1',
            project=self.project,
            created_by=self.user1,
            assignees=[self.user1, self.user2]
        )
        self.ticket2 = Ticket.objects.create(
            title='ticket 2',
            project=self.project,
            created_by=self.user1,
            assignees=[self.user1]
        )
        self.ticket3 = Ticket.objects.create(
            title='ticket 3',
            project=self.project,
            created_by=self.user1,
            assignees=[]
        )

    def test_user1_view(self):
        req = self.factory.get('/')
        req.user = self.user1

        resp = my_tickets_view(req)
        assigned_tickets = resp.context_data['tickets']

        self.assertIn(self.ticket1, assigned_tickets)
        self.assertIn(self.ticket2, assigned_tickets)
        self.assertNotIn(self.ticket3, assigned_tickets)

    def test_user2_view(self):
        req = self.factory.get('/')
        req.user = self.user2

        resp = my_tickets_view(req)
        assigned_tickets = resp.context_data['tickets']

        self.assertIn(self.ticket1, assigned_tickets)
        self.assertNotIn(self.ticket2, assigned_tickets)
        self.assertNotIn(self.ticket3, assigned_tickets)

    def test_user3_view(self):
        req = self.factory.get('/')
        req.user = self.user3

        resp = my_tickets_view(req)
        assigned_tickets = resp.context_data['tickets']

        self.assertNotIn(self.ticket1, assigned_tickets)
        self.assertNotIn(self.ticket2, assigned_tickets)
        self.assertNotIn(self.ticket3, assigned_tickets)


class CreateTicketViewTest(BaseTestCase):
    def setUp(self):
        super(CreateTicketViewTest, self).setUp()

        self.user = User.objects.create_user('first user', 'user1@example.com')
        self.project = Project.objects.create(
            title='Library Thinger',
            created_by=self.user
        )

    def test_success(self):
        req = self.factory.post('/', {
            'title' : 'ticket 1',
        })
        req.user = self.user

        resp = create_ticket_view(req, project_id=self.project.pk)

        # assert that it succeeded
        self.assertEquals(resp.status_code, 302)

        # try to get the new ticket
        # if it hasn't been created, this will fail
        Ticket.objects.get(title='ticket 1', project=self.project)

    def test_no_title(self):
        req = self.factory.post('/')
        req.user = self.user

        resp = create_ticket_view(req, project_id=self.project.pk)
        # failure
        self.assertEquals(resp.status_code, 200)

    def test_no_user(self):
        req = self.factory.post('/', {
            'title' : 'ticket 1',
        })

        with self.assertRaises(AttributeError):
            create_ticket_view(req, project_id=self.project.pk)


class UpdateTicketViewTest(BaseTestCase):
    def setUp(self):
        super(UpdateTicketViewTest, self).setUp()

        self.user = User.objects.create_user('cool guy', 'coolguy@example.com')

        self.user2 = User.objects.create_user('nice person', 'niceperson@example.com')

        self.project = Project.objects.create(
            title='Library Thinger',
            created_by=self.user
        )

        self.project2 = Project.objects.create(
            title='Other Machine',
            created_by=self.user
        )


        self.ticket = Ticket.objects.create(
            title='task 1',
            created_by=self.user,
            project=self.project
        )

    def test_success(self):
        req = self.factory.post('/', {
            'title' : 'new task 1',
            'description' : 'do bad things'
        })
        req.user = self.user2

        resp = update_ticket_view(req,
                                  project_id=self.project.pk,
                                  ticket_id=self.ticket.pk)

        new_ticket = Ticket.objects.get(pk=self.ticket.pk)

        self.assertEquals(resp.status_code, 302)
        self.assertEquals(new_ticket.title, 'new task 1')
        self.assertEquals(new_ticket.description, 'do bad things')
        self.assertEquals(new_ticket.created_by, self.user2)

    def test_no_project_id(self):
        req = self.factory.post('/', {
            'title' : 'new task 1',
            'description' : 'do bad things'
        })
        req.user = self.user2

        with self.assertRaises(KeyError):
            update_ticket_view(req, ticket_id=self.ticket.pk)

    def test_no_ticket_id(self):
        req = self.factory.post('/', {
            'title' : 'new task 1',
            'description' : 'do bad things'
        })
        req.user = self.user2

        with self.assertRaises(AttributeError):
            update_ticket_view(req, project_id=self.project.pk)


    def test_change_project_id_fail(self):
        req = self.factory.post('/', {
            'title' : 'new task 1',
            'description' : 'do bad things'
        })
        req.user = self.user2

        resp = update_ticket_view(req,
                                  project_id=self.project2.pk,
                                  ticket_id=self.ticket.pk)

        new_ticket = Ticket.objects.get(pk=self.ticket.pk)

        # this should fail, because update_ticket_view cannot
        # be used to change the project for a ticket
        self.assertEquals(resp.status_code, 200)
        self.assertEquals(new_ticket.title, 'task 1')
        self.assertEquals(new_ticket.description, '')
        self.assertEquals(new_ticket.created_by, self.user)


class DeleteTicketViewTest(BaseTestCase):
    def setUp(self):
        super(DeleteTicketViewTest, self).setUp()

        self.user = User.objects.create_user('cool guy', 'coolguy@example.com')

        self.project = Project.objects.create(
            title='Library Thinger',
            created_by=self.user
        )

        self.ticket = Ticket.objects.create(
            title='task 1',
            created_by=self.user,
            project=self.project
        )


    def test_success(self):
        req = self.factory.post('/')
        req.user = self.user

        resp = delete_ticket_view(req,
                                  project_id=self.project.pk,
                                  ticket_id=self.ticket.pk)

        self.assertEquals(resp.status_code, 302)
        self.assertNotIn(self.ticket, Ticket.objects.all())

    def test_delete_twice_fail(self):
        # try to delete the thing once, succeed
        self.test_success()

        # try to delete it again
        req = self.factory.post('/')
        req.user = self.user

        with self.assertRaises(Http404):
            delete_ticket_view(req,
                               project_id=self.project.pk,
                               ticket_id=self.ticket.pk)
