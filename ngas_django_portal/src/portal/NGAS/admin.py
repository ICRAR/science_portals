from NGAS.models import hosts, files, disks, disks_hist
from django.contrib import admin

class hostsAdmin(admin.ModelAdmin):
    list_display = ('host_id', 'srv_port', 'domain', 'ip_address')

class disksAdmin(admin.ModelAdmin):
    list_display = ('logical_name', 'disk_id', 'archive', 'installation_date')

class filesAdmin(admin.ModelAdmin):
    list_display = ('file_id', 'disk_id', 'file_version')

class diskHistAdmin(admin.ModelAdmin):
    list_display = ('disk_id', 'hist_date', 'hist_origin')

admin.site.register(hosts, hostsAdmin)
admin.site.register(files, filesAdmin)
admin.site.register(disks, disksAdmin)
admin.site.register(disks_hist, diskHistAdmin)
