from django.http import HttpResponse
from django.template import loader

from api.models import AcademyUser, Course


def standard_view(template_name, ctx=None):
    if ctx is None:
        ctx = {}

    def view(request):
        template = loader.get_template(template_name)
        context = {
            'me': AcademyUser.get_for(request.user),
            'all_categories': Course.Category.choices,
            **ctx,
        }
        return HttpResponse(template.render(context, request))

    return view


def index(request):
    trending = Course.objects.order_by('-enrollment')[:2]
    fresh = Course.objects.order_by('-id')[:3]

    return standard_view('landing/index.html', {
        'trending': trending,
        'fresh': fresh,
    })(request)
