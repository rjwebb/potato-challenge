from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView, CreateView, DeleteView, UpdateView, ListView

from .forms import ProjectForm, TicketForm
from .models import Project, Ticket


class ProjectContextMixin(object):
    project = None

    def get_project(self):
        if not self.project:
            self.project = get_object_or_404(Project, pk=self.kwargs['project_id'])

        return self.project

    def get_context_data(self, **kwargs):
        context = super(ProjectContextMixin, self).get_context_data(**kwargs)
        context['current_project'] = self.get_project()
        return context


class MyTicketsView(TemplateView):
    template_name = "site/my_tickets.html"

    def get_context_data(self):
        if self.request.user.is_authenticated():
            tickets = (
                Ticket.objects
                .filter(assignees=self.request.user.pk)
                .order_by('-modified')
            )
        else:
            tickets = []

        return {
            'tickets': tickets
        }


my_tickets_view = MyTicketsView.as_view()


class ProjectListView(ListView):
    model = Project
    template_name = "site/project_list.html"

    def get_context_data(self, **kwargs):
        context_data = super(ProjectListView, self).get_context_data(**kwargs)

        # only need to put projects that have tickets assigned to the user,
        # if the user is logged in
        if hasattr(self.request, 'user') and self.request.user.is_authenticated():
            # the IDs of all of the tickets assigned to the user
            user_ticket_ids = list(self.request.user.tickets.values_list('id', flat=True))

            # projects with tickets assigned to the user
            projects_for_user = []

            # projects with no tickets assigned to the user
            projects_not_for_user = []

            for p in context_data['object_list']:
                # filter tickets assigned to the user
                assigned_tickets = p.tickets.filter(id__in=user_ticket_ids)

                # if there are any such tickets
                if assigned_tickets.exists():
                    projects_for_user.append(p)
                else:
                    projects_not_for_user.append(p)

            # put the projects with tickets assigned to the user first
            context_data['object_list'] = projects_for_user + projects_not_for_user

        return context_data

project_list_view = ProjectListView.as_view()


class CreateProjectView(CreateView):
    model = Project
    form_class = ProjectForm
    template_name = "site/project_form.html"

    def get_success_url(self):
        return reverse("project-list")

    def get_form_kwargs(self):
        kwargs = super(CreateProjectView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['title'] = 'Create project'
        return kwargs


create_project_view = login_required(CreateProjectView.as_view())


class UpdateProjectView(ProjectContextMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    pk_url_kwarg = 'project_id'
    template_name = "site/project_form.html"

    def get_success_url(self):
        return reverse("project-list")

    def get_form_kwargs(self):
        kwargs = super(UpdateProjectView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['title'] = "Edit {0}".format(self.object.title)
        return kwargs


update_project_view = login_required(UpdateProjectView.as_view())


class ProjectView(ProjectContextMixin, TemplateView):
    template_name = "site/project_detail.html"

    def get_context_data(self, **kwargs):
        context = super(ProjectView, self).get_context_data(**kwargs)
        project = self.get_project()
        context.update({
            "project": project,
            "tickets": project.tickets.all()
        })
        return context


project_view = ProjectView.as_view()


class CreateTicketView(ProjectContextMixin, CreateView):
    model = Ticket
    form_class = TicketForm
    template_name = "site/ticket_form.html"

    def get_success_url(self):
        return reverse("project-detail", kwargs={"project_id": self.kwargs['project_id']})

    def get_form_kwargs(self):
        kwargs = super(CreateTicketView, self).get_form_kwargs()
        kwargs['project'] = self.get_project()
        kwargs['user'] = self.request.user
        kwargs['title'] = 'Create ticket'
        return kwargs


create_ticket_view = login_required(CreateTicketView.as_view())


class UpdateTicketView(ProjectContextMixin, UpdateView):
    model = Ticket
    form_class = TicketForm
    pk_url_kwarg = 'ticket_id'
    template_name = "site/ticket_form.html"

    def get_success_url(self):
        return reverse("project-detail", kwargs={"project_id": self.kwargs['project_id']})

    def get_form_kwargs(self):
        kwargs = super(UpdateTicketView, self).get_form_kwargs()
        kwargs['project'] = self.get_project()
        kwargs['user'] = self.request.user
        kwargs['title'] = "Edit {0}".format(self.object.title)
        return kwargs


update_ticket_view = login_required(UpdateTicketView.as_view())


class DeleteTicketView(ProjectContextMixin, DeleteView):
    model = Ticket
    pk_url_kwarg = 'ticket_id'

    def get_success_url(self):
        return reverse("project-detail", kwargs={"project_id": self.kwargs['project_id']})

delete_ticket_view = login_required(DeleteTicketView.as_view())
