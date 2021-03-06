import nltk
import pickle
import numpy as np
import json
import random
from keras.models import load_model
from nltk.stem import WordNetLemmatizer


class ChatBot:
    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()
        self.model = load_model('/home/sree/SREEVISHAL/Project/Shop3DPrints/api/chatbot/chatbot_model.h5')
        self.intents = json.loads(open('/home/sree/SREEVISHAL/Project/Shop3DPrints/api/chatbot/intents.json').read())
        self.words = pickle.load(open('/home/sree/SREEVISHAL/Project/Shop3DPrints/api/chatbot/words.pkl', 'rb'))
        self.classes = pickle.load(open('/home/sree/SREEVISHAL/Project/Shop3DPrints/api/chatbot/classes.pkl', 'rb'))

    def __clean_up_sentence(self, sentence):
        sentence_words = nltk.word_tokenize(sentence)
        sentence_words = [self.lemmatizer.lemmatize(word.lower()) for word in sentence_words]
        return sentence_words

    def __bow(self, sentence, wrds, show_details=True):
        sentence_words = self.__clean_up_sentence(sentence)
        bag = [0] * len(wrds)
        for s in sentence_words:
            for i, w in enumerate(wrds):
                if w == s:
                    bag[i] = 1
                    if show_details:
                        print("found in bag: %s" % w)
        return np.array(bag)

    def __predict_class(self, sentence):
        p = self.__bow(sentence, self.words, show_details=False)
        res = self.model.predict(np.array([p]))[0]
        error_threshold = 0.25
        results = [[i, r] for i, r in enumerate(res) if r > error_threshold]
        results.sort(key=lambda x: x[1], reverse=True)
        return_list = []
        for r in results:
            return_list.append({"intent": self.classes[r[0]], "probability": str(r[1])})
        return return_list

    def __get_response(self, ints):
        tag = ints[0]['intent']
        list_of_intents = self.intents['intents']
        result = None
        for i in list_of_intents:
            if i['tag'] == tag:
                result = random.choice(i['responses'])
                break
        return result

    def chat_bot_response(self, msg):
        ints = self.__predict_class(msg)
        res = self.__get_response(ints)
        return res