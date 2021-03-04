from twilio.rest import Client
account_sid = "ACfff7e9d72b0c093d5c1c415314a454a0"
# Your Auth Token from twilio.com/console
auth_token  = "075dafd34ddc37dd5b87358a0cd084dc"

client = Client(account_sid, auth_token)


# this is the Twilio sandbox testing number
from_whatsapp_number='whatsapp:+14155238886'
# replace this number with your own WhatsApp Messaging number
to_whatsapp_number='whatsapp:+917358499668'

client.messages.create(body='Hello World!',
                       from_=from_whatsapp_number,
                       to=to_whatsapp_number)