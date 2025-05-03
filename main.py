from tkinter import Image
from kivy.config import Config
Config.set("graphics", "width", "360")
Config.set("graphics", "height", "640")
Config.set("graphics", "resizable", "0")

import threading
import requests
import speech_recognition as sr
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.uix.relativelayout import RelativeLayout
from kivy.core.text import LabelBase    
import uuid
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.animation import Animation
from kivy.clock import Clock
import platform
# Check if running on Android
IS_ANDROID = platform.system() == 'Linux' and platform.machine().startswith('arm')

if IS_ANDROID:
    from android.permissions import request_permissions, Permission
    from jnius import autoclass, cast
    from android import activity

    # Request permissions on Android
    request_permissions([Permission.RECORD_AUDIO, Permission.INTERNET])

def listen_and_recognize(callback):
    if IS_ANDROID:
        # Android-specific voice recognition
        start_android_voice_recognition(callback)
    else:
        # PC-specific voice recognition
        r = sr.Recognizer()
        with sr.Microphone() as source:
            print("Say something:")
            audio = r.listen(source)
            try:
                text = r.recognize_google(audio)
                callback(text)
            except Exception as e:
                callback(f"Error: {e}")
def start_android_voice_recognition(callback):
    def on_result(requestCode, resultCode, intent_data):
        if resultCode == -1:  # RESULT_OK
            results = intent_data.getStringArrayListExtra(
                SpeechRecognizer.RESULTS_RECOGNITION)
            if results and len(results) > 0:
                Clock.schedule_once(lambda dt: callback(results[0]))
        
        activity.unbind(on_activity_result=on_result)
    
    activity.bind(on_activity_result=on_result)
    
    Intent = autoclass('android.content.Intent')
    SpeechRecognizer = autoclass('android.speech.SpeechRecognizer')
    
    intent = Intent(SpeechRecognizer.ACTION_RECOGNIZE_SPEECH)
    intent.putExtra(SpeechRecognizer.EXTRA_LANGUAGE_MODEL,
                   SpeechRecognizer.LANGUAGE_MODEL_FREE_FORM)
    
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    currentActivity = cast('android.app.Activity', PythonActivity.mActivity)
    currentActivity.startActivityForResult(intent, 1001)

session_id = str(uuid.uuid4())
Window.softinput_mode = 'pan'

LabelBase.register(name="EmojiFont", fn_regular="NotoColorEmoji-Regular.ttf")

class ChatBubble(Label):
    def __init__(self, text, align="right", **kwargs):
        super().__init__(**kwargs)
        self.text = text
        self.halign = "left"
        self.valign = "middle"
        self.padding = (10, 8)
        self.font_size = '16sp'
        self.size_hint = (None, None)
        self.text_size = (Window.width * 0.65, None)
        self.bind(texture_size=self.update_size)
        self.align = align
        
        with self.canvas.before:
            Color(*( (0.0, 0.6, 1, 1) if align == "right" else (0.25, 0.5, 0.25, 1) ))
            self.bg = RoundedRectangle(radius=[15])
        
        self.bind(pos=self.update_bg, size=self.update_bg)

    def update_size(self, *args):
        self.size = (self.texture_size[0] + dp(20), self.texture_size[1] + dp(16))
        if not hasattr(self, '_popped'):
            self._popped = True
            self.opacity = 0
            Animation(opacity=1, d=0.15).start(self)

    def update_bg(self, *args):
        if not self.parent:
            return
        
        margin = dp(10)
        if self.align == "right":
            self.bg.pos = (self.parent.width - self.width - margin, self.y)
        else:
            self.bg.pos = (margin, self.y)
        self.bg.size = self.size

    def pop_in(self):
        self.scale = 0.7
        anim = Animation(scale=1.0, d=0.2, t='out_back')
        anim.start(self)

class ChatApp(App):
    def on_enter_key(self, instance):
        self.send_message()

    def on_key_down(self, instance, keyboard, keycode, text, modifiers):
        if keycode == 40:  # Enter key
            if 'shift' in modifiers:
                return False  # Allow line break
            else:
                self.send_message()
                return True
        return False

    def build(self):
        self.recognizer =sr.Recognizer()
        self.session_id = str(uuid.uuid4())
        root = RelativeLayout()

        with root.canvas.before:
            self.bg = Rectangle(source='background.jpg', size=root.size, pos=root.pos)

        root.bind(size=self.update_bg, pos=self.update_bg)

        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=5)
        self.layout.size_hint = (1, 1)

        self.chat_history = GridLayout(cols=1, size_hint_y=None, spacing=3)
        self.chat_history.bind(minimum_height=self.chat_history.setter('height'))

        self.scroll_view = ScrollView(size_hint=(1, 0.85))
        self.scroll_view.add_widget(self.chat_history)

        self.scroll_view.bind(height=self._update_scroll_position)

        input_layout = BoxLayout(
            size_hint_y=None,
            height=dp(60),  # Fixed container height
            spacing=dp(5),
            padding=(dp(5), dp(5))
        )
        
        self.user_input = TextInput(
            hint_text="Type your message...",
            multiline=True,
            size_hint_x=0.8,
            size_hint_y=None,
            height=dp(50),
            padding=(dp(10), dp(10)),
            line_height=1.2,
            background_color=(1, 1, 1, 0.7),
            do_wrap=True,  # Enable word wrapping
            write_tab=False
        )
                            
        self.user_input.bind(
            text=self.adjust_input_height,
            on_text_validate=self.on_enter_key,
            on_key_down=self.on_key_down
        )

        send_button = Button(
            text="Send",
            size_hint_x=0.15,
            height=dp(50)
        )
        send_button.bind(on_release=self.send_message)

        mic_button = Button(
            size_hint_x=0.15,
            height=dp(40),
            background_normal='mic-button.png',
            background_down='mic-button-pressed.png'
        )
        mic_button.bind(on_release=self.voice_input)
        
        input_layout.add_widget(self.user_input)
        input_layout.add_widget(send_button)
        input_layout.add_widget(mic_button)

        self.layout.add_widget(self.scroll_view)
        self.layout.add_widget(input_layout)
        root.add_widget(self.layout)

        self.start_conversation()
        return root
    def _update_scroll_position(self, instance, value):
        """Ensures chat stays properly aligned during all resizes"""
        if self.user_input.height > dp(50):  # If expanded
            self.scroll_view.scroll_y = 0
    def listen_for_audio(self):
        # Show "Listening..." first
        self.display_message("Listening...", "ai")
        
        # Then delay the actual listening slightly to let the UI update
        Clock.schedule_once(lambda dt: self.voice_input(), 0.1)
    def adjust_input_height(self, instance, value):
        """Adjusts text input height and properly pushes chat history up"""
        # Calculate new height
        line_count = max(1, len(instance._lines))
        new_height = line_count * (instance.line_height + dp(10))
        new_height = max(dp(50), min(new_height, dp(120)))
        
        if abs(instance.height - new_height) > dp(1):
            # Calculate height difference
            height_diff = new_height - instance.height
            
            # Apply new height
            instance.height = new_height
            
            # Adjust chat history position
            if height_diff > 0:  # Only when expanding
                # Calculate scroll adjustment (convert pixels to 0-1 scale)
                scroll_adjust = height_diff / self.chat_history.height
                
                # Apply the adjustment smoothly
                Animation.stop_all(self.scroll_view)
                anim = Animation(scroll_y=max(0, self.scroll_view.scroll_y - scroll_adjust), 
                            duration=0.1)
                anim.start(self.scroll_view)
            
            # Force layout update
            instance.parent.parent.do_layout()
        
        # Ensure proper scrolling when at max height
        if new_height >= dp(120):
            instance.scroll_y = 0
            self.scroll_view.scroll_y = 0

    def start_conversation(self):
        self.add_message(f"Hey there! What can I do for you today?", align="left")

    def send_message(self, instance=None):
        user_message = self.user_input.text.strip()
        if not user_message:
            return

        self.add_message(user_message, align="right")
        self.user_input.text = ""

        self.typing_bubble = ChatBubble(text="thinking.", align="left")
        container = BoxLayout(size_hint_y=None, height=self.typing_bubble.height)
        self.typing_bubble.bind(texture_size=lambda instance, value: self.update_bubble_height(instance, value, container))
        container.add_widget(self.typing_bubble)
        container.add_widget(Label(size_hint_x=0.2))
        self.chat_history.add_widget(container)
        self.chat_history.height += self.typing_bubble.height + 10
        self.scroll_view.scroll_y = 0

        self.animate_thinking()
        threading.Thread(target=self.fetch_ai_reply, args=(user_message,)).start()

        # Scroll to bottom after sending
        Clock.schedule_once(lambda dt: setattr(self.scroll_view, 'scroll_y', 0), 0.1)

    def animate_thinking(self):
        self.thinking_state = 0
        def update_thinking(dt):
            states = ["thinking.", "thinking..", "thinking..."]
            if self.typing_bubble:
                self.typing_bubble.text = states[self.thinking_state % 3]
                self.typing_bubble.texture_update()
                self.thinking_state += 1
        self.thinking_event = Clock.schedule_interval(update_thinking, 0.5)

    def fetch_ai_reply(self, user_message):
        try:
            response = requests.post("https://kaltalkai.onrender.com/chat", 
                                   json={"message": user_message, "session_id": self.session_id})
            bot_reply = response.json().get("response", "Error: No response")
        except Exception:
            bot_reply = "Error: Could not connect to server."

        if hasattr(self, 'thinking_event'):
            Clock.schedule_once(lambda dt: self.thinking_event.cancel(), 0)

        Clock.schedule_once(lambda dt: self.animate_typing(bot_reply), 0)

    def animate_typing(self, full_text):
        self.typing_bubble.text = ""
        self.current_text_index = 0
        self.full_text = full_text

        def update_text(dt):
            if self.current_text_index < len(self.full_text):
                self.typing_bubble.text += self.full_text[self.current_text_index]
                self.typing_bubble.texture_update()
                self.current_text_index += 1
            else:
                return False

        Clock.schedule_interval(update_text, 0.03)

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
        bubble.pop_in()
        self.chat_history.height += bubble.height + 10
        self.scroll_view.scroll_y = 0

    def update_bubble_height(self, instance, value, container):
        instance.height = instance.texture_size[1] + 20
        container.height = instance.height

    def _start_listening(self):
        recognizer = sr.Recognizer()
        try:
            with sr.Microphone() as source:
                try:
                    audio = recognizer.listen(source, timeout=5)
                    user_message = recognizer.recognize_google(audio)
                    Clock.schedule_once(lambda dt: self._handle_voice_result(user_message), 0)
                except sr.UnknownValueError:
                    Clock.schedule_once(lambda dt: self.add_message("Sorry, I couldn't understand that.", align="left"), 0)
                except sr.RequestError:
                    Clock.schedule_once(lambda dt: self.add_message("Speech service unavailable.", align="left"), 0)
                except sr.WaitTimeoutError:
                    Clock.schedule_once(lambda dt: self.add_message("No speech detected. Try again.", align="left"), 0)
        except Exception as e:
            Clock.schedule_once(lambda dt: self.add_message(f"Mic error: {str(e)}", align="left"), 0)

    def _handle_voice_result(self, text):
        self.user_input.text = text
        self.send_message()

    def voice_input(self, instance=None):
        # Show "Listening..." message immediately
        self.listening_bubble = ChatBubble("Listening...", align="left")
        self.listening_container = BoxLayout(size_hint_y=None, height=self.listening_bubble.height)
        self.listening_bubble.bind(texture_size=lambda instance, value: self.update_bubble_height(instance, value, self.listening_container))
        self.listening_container.add_widget(self.listening_bubble)
        self.listening_container.add_widget(Label(size_hint_x=0.2))
        self.chat_history.add_widget(self.listening_container)
        self.chat_history.height += self.listening_bubble.height + 10
        self.scroll_view.scroll_y = 0
        
        # Start recognition
        threading.Thread(target=self._start_voice_recognition).start()
    def _pc_voice_recognition(self):
        r = sr.Recognizer()
        with sr.Microphone() as source:
            try:
                audio = r.listen(source, timeout=5)
                text = r.recognize_google(audio)
                Clock.schedule_once(lambda dt: self._handle_voice_result(text))
            except Exception as e:
                Clock.schedule_once(lambda dt: self.add_message(f"Error: {str(e)}", align="left"))
    def voice_input(self, instance=None):
        # Show "Listening..." message immediately
        self.listening_bubble = ChatBubble("Listening...", align="left")
        self.listening_container = BoxLayout(size_hint_y=None, height=self.listening_bubble.height)
        self.listening_bubble.bind(texture_size=lambda instance, value: self.update_bubble_height(instance, value, self.listening_container))
        self.listening_container.add_widget(self.listening_bubble)
        self.listening_container.add_widget(Label(size_hint_x=0.2))
        self.chat_history.add_widget(self.listening_container)
        self.chat_history.height += self.listening_bubble.height + 10
        self.scroll_view.scroll_y = 0
        
        # Start recognition
        threading.Thread(target=self._start_voice_recognition).start()

    def _start_voice_recognition(self):
        if IS_ANDROID:
            self._android_voice_recognition()
        else:
            self._pc_voice_recognition()

    def _android_voice_recognition(self):
        def on_result(requestCode, resultCode, intent_data):
            if resultCode == -1:  # RESULT_OK
                results = intent_data.getStringArrayListExtra(
                    SpeechRecognizer.RESULTS_RECOGNITION)
                if results and len(results) > 0:
                    Clock.schedule_once(lambda dt: self._handle_voice_result(results[0]))
            
            # Remove listening message
            Clock.schedule_once(lambda dt: self._remove_listening_message())

        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        currentActivity = cast('android.app.Activity', PythonActivity.mActivity)
        
        activity.bind(on_activity_result=on_result)
        
        Intent = autoclass('android.content.Intent')
        SpeechRecognizer = autoclass('android.speech.SpeechRecognizer')
        
        intent = Intent(SpeechRecognizer.ACTION_RECOGNIZE_SPEECH)
        intent.putExtra(SpeechRecognizer.EXTRA_LANGUAGE_MODEL,
                       SpeechRecognizer.LANGUAGE_MODEL_FREE_FORM)
        
        currentActivity.startActivityForResult(intent, 1001)

    def _pc_voice_recognition(self):
        r = sr.Recognizer()
        try:
            with sr.Microphone() as source:
                try:
                    audio = r.listen(source, timeout=5)
                    text = r.recognize_google(audio)
                    Clock.schedule_once(lambda dt: self._handle_voice_result(text))
                except sr.UnknownValueError:
                    Clock.schedule_once(lambda dt: self.add_message("Sorry, I couldn't understand that.", align="left"))
                except sr.RequestError:
                    Clock.schedule_once(lambda dt: self.add_message("Speech service unavailable.", align="left"))
                except sr.WaitTimeoutError:
                    Clock.schedule_once(lambda dt: self.add_message("No speech detected. Try again.", align="left"))
        except Exception as e:
            Clock.schedule_once(lambda dt: self.add_message(f"Mic error: {str(e)}", align="left"))
        finally:
            Clock.schedule_once(lambda dt: self._remove_listening_message())

    def _remove_listening_message(self):
        if hasattr(self, 'listening_container') and self.listening_container in self.chat_history.children:
            self.chat_history.remove_widget(self.listening_container)
            # Recalculate chat history height
            total_height = 0
            for child in self.chat_history.children:
                total_height += child.height + 10
            self.chat_history.height = total_height

    def _handle_voice_result(self, text):
        self._remove_listening_message()
        self.user_input.text = text
        self.send_message()
    

    def update_bg(self, *args):
        self.bg.size = args[0].size
        self.bg.pos = args[0].pos

if __name__ == "__main__":
    ChatApp().run()