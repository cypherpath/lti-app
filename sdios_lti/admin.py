from django.contrib import admin

from sdios_lti.models import Consumer, EnvironmentMap, UserMap, Setting


admin.site.register(Consumer)
admin.site.register(EnvironmentMap)
admin.site.register(UserMap)
admin.site.register(Setting)
