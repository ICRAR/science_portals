from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.http import HttpResponse
from NGAS.models import hosts, disks, files, disks_hist
from django.template import RequestContext
import datetime
from django.db.models import Sum
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


def index(request):
    return render_to_response('NGAS/index.html')

def hostdirect(request):
    return render_to_response('NGAS/hostdirect.html')

def filedirect(request):
    return render_to_response('NGAS/filedirect.html')

def diskdirect(request):
    return render_to_response('NGAS/diskdirect.html')

###### HOST RELATED VIEWS #####

def hosturl(request, option):
    url = '/NGAS/hosts/query/display/?option=' + option
    if option == 'all':
        pass
    if option == 'opt1':
        host_id = request.POST['host_id']
        port_str = request.POST['port_num']
        url += '&host_id=' + host_id + '&port_str=' + port_str
    if option == 'opt2':
        pass
    if option == 'opt3':
        host_id = request.POST['host_id']
        url += '&host_id=' + host_id
    if option == 'opt4':
        ip_add = request.POST['ip_add']
        url += '&ip_add=' + ip_add
    if option == 'opt5':
        port_num = request.POST['port_num']
        url += '&port_num=' + port_num
    if option == 'opt6':
        cluster = request.POST['cluster']
        url += '&cluster=' + cluster
    url += '&page=1'
    return redirect(url)
    

def hostview(request):
    
    r2disp=2

    option = request.GET.get('option')
    urlstring = '?option=' + option
    if option == 'all':
        h = hosts.objects.all()
    
    if option == 'opt1':
        host_id = request.GET.get('host_id')
        port_str = request.GET.get('port_str')
        try:
            port_num = int(port_str)
        except ValueError:
            port_num = 0
        h = hosts.objects.filter(host_id__istartswith=host_id)
        h = h.filter(srv_port=port_num)
        urlstring += '&host_id=' + host_id + '&port_str=' + port_str
    if option == 'opt2':
        h = hosts.objects.extra(where=["NOT srv_suspended ISNULL"])
    if option == 'opt3':
        host_id = request.GET.get('host_id')
        h = hosts.objects.filter(host_id__istartswith=host_id)
        urlstring += '&host_id=' + host_id
    if option == 'opt4':
        ip_add = request.GET.get('ip_add')
        h = hosts.objects.filter(ip_address__istartswith=ip_add)
        urlstring += '&ip_add=' + ip_add
    if option == 'opt5':
        port_num = request.GET.get('port_num')
        try:
           port_num = int(port_num)
        except ValueError:
           port_num = 0
        h = hosts.objects.filter(srv_port=port_num)
        urlstring += '&port_num=' + str(port_num)
    if option == 'opt6':
        cluster = request.GET.get('cluster')
        h = hosts.objects.filter(cluster_name__istartswith=cluster)
        urlstring += '&cluster=' + cluster
        
    h=h.order_by('host_id')

    paginator = Paginator(h, r2disp)
    page = request.GET.get('page')
    try:
        host_list = paginator.page(page)
    except PageNotAnInteger:
        host_list = paginator.page(1)
    except EmptyPage:
        host_list = paginator.page(paginator.num_pages)

    return render_to_response('NGAS/hostview.html',
                              {'results': host_list, 'urlstring':urlstring})

def hostquery(request):
    return render_to_response('NGAS/hostquery.html', context_instance=RequestContext(request))

def hostdetails(request, host_id):
    try:
        int(host_id)
        p = get_object_or_404(hosts, pk=host_id)
    except ValueError:
        p = get_object_or_404(hosts, host_id=host_id)
    return render_to_response('NGAS/hostdetails.html', {'host': p})


##### DISK RELATED VIEWS #####


def diskurl(request, option):
    url = '/NGAS/disks/query/display/?option=' + option
    if option == 'all':
        url += '&page=1'
    if option == 'opt1':
        url += '&page=1'
    return redirect(url)

def diskview(request):
    
    r2disp=2
    option = request.GET.get('option')
    urlstring = '?option=' + option
    if option == 'all':
        d = disks.objects.all()
    else:
        if option == 'opt1':
            d = disks.objects.exclude(completed = 0)
        if option == 'opt2':
            pass

    d=d.order_by('logical_name')
    
    paginator = Paginator(d, r2disp)
    page = request.GET.get('page')
    try:
        disk_list = paginator.page(page)
    except PageNotAnInteger:
        disk_list = paginator.page(1)
    except EmptyPage:
        disk_list = paginator.page(paginator.num_pages)
    
    return render_to_response('NGAS/diskview.html',
                              {'results': disk_list, 'urlstring':urlstring})

def diskquery(request):
    return render_to_response('NGAS/diskquery.html', context_instance=RequestContext(request))

def diskdetails(request, disk_id):
    p = get_object_or_404(disks, pk=disk_id)
    return render_to_response('NGAS/diskdetails.html', {'disk': p},
                              context_instance=RequestContext(request))

def diskhistory(request, disk_id):
    h = disks_hist.objects.filter(disk_id = disk_id).order_by('disk_id', '-hist_date')
    return render_to_response('NGAS/diskhistory.html', {'hist':h})

def diskhistquery(request):
    return render_to_response('NGAS/diskhistquery.html',
                              context_instance=RequestContext(request))

def diskstatusquery(request):
    return render_to_response('NGAS/diskstatusquery.html',
                              context_instance=RequestContext(request))

def diskhistview(request):
    disk_id = request.POST['disk_id']
    if disk_id == '%':
        h = disks_hist.objects.all().order_by('disk_id', '-hist_date')
    else:
        h = disks_hist.objects.filter(disk_id = disk_id).order_by('disk_id', '-hist_date')
    return render_to_response('NGAS/diskhistory.html', {'hist':h})

def diskstatsurl(request, junk):
    disk_id = request.POST['disk_id']
    host_id = request.POST['host_id']
    logical_name = request.POST['logical_name']
    refine1 = 'None'
    refine2 = 'None'
    url = ('/NGAS/disks/query/status/search/?disk_id=' + disk_id + '&host_id=' + host_id +
                                        '&logical_name=' + logical_name +
                                           '&refine1=' + refine1)
    return redirect(url)

def diskstatsview(request):
    disk_id = request.GET.get('disk_id')
    host_id = request.GET.get('host_id')
    logical_name = request.GET.get('logical_name')
    refine1 = request.GET.get('refine1')
    d = disks.objects.all()
    if disk_id != '%':
        d = d.filter(dsik_id = disk_id)
    if host_id != '%':
        d = d.filter(host_id = host_id)
    if logical_name == '%_M_%' or logical_name == '%_R_%':
        logical_name = logical_name.replace('%_', '-')
        logical_name = logical_name.replace('_%', '-')
    if logical_name != '%':
        d = d.filter(logical_name__contains=logical_name)
    if refine1 == '1':
        d = d.filter(mounted = 1)
    elif refine1 == '0':
        d = d.filter(mount_point = '--%')
    elif refine1 == 'unknown':
        d = d.filter(mount_point = None or '')
    urlstring1 = ('/NGAS/disks/query/status/search/?disk_id=' + disk_id + '&host_id=' + host_id
                                        + '&logical_name=' + logical_name)

    urlstring2 = ('/NGAS/disks/query/status/search/?disk_id=' + disk_id + '&host_id=' + host_id
                                        + '&refine1=' + refine1)
    
    return render_to_response('NGAS/diskstatistics.html',
                              {'disks':d, 'urlstring1':urlstring1, 'urlstring2':urlstring2},
                              context_instance=RequestContext(request))

def diskstatsupdate(request):
    disk_id = request.GET.get('disk_id')
    d = get_object_or_404(disks, pk=disk_id)
    return render_to_response('NGAS/diskstatsupdate.html', {'disk':d},
                              context_instance=RequestContext(request))

def diskstatssubmit(request):
    mount_point = request.POST['mount_point']
    disk_id = request.POST['disk_id']
    d = disks.objects.get(disk_id = disk_id)
    d.mount_point = mount_point
    d.save()
    return redirect(("/NGAS/disks/details/" + disk_id + "/"))
    

def diskhistdesc(request, disk_id, hist_id):
    h = disks_hist.objects.get(pk = hist_id)
    return render_to_response('NGAS/diskhistdesc.html', {'entry':h})


##### FILE RELATED VIEWS #####


def fileurl(request, option):
    url = '/NGAS/files/query/display/?option=' + option
    if option == 'all':
        pass
    if option == 'opt1':
        pass
    if option == 'opt2':
        start_date = request.POST['start_date']
        end_date = request.POST['end_date']
        file_id = request.POST['file_id']
        url += '&start_date=' + start_date + '&end_date=' + end_date + '&file_id=' + file_id
    if option == 'opt3':
        file_id = request.POST['file_id']
        disk_id = request.POST['disk_id']
        ingestion_date = request.POST['ingestion_date']
        file_status = request.POST['file_status']
        url += ('&file_id=' + file_id + '&disk_id=' + disk_id +
                    '&ingestion_date=' + ingestion_date + '&file_status=' + file_status)

    if option == 'opt6':
        start_date = request.POST['start_date']
        end_date = request.POST['end_date']
        url = ('/NGAS/files/query/insstat/display/?start_date=' + start_date +
                                                   '&end_date=' + end_date)
    if option == 'diskfiles':
        disk_id = request.GET.get('disk_id')
        file_id = request.GET.get('file_id')
        url += '&disk_id=' + disk_id
        if file_id != None and file_id != '%':
            url += '&file_id=' + file_id
    
    url += '&page=1'
    return redirect(url)
        

def fileview(request):
    
    r2disp=2
    option = request.GET.get('option')
    urlstring = '?option=' + option
    
    if option == 'all':
        f = files.objects.all()
    
    if option == 'opt1':
        f = files.objects.extra(where=["NOT ingestion_date ISNULL"])
        f = f.order_by('-ingestion_date')[0]
        f = files.objects.filter(pk=f.id)
           
    if option == 'opt2':
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        file_id = request.GET.get('file_id')
        f = files.objects.filter(ingestion_date__gte=start_date)
        f = f.filter(ingestion_date__lte=end_date)
        if file_id != '%':
            f = f.filter(file_id=file_id)
        urlstring += ('&start_date=' + start_date + '&end_date=' + end_date +
                          '&file_id=' + file_id)

    if option == 'opt3':
        file_id = request.GET.get('file_id')
        disk_id = request.GET.get('disk_id')
        ingestion_date = request.GET.get('ingestion_date')
        file_status = request.GET.get('file_status')
        f = files.objects.all()
        if file_id != '%':
            f = f.filter(file_id=file_id)
        if disk_id != '%':
            f = f.filter(disk_id=disk_id)
        if ingestion_date != '%':
            f = f.filter(ingestion_date=ingestion_date)
        if file_status != '%':
            f = f.filter(file_status=file_status)
        urlstring += ('&file_id=' + file_id + '&disk_id=' + disk_id +
                        '&ingestion_date=' + ingestion_date + '&file_status=' + file_status)

    if option == 'diskfiles':
        disk_id = request.GET.get('disk_id')
        file_id = request.GET.get('file_id')
        f = files.objects.filter(disk_id = disk_id)
        urlstring += '&disk_id=' + disk_id
        if file_id != None and file_id != '%':
            f = f.filter(file_id = file_id)
            urlstring += '&file_id=' + file_id

    f = f.order_by('file_id')
        
    paginator = Paginator(f, r2disp)
    page = request.GET.get('page')
    try:
        file_list = paginator.page(page)
    except PageNotAnInteger:
        file_list = paginator.page(1)
    except EmptyPage:
        file_list = paginator.page(paginator.num_pages)
    
    return render_to_response('NGAS/fileview.html',
                              {'results': file_list, 'urlstring':urlstring})

def filedaterange(request, opt):
    now = datetime.datetime.now()
    cur_date = now.strftime("%Y-%m-%d")
    prev_date = now - datetime.timedelta(1)
    prev_date = prev_date.strftime("%Y-%m-%d")
    if opt == 2:
        template = 'NGAS/filedrquery.html'
    if opt == 6:
        template = 'NGAS/fileinsertstats.html'
    return render_to_response(template,
                              {'cur_date': cur_date, 'prev_date': prev_date},
                              context_instance=RequestContext(request))

    
def filesearchform(request):
    return render_to_response('NGAS/filesearchform.html',
                              context_instance=RequestContext(request))

def filequery(request):
    return render_to_response('NGAS/filequery.html',
                              context_instance=RequestContext(request))

def filetotalstats(request):
    f = files.objects.all()
    count = f.count()
    total=None
    x=f.aggregate(total=Sum('file_size'))
    x = x.pop('total')
    total = ((float(x)/1048576)/1048576)
    return render_to_response('NGAS/filetotalstats.html',
                              {'numFiles':count, 'totalSize':total})

def filerangedisp(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    f = files.objects.filter(ingestion_date__gte=start_date)
    f = f.filter(ingestion_date__lte=end_date)
    urlstring = '?start_date=' + start_date + '&end_date=' + end_date
    total = None
    if f.count() != 0:
        x=f.aggregate(total=Sum('file_size'))
        x = x.pop('total')
        total = ((float(x)/1048576)/1024)
    numFiles = f.count()

    paginator = Paginator(f, 2)
    page = request.GET.get('page')
    try:
        file_list = paginator.page(page)
    except PageNotAnInteger:
        file_list = paginator.page(1)
    except EmptyPage:
        file_list = paginator.page(paginator.num_pages)
    
    return render_to_response('NGAS/filerangestats.html',
                             {'total':total, 'start_date':start_date, 'end_date':end_date,
                              'numFiles':numFiles, 'results':file_list, 'urlstring':urlstring})

def filestatcheck(request):
    return render_to_response('NGAS/filestatcheck.html',
                              context_instance=RequestContext(request))


def filestatres(request):
    status = request.POST['status']
    disk_id = request.POST['disk_id']
    f = files.objects.all()
    if status != '%':
        f = f.filter(file_status=status)
    else:
        status = "all"
    if disk_id != '%':
        f = f.filter(disk_id=disk_id)
    f = f.order_by('disk_id')
    a=[]
    first = True
    count = 0
    DID = ''
    for x in f:
        if x.disk_id != DID:
            if not first:
                a.append((DID, count))
            first = False
            count = 0
            DID = x.disk_id
        count += 1
    if DID != '': a.append((DID, count))
    class disk_count:
        disk_id = None
        count = None
        
    b=[]
    if a != []:
        for x in a:
            disk = disk_count()
            disk.disk_id = x[0]
            disk.count = x[1]
            b.append(disk)    

    if b == []:
        b = None
    
    return render_to_response('NGAS/filestatres.html',
                              {'results': b, 'status':status})

def filediskcheck(request):
    return render_to_response('NGAS/filediskcheck.html',
                                 context_instance=RequestContext(request))
        
def filediskres(request):
    file_id = request.POST['file_id']
    f = files.objects.all()
    if file_id != '%':
        f = f.filter(file_id=file_id)
    f = f.order_by('disk_id')
    a=[]
    first = True
    count = 0
    DID = ''
    for x in f:
        if x.disk_id != DID:
            if not first:
                a.append((DID, count))
            first = False
            count = 0
            DID = x.disk_id
        count += 1
    if DID != '': a.append((DID, count))
    class disk_count:
        disk_id = None
        count = None
        
    b=[]
    if a != []:
        for x in a:
            disk = disk_count()
            disk.disk_id = x[0]
            disk.count = x[1]
            b.append(disk)    

    if b == []:
        b = None
    
    return render_to_response('NGAS/filediskres.html',
                              {'results': b, 'file_id':file_id})

def filestatdisk(request, disk_id, status):
    f = files.objects.filter(disk_id = disk_id)
    l_name = f[0].disk_id.logical_name
    status = status.replace("status_", "")
    if status != 'all':
        f = f.filter(file_status=status)
    else:
        status = '%'
    f = f.order_by('file_id')

    paginator = Paginator(f, 2)
    page = request.GET.get('page')
    try:
        file_list = paginator.page(page)
    except PageNotAnInteger:
        file_list = paginator.page(1)
    except EmptyPage:
        file_list = paginator.page(paginator.num_pages)
    
    return render_to_response('NGAS/filestatdisk.html',
                              {'files': file_list, 'name': l_name, 'status': status})



def filedetails(request, file_id):
    p = get_object_or_404(files, pk=file_id)
    return render_to_response('NGAS/filedetails.html', {'file': p})


