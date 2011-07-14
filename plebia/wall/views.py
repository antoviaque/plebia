from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.template import RequestContext

from wall.models import Post, PostForm

def new_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            # TODO Process the data in form.cleaned_data
            form.save()
            return HttpResponseRedirect('/')
    else:
        form = PostForm()

    latest_post_list = Post.objects.all().order_by('-pub_date')[:20]

    return render_to_response('wall/index.html', {
        'form': form,
        'latest_post_list': latest_post_list,
    }, context_instance=RequestContext(request))

