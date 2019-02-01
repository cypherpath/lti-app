from django.conf.urls import patterns, include, url
from django.contrib import admin

import sdios_lti.views

urlpatterns = patterns(
    "",
    url(r"^$", sdios_lti.views.index, name="index"),

    url(r"^login/$", sdios_lti.views.login, name="login"),
    url(r"^logout/$", sdios_lti.views.logout, name="logout"),

    url(r"^sdis/$", sdios_lti.views.view_environments, name="sdis"),
    url(r"^sdis/export/$", sdios_lti.views.export_environment, name="export_environment"),
    url(r"^sdis/remove/(?P<sdi_id>[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12})/$", sdios_lti.views.remove_lti_access, name="remove_lti_access"),

    url(r"^consumers/$", sdios_lti.views.view_consumers, name="consumers"),
    url(r"^consumers/add_consumer/$", sdios_lti.views.add_consumer, name="add_consumer"),
    url(r"^consumers/delete_consumer/$", sdios_lti.views.delete_consumer, name="delete_consumer"),

    url(r"^users/$", sdios_lti.views.view_users, name="users"),

    url(r"^settings/$", sdios_lti.views.manage_settings, name="settings"),

    url(r"^lti/$", sdios_lti.views.lti, name="lti"),

    url(r"^admin/", include(admin.site.urls)),
)
