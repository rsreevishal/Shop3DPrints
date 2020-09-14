from django.http import HttpResponse
from django.template import loader

from api.models import AcademyUser


def standard_view(template_name):
    def view(request):
        template = loader.get_template(template_name)
        context = {
            'me': AcademyUser.get_for(request.user),
        }
        return HttpResponse(template.render(context, request))

    return view
