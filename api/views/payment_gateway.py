import json
import stripe
from django.db import IntegrityError
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from django.conf import settings
from api.models import Order, Purchase, OrderStatus
from academy_backend import settings


def checkout(request):
    try:
        order = Order.objects.get(pk=int(request.POST.get("order_id")))
        purchase = Purchase(
            order=order,
            datetime=timezone.now()
        )
        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[
                    {
                        'price_data': {
                            'currency': 'inr',
                            'unit_amount': int(purchase.order.total_cost * 100),
                            'product_data': {
                                'name': purchase.order.product.name,
                            },
                        },
                        'quantity': 1,
                    }
                ],
                mode='payment',
                success_url=settings.STRIPE_DOMAIN + reverse('customer-products'),  # TODO: Success
                cancel_url=settings.STRIPE_DOMAIN + reverse('customer-products'),
                api_key=settings.STRIPE_API_KEY
            )
        except Exception as e:
            print(f"Couldn't checkout: {e}")
            return HttpResponse(str(e), status=403)

        purchase.stripe_id = checkout_session.stripe_id
        try:
            purchase.save()
        except IntegrityError:
            return JsonResponse(
                {"type": "ERROR", "message": "Sorry! You cannot order. Check if you have already ordered this item."},
                status=400)
        return HttpResponse(json.dumps({'id': checkout_session.id, 'order_status': OrderStatus.pending}))
    except Exception as e:
        print(f"Couldn't checkout: {e}")
        return HttpResponse("Not valid data", status=403)


@csrf_exempt
def checkout_webhook(request):
    print("----------Starting checkout webhook-------------")
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_ENDPOINT_SECRET
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)
    # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        purchase = Purchase.objects.get(stripe_id=session.id)
        purchase.confirmed = True
        purchase.save()
        order = purchase.order
        order.order_status = OrderStatus.payed
        order.save()
        print(session)
    # Passed signature verification
    return HttpResponse(status=200)
