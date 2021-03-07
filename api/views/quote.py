import uuid
from django.http import JsonResponse

from django.conf import settings
from api.models import Order, OrderStatus
from academy_backend import settings
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from weasyprint import HTML

from api.views.whatsapp import WhatsAppMessage


def html_to_pdf_view(order, file_name):
    try:
        html_string = render_to_string('service_provider/invoice_template.html',
                                       {"order": order, "file_name": file_name})
        html = HTML(string=html_string)
        html.write_pdf(target=f'media/invoice/{file_name}')
        return True
    except Exception as e:
        print(f"Error occured in pdf: {e}")
        return False


def generate_quote(request, order_id: int = None):
    try:
        if request.POST:
            order = Order.objects.get(pk=order_id)
            if request.POST.get('additional_value'):
                order.additional_value = request.POST.get('additional_value')
            if request.POST.get('additional_cost'):
                order.additional_cost = float(request.POST.get('additional_cost'))
            if request.POST.get('total_cost'):
                order.total_cost = float(request.POST.get('total_cost'))
            if request.POST.get('comments'):
                order.comments = request.POST.get('comments')
            file_name = f'{str(uuid.uuid4())}.pdf'
            if html_to_pdf_view(order, file_name):
                order.invoice_generated = True
                order.invoice_file_name = file_name
                order.order_status = OrderStatus.quoted
            order.save()
            email = EmailMessage(
                'Your order was received', f'Hello {order.product.customer}. We processed your invoice',
                settings.DEFAULT_FROM_EMAIL, [order.product.customer.django_user.email])
            email.attach_file(f'media/invoice/{file_name}')
            email.send()
            status_names = ["Completed", "Cancelled", "Quoted", "Pending", "Shipped", "Payed"]
            try:
                wapp = WhatsAppMessage()
                wapp.send_message(f'whatsapp:+{order.product.customer.country}{order.product.customer.phone_number}',
                                  f'Your order *{order.product.name}* status is updated to: *{status_names[order.order_status]}* by {order.service_provider}. Check your mail')
            except Exception as e:
                print(e)
            return JsonResponse({"type": "SUCCESS",
                                 "message": "Successfully generated quote and sent to customer email."}, status=200)
    except Exception as e:
        print(e)
        return JsonResponse({"type": "ERROR", "message": "Failed to generate quote."}, status=200)
