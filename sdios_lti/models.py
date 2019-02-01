import os
import random
import string
import time

from django.db import models


class Consumer(models.Model):
    """
    Each LMS which connects is considered a consumer and must have an
    entry in this table.  Two LMSes may not share the same consumer key
    unless they can be certain that no two users will share the same ID.
    """

    name = models.CharField(max_length=100, unique=True)
    key = models.CharField(max_length=255, unique=True)
    secret = models.CharField(max_length=64)

    @staticmethod
    def get_consumer(consumer_key):
        """
        Return a consumer which corresponds to the specified consumer
        key.

        If the specified consumer does not exist,
        :class:`Consumer.DoesNotExist` is raised.

        :param consumer_key: An LTI consumer key.
        :type consumer_key: string
        :returns: A :class:`Consumer` instance.
        :rtype: :class:`Consumer`
        """

        return Consumer.objects.get(key=consumer_key)

    @staticmethod
    def get_secret(consumer_key):
        """
        Return the secret corresponding to the specified consumer key.

        If the specified consumer does not exist,
        :class:`Consumer.DoesNotExist` is raised.

        :param consumer_key: An LTI consumer key.
        :type consumer_key: string
        :returns: The secret associated with the specified key.
        :rtype: string
        """

        return str(Consumer.get_consumer(consumer_key).secret)

    def __str__(self):
        return unicode(self).encode("utf-8")

    def __unicode__(self):
        return u"{} ({})".format(self.name, self.key)


class EnvironmentMap(models.Model):
    """
    To get access to an environment, the LMS must pass in an environment
    key which corresponds to a SDI OS environment.  Each
    environment which is available through LTI must have an entry in
    this table.  Entries map LTI IDs (which may be arbitrarily chosen)
    to SDI OS environments (which are referred to via UUIDs).
    It is acceptable, but not mandatory, that the LTI ID be the same as
    the SDI OS ID.

    Each environment also has a name which will be displayed to the
    user.  To avoid clashes across different environments, the name must
    be unique across all mappings.
    """

    name = models.CharField("LTI SDI Name", max_length=255, unique=True, help_text="Ensure the SDI name has not been used before.")
    sdios_environment_uuid = models.CharField(max_length=36, unique=True)
    lti_environment_key = models.CharField("LTI SDI Key", max_length=255, unique=True)

    def __str__(self):
        return unicode(self).encode("utf-8")

    def __unicode__(self):
        return u"{} ({} -> {})".format(self.name, self.lti_environment_key, self.sdios_environment_uuid)


class UserMap(models.Model):
    """
    When logging a user into the LTI instance, an LMS passes a unique
    (to that consumer) user ID.  A corresponding user must be created on
    the SDI OS instance so that the LMS user has an account.
    Entries in this table map consumer/user ID pairs to SDI OS
    users.
    """

    consumer = models.ForeignKey(Consumer)
    lti_user_id = models.CharField(max_length=255)
    sdios_username = models.CharField(max_length=255, unique=True)
    sdios_password = models.CharField(max_length=255)

    class Meta:
        unique_together = ("consumer", "lti_user_id")

    def __str__(self):
        return unicode(self).encode("utf-8")

    def __unicode__(self):
        return u"{} -> {} ({})".format(self.consumer, self.lti_user_id, self.sdios_username)

    @staticmethod
    def get_sdios_user(api, usermap):
        """
        Return a SDI OS user instance (as returned by the
        SDI OS API) corresponding to the specified user map
        entry.  If no such user exists, return `None`.

        :param api: An API object.
        :type api: :class:`APIRequest`
        :param usermap: The user mapping to look up.
        :type usermap: :class:`UserMap`
        :returns: The SDI OS API's representation of the
            specified user, or `None` if no such user exists.
        :rtype: dict or `None`
        """

        users = filter(lambda e: e["username"] == usermap.sdios_username, api.get("accounts/users"))
        if users:
            return users[0]

    @staticmethod
    def get(api, consumer, lti_user_id):
        """
        Get a :class:`UserMap` instance corresponding to the specified
        consumer/user ID pair.  If such a mapping does not exist, a new
        SDI OS user and associated mapping entry are created
        first.

        :param api: An API object.
        :type api: :class:`APIRequest`
        :param consumer: An LTI consumer.
        :type consumer: string
        :param lti_user_id: An LTI user ID as passed in by the LMS.
        :type lti_user_id: string
        :returns: A user mapping entry.
        :rtype: :class:`UserMap`
        """

        consumer = Consumer.get_consumer(consumer)

        default_tenancy = api.get("system/settings/")["default_tenancy"]

        try:
            usermap = UserMap.objects.get(consumer=consumer, lti_user_id=lti_user_id)
            if UserMap.get_sdios_user(api, usermap) is None:
                usermap.delete()
                raise UserMap.DoesNotExist
        except UserMap.DoesNotExist:
            def __get_rand_chars(strg, leng):
                return "".join(random.choice(strg) for x in range(leng))

            sdios_username = "SDIOS-LTI-{}".format(os.urandom(8).encode("hex"))
            rand_chars = __get_rand_chars(string.letters, 10) + __get_rand_chars(string.digits, 3) + __get_rand_chars(string.punctuation, 3)
            sdios_password = "".join(random.sample(rand_chars, len(rand_chars)))

            user_params = UserMap.__user_params(sdios_username, sdios_password, default_tenancy)
            api.post("accounts/users", user_params)
            usermap = UserMap(consumer=consumer, lti_user_id=lti_user_id, sdios_username=sdios_username, sdios_password=sdios_password)
            usermap.save()

        # Ensure the user has the proper settings.  This is not
        # necessary unless user parameters (see __user_params) change
        # *after* users have already been created.
        user = UserMap.get_sdios_user(api, usermap)
        user_params = UserMap.__user_params(usermap.sdios_username, usermap.sdios_password, default_tenancy)
        api.put("accounts/users/{}".format(user["pk"]), user_params)

        return usermap

    @staticmethod
    def __user_params(username, password, tenancy):
        return {
            "username": username,
            "password": password,
            "tenancy": tenancy,
            "display_name": username,
            "email": "",
            "id_tenancy_admin": False,
            "is_active": True,
            "is_superuser": False,
            "permissions": {
                "access_dashboard": False,
                "access_sdis": True,
                "access_physical": False,
                "access_profile": False,
                "access_storage": False,
                "allow_nas": True,
                "edit_sdis": False,
                "share_sdis": False,
                "share_images": False,
                "start_sdis": True,
                "view_navbar": False,
                "share_networks": False,
            },
        }

    @staticmethod
    def login(api, usermap, source_environment):
        """
        Set up a user's environment and return a URL which will pass the
        user to the environment.  A copy is made of the source
        environment in the target user's SDI OS account.

        :param api: An API object.
        :type api: :class:`APIRequest`
        :param usermap: A mapping for the desired user.
        :type usermap: :class:`UserMap`
        :param source_environment: The environment to copy.
        :type source_environment: :class:`EnvironmentMap`
        :returns: A URL which will take the user to the environment.
        :rtype: string
        """

        user = UserMap.get_sdios_user(api, usermap)

        environments = api.get("sdis")

        if user is None:
            raise Exception

        try:
            source_user = filter(lambda e: e["sdi_id"] == source_environment.sdios_environment_uuid, environments)[0]["user"]
        except IndexError:
            source_environment.delete()
            raise

        # If the desired target environment already exists, try deleting
        # it.  This will fail if the environment does not exist (i.e.
        # this is the user's first visit) or if the environment is
        # running.  If the environment is running, we want to reuse that
        # anyway, so failure to delete is OK.
        user_environment = filter(lambda e: e["name"] == source_environment.name and e["user"] == user["pk"], environments)
        if user_environment:
            try:
                api.delete("sdis/{}".format(user_environment[0]["sdi_id"]))
            except Exception:
                pass

        env_data = {
            "name": source_environment.name,
            "user": int(user["pk"]),
            "remove_persistence": True,
        }

        # Try copying the source environment to the target environment.
        # This can fail is the source environment is running of if the
        # target environment exists.
        try:
            api.post("sdis/{}/copy".format(source_environment.sdios_environment_uuid), env_data)
            # Copying is done asynchronously, so there is a slight race
            # after a copy: it could still be in a pending state after
            # returning.  Because no images are being copied, assume the
            # copy runs quickly enough that a 2 second delay will avoid
            # the race.
            time.sleep(2)
        except Exception:
            pass

        environments = api.get("sdis")

        # This will fail if the environment does not exist, which is
        # possible if the source environment was running and this is the
        # user's first login attempt.
        environment = filter(lambda e: e["user"] == int(user["pk"]) and e["name"] == source_environment.name, environments)[0]

        # Stop all environments belonging to this user, except for the
        # just-copied environment.
        for env in filter(lambda e: e["user"] == user["pk"] and e["name"] != source_environment.name, environments):
            api.post("sdis/{}/stop".format(env["sdi_id"]))

        url = api.post("accounts/login/token", {"user": user["pk"]})["url"]
        url = "{}?next={}".format(url, environment["url"].split(Setting.get().sdios_url)[1])

        return url


class Setting(models.Model):
    """
    This table keeps holds all information necessary to use SDI OS's
    API.  Only one entry exists in this table, serving as a
    global API configuration.
    """

    sdios_url = models.CharField(" URL", max_length=255, help_text="This is where your SDI OS instance lives.", default="127.0.0.1:8000")
    sdios_username = models.CharField("SDI OS API username", max_length=255, help_text="The username of your SDI OS API user.", default="")
    sdios_password = models.CharField("SDI OS API password", max_length=255, help_text="The password of your SDI OS API user.", default="")
    client_id = models.CharField("Client ID", max_length=255, help_text="Client ID found under API application at {SDI OS URL}/api/o/applications.", default="")
    client_secret = models.CharField("Client Secret", max_length=255, help_text="Client Secret found under API application at {SDI OS URL}/api/o/applications.", default="")

    @staticmethod
    def get():
        """
        Get a :class:`Setting` record which applies to default API
        settings.  If one does not exist, create an initial blank
        Setting with localhost as SDI OS URL.

        :returns: Default settings entry
        :rtype: :class:`Setting`
        """
        try:
            #Default initial settings
            settings = Setting.objects.all()[0]
        except IndexError:
            # Create default settings if all settings are deleted
            settings = Setting()
            settings.save()

        return settings

    def __str__(self):
        return unicode(self).encode("utf-8")

    def __unicode__(self):
        return u"SDI OS @ {} (ID: {}, Secret: {})".format(self.sdios_url, self.client_id, self.client_secret)
