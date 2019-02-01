import re

from django import forms

from sdios_lti.models import Consumer, Setting, EnvironmentMap


class CreateConsumerForm(forms.ModelForm):
    """
    Form for creating a new consumer.
    """

    class Meta:
        model = Consumer
        fields = ["name", "key", "secret"]


class ManageSettingsForm(forms.ModelForm):
    """
    Form for updating API settings.
    """
    sdios_password = forms.CharField(label="SDI OS Password", widget=forms.PasswordInput())
    def clean_sdios_url(self):
        url = self.cleaned_data["sdios_url"]

        # If the user added http://, https://, or a trailing slash,
        # strip them.
        url = re.sub(r"^https?://", "", url, flags=re.I)
        url = re.sub(r"/+$", "", url)

        return url

    class Meta:
        model = Setting
        fields = ["sdios_url", "sdios_username", "sdios_password", "client_id", "client_secret"]


class ExportEnvironmentForm(forms.ModelForm):
    """
    Form for exporting SDIs to LTI with fields populated
    in the front-end.
    """

    sdios_environment_uuid = forms.CharField(widget=forms.HiddenInput)

    class Meta:
        model = EnvironmentMap
        fields = ["name", "lti_environment_key", "sdios_environment_uuid"]
