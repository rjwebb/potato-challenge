from django import forms
from django.contrib.auth import get_user_model

from crispy_forms_foundation.forms import FoundationModelForm

from .models import Project, Ticket


class BaseTrackerForm(FoundationModelForm):
    def __init__(self, user=None, title=None, *args, **kwargs):
        self.title = title
        self.user = user

        super(BaseTrackerForm, self).__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs['placeholder'] = field.label

    def save(self, *args, **kwargs):
        commit = kwargs.pop('commit', True)
        instance = super(BaseTrackerForm, self).save(
            commit=False, *args, **kwargs)

        self.pre_save(instance)

        if commit:
            instance.save()

        return instance

    def pre_save(self, instance):
        pass


class ProjectForm(BaseTrackerForm):
    class Meta:
        model = Project
        fields = ('title',)

    def pre_save(self, instance):
        instance.created_by = self.user

class EmailChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return obj.email

class TicketForm(BaseTrackerForm):
    assignees = EmailChoiceField(queryset=None, required=False)
    assignees.help_text = ''

    class Meta:
        model = Ticket
        fields = ('title', 'description', 'assignees',)

    def __init__(self, project=None, *args, **kwargs):
        self.project = project
        super(TicketForm, self).__init__(*args, **kwargs)


        self.fields['assignees'].queryset = get_user_model().objects.all()

    def clean(self):
        super(TicketForm, self).clean()

        # prevent this form from changing the project ID of this ticket
        try:
            t = Ticket.objects.get(pk=self.instance.id)
            if t.project != self.project:
                raise forms.ValidationError("cannot change the project "
                                            "of this ticket through this form!")
        except Ticket.DoesNotExist:
            pass

    def pre_save(self, instance):
        instance.created_by = self.user
        instance.project = self.project
