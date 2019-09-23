import functools

from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt

import sdios_lti.utils
from sdios_lti.api import APIRequest
from sdios_lti.decorators import ajax_required
from sdios_lti.forms import CreateConsumerForm, ManageSettingsForm, ExportEnvironmentForm
from sdios_lti.models import EnvironmentMap, UserMap, Consumer, Setting


HTTP_UNAUTHORIZED = 401


# This is exempt from cross-site request forgery protection, because the
# LMS cannot pass CSRF tokens.
@csrf_exempt
def lti(request):
    """
    Process an LTI request.  This must be an HTTP POST from an
    LTI-compatible LMS.
    """
    if request.method != "POST":
        return HttpResponseBadRequest("POST data only")

    try:
        sdios_lti.utils.validate_signature(request.POST, request.META, request.body, reverse("lti"))
    except sdios_lti.utils.BadRequest as err:
        return HttpResponseBadRequest(f"{err}")
    except sdios_lti.utils.UnauthorizedRequest as err:
        return HttpResponse(f"{err}", status=HTTP_UNAUTHORIZED)

    try:
        environment_key = request.POST["custom_sdi"]
        consumer_key = request.POST["oauth_consumer_key"]
        user_id = request.POST["user_id"]
    except KeyError:
        return HttpResponseBadRequest("missing parameters")

    try:
        api = APIRequest()
    except Exception:
        return HttpResponseBadRequest("unable to connect to SDI OS")

    try:
        environment = EnvironmentMap.objects.get(lti_environment_key=environment_key)
        usermap = UserMap.get(api, consumer_key, user_id)
    except (Exception, KeyError, EnvironmentMap.DoesNotExist, UserMap.DoesNotExist):
        return HttpResponseBadRequest("cannot look up information")

    try:
        url = sdios_lti.models.UserMap.login(api, usermap, environment)
    except Exception:
        return HttpResponseBadRequest("cannot log in")


    return HttpResponseRedirect(url)


def login(request):
    """
    Authenticate user and redirect to requested page on success.
    """

    if request.method == "POST":
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")
        redirect_to = request.POST.get("next", "")
        user = authenticate(username=username, password=password)

        if user is not None:
            if user.is_active:
                auth_login(request, user)
                return HttpResponseRedirect(redirect_to)

        return render(request, "login.html", {"error": True, "next": redirect_to})

    else:
        if request.user.is_authenticated:
            return redirect("index")
        redirect_to = request.GET.get("next", "")
        return render(request, "login.html", {"error": False, "next": redirect_to})


@login_required(login_url="/login/")
def index(request):
    """
    Redirect authenticated user to homepage.
    """

    return render(request, "index.html")


@login_required(login_url="/login/")
def logout(request):
    """
    Log out user and redirect back to login screen.
    """

    auth_logout(request)
    return redirect("login")


@login_required(login_url="/login/")
def view_environments(request, form=ExportEnvironmentForm(), validation_error=False):
    """
    Retrieve all environments via API. Check if they exist as LTI mapped
    environments.  Then sort according to user and user"s environments.
    """

    api = APIRequest()
    environments = api.get("sdis")

    usermap = {}

    for environment in environments:
        if environment["user"] not in usermap:
            usermap[environment["user"]] = api.get("accounts/users/{}".format(environment["user"]))
        environment["user"] = usermap[environment["user"]]

        try:
            lti_environment = EnvironmentMap.objects.get(sdios_environment_uuid=environment["sdi_id"])
            environment["lti_status"] = True
            environment["lti_name"] = lti_environment.name
            environment["lti_key"] = lti_environment.lti_environment_key
        except EnvironmentMap.DoesNotExist:
            environment["lti_status"] = False

    def compare(obj_a, obj_b):
        def cmp_priv(a, b):
            return (a > b) - (a < b)

        if obj_a["user"] == obj_b["user"]:
            return cmp_priv(obj_a["name"], obj_b["name"])

        return cmp_priv(obj_a["user"]["username"], obj_b["user"]["username"])

    environments = sorted(environments, key=functools.cmp_to_key(compare))

    # Filter out environments belonging to SDI OS LTI users
    # since it makes no sense to export these.
    sdios_usernames = [usermap.sdios_username for usermap in UserMap.objects.all()]
    environments = [environment for environment in environments if environment["user"]["username"] not in sdios_usernames]

    pkg = {
        "sdis": environments,
        "form": form,
        "error": validation_error,
    }
    return render(request, "environments.html", pkg)


@login_required(login_url="/login/")
def export_environment(request):
    """
    Enable LTI access for the requested environment.
    """

    if request.method == "POST":
        form = ExportEnvironmentForm(request.POST)

        if form.is_valid():
            form.save()
        else:
            # Export environment form with validation errors.
            return view_environments(request, form=form, validation_error=True)

        return redirect("sdis")


@login_required(login_url="/login/")
def remove_lti_access(request, sdi_id):
    """
    Remove LTI access from requested environment,
    """

    try:
        lti_environment = EnvironmentMap.objects.get(sdios_environment_uuid=sdi_id)
        lti_environment.delete()
    except KeyError:
        return HttpResponseBadRequest("LTI Container does not exist")
    return redirect("sdis")


@login_required(login_url="/login/")
def view_consumers(request):
    """
    Send list of consumers and form to add new ones.
    """

    consumers = Consumer.objects.all()
    form = CreateConsumerForm()
    pkg = {
        "consumers": consumers,
        "form": form
    }
    return render(request, "consumers.html", pkg)


@login_required(login_url="/login/")
def add_consumer(request):
    """
    Validate consumer form and a new consumer if valid.
    """

    if request.method == "POST":
        form = CreateConsumerForm(request.POST)

        if form.is_valid():
            form.save()
        else:
            pkg = {
                "consumers": Consumer.objects.all(),
                "form": form
            }
            return render(request, "consumers.html", pkg)
        return redirect("consumers")


@ajax_required
@login_required(login_url="/login/")
def delete_consumer(request):
    """
    Delete requested consumer.
    """

    try:
        consumer = Consumer.objects.get(id=request.POST["consumer_id"])
        consumer.delete()
    except KeyError:
        return HttpResponseBadRequest("Consumer does not exist")
    return HttpResponse()


@login_required(login_url="/login/")
def manage_settings(request):
    """
    Update API settings.
    """

    settings = Setting.get()

    if request.method == "POST":
        form = ManageSettingsForm(request.POST, instance=settings)

        if form.is_valid():
            form.save()
            # Look the form up again, because ManageSettingsForm might
            # modify the data.
            form = ManageSettingsForm(instance=Setting.get())
    else:
        form = ManageSettingsForm(instance=settings)

    return render(request, "settings.html", {"form": form})


@login_required(login_url="/login/")
def view_users(request):
    """
    View SDI OS LTI mapped users.
    """

    users = UserMap.objects.all().order_by("sdios_username")
    consumers = Consumer.objects.filter(usermap__in=users).distinct().order_by("name")

    pkg = {
        "users": users,
        "consumers": consumers,
    }
    return render(request, "users.html", pkg)
