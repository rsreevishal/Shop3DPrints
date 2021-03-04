from twilio.rest import Client


class WhatsAppMessage:
    def __init__(self):
        self.account_sid = "ACfff7e9d72b0c093d5c1c415314a454a0"
        self.auth_token = "075dafd34ddc37dd5b87358a0cd084dc"
        self.client = Client(self.account_sid, self.auth_token)
        self.from_whatsapp_number = 'whatsapp:+14155238886'

    def send_message(self, to_number, msg):
        self.client.messages.create(body=msg, from_=self.from_whatsapp_number, to=to_number)
