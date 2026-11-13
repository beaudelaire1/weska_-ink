import json
import stripe
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .services import process_stripe_event


@csrf_exempt
@require_POST
def stripe_webhook(request):
    if not settings.STRIPE_WEBHOOK_SECRET:
        return HttpResponse("Stripe webhook non configuré.", status=503)
    signature = request.headers.get("Stripe-Signature", "")
    try:
        event = stripe.Webhook.construct_event(request.body, signature, settings.STRIPE_WEBHOOK_SECRET)
        event = event.to_dict_recursive()
        process_stripe_event(event)
    except (ValueError, stripe.SignatureVerificationError):
        return HttpResponseBadRequest("Signature invalide.")
    except Exception:
        # Stripe retries 5xx responses; errors remain visible to application logs.
        import logging
        logging.getLogger(__name__).exception("Erreur lors du traitement d'un webhook Stripe")
        return HttpResponse("Erreur de traitement.", status=500)
    return HttpResponse(status=200)
