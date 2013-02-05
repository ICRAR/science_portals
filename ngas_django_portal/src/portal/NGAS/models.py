from django.db import models

class hosts(models.Model):
    host_id = models.CharField(max_length=32, db_index=True, unique=True)
    domain = models.CharField(max_length=30)
    ip_address = models.CharField(max_length=20)
    mac_address = models.CharField(max_length=20, null=True, blank=True)
    n_slots = models.SmallIntegerField(null=True, blank=True)
    cluster_name = models.CharField(max_length=16, null=True, blank=True)
    installation_date = models.CharField(max_length=23, null=True, blank=True)
    srv_version = models.CharField(max_length=20, null=True, blank=True)
    srv_port = models.IntegerField()
    srv_archive = models.SmallIntegerField(null=True, blank=True)
    srv_retrieve = models.SmallIntegerField(null=True, blank=True)
    srv_process = models.SmallIntegerField(null=True, blank=True)
    srv_remove = models.SmallIntegerField(null=True, blank=True)
    srv_state = models.CharField(max_length=20, null=True, blank=True)
    srv_data_checking = models.SmallIntegerField(null=True, blank=True)
    srv_check_start = models.CharField(max_length=23, null=True, blank=True)
    srv_check_remain = models.IntegerField(null=True, blank=True)
    srv_check_end = models.CharField(max_length=23, null=True, blank=True)
    srv_check_rate = models.FloatField(null=True, blank=True)
    srv_check_mb = models.FloatField(null=True, blank=True)
    srv_checked_mb = models.FloatField(null=True, blank=True)
    srv_check_files = models.DecimalField(max_digits=20, decimal_places=0, null=True, blank=True)
    srv_check_count = models.DecimalField(max_digits=20, decimal_places=0, null=True, blank=True)
    srv_suspended = models.SmallIntegerField(null=True, blank=True)
    srv_req_wake_up_srv = models.CharField(max_length=32, null=True, blank=True)
    srv_req_wake_up_time = models.CharField(max_length=23, null=True, blank=True)
    class Meta:
        unique_together = ("host_id", "srv_port")
        db_table = "ngas_hosts"
        verbose_name = "host"
    def __unicode__(self):
        return self.host_id + ' on Port:' + str(self.srv_port)
    
class disks(models.Model):
    disk_id = models.CharField(max_length=128, primary_key=True)
    archive = models.CharField(max_length=64)
    installation_date = models.CharField(max_length=23)
    disk_type = models.CharField(name='type', max_length=64)
    manufacturer = models.CharField(max_length=64, null=True, blank=True)
    logical_name = models.CharField(max_length=128)
    host_id = models.ForeignKey(hosts, to_field='host_id', null=True, blank=True)
    slot_id = models.CharField(max_length=32, null=True, blank=True)
    mounted = models.SmallIntegerField(null=True, blank=True)
    mount_point = models.CharField(max_length=128, null=True, blank=True)
    number_of_files = models.IntegerField()
    available_mb = models.IntegerField()
    bytes_stored = models.DecimalField(max_digits=20, decimal_places=0)
    completed = models.SmallIntegerField()
    completion_date = models.CharField(max_length=23, null=True, blank=True)
    checksum = models.CharField(max_length=64, null=True, blank=True)
    total_disk_write_time = models.FloatField(null=True, blank=True)
    last_check = models.CharField(max_length=23, null=True, blank=True)
    last_host_id = models.CharField(max_length=32, null=True, blank=True)
    class Meta:
        db_table = "ngas_disks"
        verbose_name = "disk"
    def __unicode__(self):
        return self.disk_id

class disks_hist(models.Model):
    disk_id = models.ForeignKey(disks, db_index=True)
    hist_date = models.CharField(max_length=23, db_index=True)
    hist_origin = models.CharField(max_length=64, db_index=True)
    hist_synopsis = models.CharField(max_length=255)
    hist_descr_mime_type = models.CharField(max_length=64, null=True, blank=True)
    hist_descr = models.TextField(null=True, blank=True)
    class Meta:
        db_table = "ngas_disks_hist"
    def __unicode__(self):
        return self.disk_id.disk_id + ' hist_date: ' + self.hist_date + ' hist_origin: ' + self.hist_origin

class files(models.Model):
    disk_id = models.ForeignKey('disks')
    file_name = models.CharField(max_length=255)
    file_id = models.CharField(max_length=64)
    file_version = models.IntegerField(default=1)
    file_format = models.CharField(name='format', max_length=32)
    file_size = models.DecimalField(max_digits=20, decimal_places=0)
    uncompressed_file_size = models.DecimalField(max_digits=20, decimal_places=0)
    compression = models.CharField(max_length=32, null=True, blank=True)
    ingestion_date = models.CharField(max_length=23)
    file_ignore = models.SmallIntegerField(null=True, blank=True)
    checksum = models.CharField(max_length=64, null=True, blank=True)
    checksum_plugin = models.CharField(max_length=64, null=True, blank=True)
    file_status = models.CharField(max_length=8, default='00000000')
    creation_date = models.CharField(max_length=23, null=True, blank=True)
    class Meta:
        unique_together = ("file_id", "file_version", "disk_id")
        db_table = "ngas_files"
        verbose_name = "file"
    def __unicode__(self):
        return 'FileID: ' + self.file_id + ', Version: ' + str(self.file_version) + ', DiskID: ' + self.disk_id.disk_id
      
