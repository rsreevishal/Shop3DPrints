from django.http import JsonResponse
from api.chatbot.chatbot import ChatBot


def chat_bot(request):
    if request.POST:
        try:
            chatbot = ChatBot()
            res = chatbot.chat_bot_response(request.POST.get("message"))
            return JsonResponse({"type": "SUCCESS", "message": request.POST.get("message"), "response": res},
                                status=200)
        except Exception as e:
            print(e)
            return JsonResponse({"type": "ERROR", "message": request.POST.get("message"), "response": ""}, status=200)
    return JsonResponse({"type": "ERROR", "message": "Can't process", "response": "Can't process"}, status=200)
