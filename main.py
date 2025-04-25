from kivy.config import Config

# Set default size for mobile emulation
Config.set("graphics", "width", "360")
Config.set("graphics", "height", "640")
Config.set("graphics", "resizable", "0")

import requests
import speech_recognition as sr
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.graphics import Color, RoundedRectangle
from kivy.uix.relativelayout import RelativeLayout
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.uix.image import Image
from kivy.graphics import Rectangle
from kivy.uix.relativelayout import RelativeLayout
import uuid
import requests

session_id = str(uuid.uuid4())

AI_NAME = "KaltalkAI"  # Define the AI assistant's name


class ChatBubble(Label):
    def __init__(self, text, align="right", **kwargs):
        super().__init__(text=text, size_hint_y=None, padding=(10, 6), **kwargs)
        self.bind(size=self.update_size)

        self.font_size = '14sp'
        self.halign = "right" if align == "right" else "left"
        self.valign = "middle"
        self.size_hint_x = 0.45 if align == "right" else 0.55

        user_bg_color = (0.0, 0.6, 1, 1)  # Blue for user messages
        bot_bg_color = (0.25, 0.5, 0.25, 1)  # Green for bot messages

        with self.canvas.before:
            Color(*(user_bg_color if align == "right" else bot_bg_color))
            self.rect = RoundedRectangle(radius=[12, 12, 12, 12])

        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.rect.size = self.size
        if self.halign == "right":
            self.rect.pos = (self.parent.width - self.width - 10, self.y)
        else:
            self.rect.pos = (10, self.y)

    def update_size(self, *args):
        self.text_size = (self.width - 20, None)
        self.texture_update()
        self.height = self.texture_size[1] + 20


class ChatApp(App):
    
    def build(self):
        self.session_id = str(uuid.uuid4())
        root = RelativeLayout()

        # Draw background image BEFORE anything else
        with root.canvas.before:
            self.bg = Rectangle(source='background.jpg', size=root.size, pos=root.pos)

        # Make it stretch with window
        root.bind(size=self.update_bg, pos=self.update_bg)

        # Main chat layout (on top of the image)
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=5)
        self.layout.size_hint = (1, 1)  # ⬅️ This is the fix to make layout fill the whole screen

        self.chat_history = GridLayout(cols=1, size_hint_y=None, spacing=3)
        self.chat_history.bind(minimum_height=self.chat_history.setter('height'))

        self.scroll_view = ScrollView(size_hint=(1, 0.85))
        self.scroll_view.add_widget(self.chat_history)

        input_layout = BoxLayout(size_hint_y=None, height=60, spacing=5, padding=(5, 5))
        self.user_input = TextInput(hint_text="Type your message...", multiline=True, size_hint_x=0.65, height=50)
        self.user_input.bind(text=self.adjust_input_height)

        send_button = Button(text="Send", size_hint_x=0.2, height=50)
        send_button.bind(on_release=self.send_message)

        mic_button = Button(text="🎤", size_hint_x=0.15, height=50)
        mic_button.bind(on_release=self.voice_input)

        input_layout.add_widget(self.user_input)
        input_layout.add_widget(send_button)
        input_layout.add_widget(mic_button)

        self.layout.add_widget(self.scroll_view)
        self.layout.add_widget(input_layout)

        root.add_widget(self.layout)  # Make sure layout is added AFTER background

        self.start_conversation()  # AI starts the convo

        return root



    def start_conversation(self):
        """ AI sends the first message when the app starts """
        self.add_message(f"Hey there! I'm {AI_NAME}, your personal AI buddy. What can I do for you today?", align="left")

    def adjust_input_height(self, instance, value):
        """ Adjusts the input box height dynamically as the user types """
        max_height = 90  
        min_height = 50  
        num_lines = value.count("\n") + 1  
        line_height = self.user_input.line_height
        self.user_input.height = min(max(num_lines * line_height + 20, min_height), max_height)

    def send_message(self, instance=None):
        user_message = self.user_input.text.strip()
        if not user_message:
            return  

        self.add_message(user_message, align="right")

        try:
            response = requests.post("https://kaltalkai.onrender.com/chat", json={"message": user_message,
                                                                         "session_id": self.session_id})
            bot_reply = response.json().get("response", "Error: No response")
        except Exception:
            bot_reply = "Error: Could not connect to server."

        self.add_message(bot_reply, align="left")
        self.user_input.text = ""

    def voice_input(self, instance=None):
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            self.add_message("Listening...", align="left")
            try:
                audio = recognizer.listen(source, timeout=5)
                user_message = recognizer.recognize_google(audio)
                self.user_input.text = user_message  
                self.send_message()
            except sr.UnknownValueError:
                self.add_message("Could not understand audio", align="left")
            except sr.RequestError:
                self.add_message("Speech service unavailable", align="left")

    def add_message(self, text, align="left"):
        bubble = ChatBubble(text=text, align=align)

        message_container = BoxLayout(size_hint_y=None, height=bubble.height)
        bubble.bind(texture_size=lambda instance, value: self.update_bubble_height(instance, value, message_container))

        if align == "right":
            message_container.add_widget(Label(size_hint_x=0.2))
            message_container.add_widget(bubble)
        else:
            message_container.add_widget(bubble)
            message_container.add_widget(Label(size_hint_x=0.2))

        self.chat_history.add_widget(message_container)
        self.chat_history.height += bubble.height + 10
        self.scroll_view.scroll_y = 0

    def update_bubble_height(self, instance, value, container):
        instance.height = instance.texture_size[1] + 20
        container.height = instance.height

    def update_bg(self, *args):
        self.bg.size = args[0].size
        self.bg.pos = args[0].pos




if __name__ == "__main__":
    ChatApp().run()
