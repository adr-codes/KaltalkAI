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

class ChatBubble(Label):
    def __init__(self, text, align="left", **kwargs):
        super().__init__(text=text, size_hint_y=None, padding=(10, 10), **kwargs)
        self.bind(size=self.update_size)
        self.halign = align
        self.valign = "middle"

        # Define the app background color (adjust as needed)
        app_bg_color = (0.15, 0.15, 0.15, 1)  # Example: Dark gray background

        # Make the bubble slightly lighter
        lighter_color = tuple(min(c + 0.1, 1) for c in app_bg_color[:3]) + (1,)

        with self.canvas.before:
            Color(*lighter_color)  # Apply the adjusted color
            self.rect = RoundedRectangle(radius=[10, 10, 10, 10])

        self.bind(pos=self.update_rect, size=self.update_rect)
    
    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size
    
    def update_size(self, *args):
        self.text_size = (self.width - 20, None)
        self.texture_update()
        self.height = self.texture_size[1] + 20



class ChatApp(App):
    def build(self):
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=5)

        # Scrollable chat history
        self.scroll_view = ScrollView()
        self.chat_history = GridLayout(cols=1, size_hint_y=None, spacing=5)
        self.chat_history.bind(minimum_height=self.chat_history.setter('height'))
        self.scroll_view.add_widget(self.chat_history)

        # Input field, send button, and mic button
        input_layout = BoxLayout(size_hint_y=None, height=50, spacing=5)
        self.user_input = TextInput(hint_text="Type your message...", multiline=True, size_hint_x=0.7)
        self.user_input.bind(text=self.adjust_input_height)
        
        send_button = Button(text="Send", size_hint_x=0.15)
        send_button.bind(on_release=self.send_message)

        mic_button = Button(text="🎤", size_hint_x=0.15)
        mic_button.bind(on_release=self.voice_input)

        input_layout.add_widget(self.user_input)
        input_layout.add_widget(send_button)
        input_layout.add_widget(mic_button)

        self.layout.add_widget(self.scroll_view)
        self.layout.add_widget(input_layout)

        return self.layout

    def adjust_input_height(self, instance, value):
        max_height = 150  # Limit to about 5 lines
        min_height = 50   # Default height
        num_lines = value.count("\n") + 1  # Count lines based on newlines
        line_height = self.user_input.line_height
        self.user_input.height = min(max(num_lines * line_height + 20, min_height), max_height)
    
    def send_message(self, instance=None):
        user_message = self.user_input.text.strip()
        if not user_message:
            return  # Ignore empty messages

        self.add_message(user_message, align="right")

        # Send to backend
        try:
            response = requests.post("http://127.0.0.1:5000/chat", json={"message": user_message})
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
                audio = recognizer.listen(source, timeout=5)  # Listen for 5 seconds
                user_message = recognizer.recognize_google(audio)
                self.user_input.text = user_message  # Autofill text field
                self.send_message()  # Send the voice-recognized text
            except sr.UnknownValueError:
                self.add_message("Could not understand audio", align="left")
            except sr.RequestError:
                self.add_message("Speech service unavailable", align="left")

    def add_message(self, text, align="left"):
        bubble = ChatBubble(text=text, align=align, size_hint_x=0.75 if align == "right" else 0.85)
        self.chat_history.add_widget(bubble)
        self.chat_history.height += bubble.height + 10
        self.scroll_view.scroll_y = 0  # Auto-scroll to the bottom

if __name__ == "__main__":
    ChatApp().run()
