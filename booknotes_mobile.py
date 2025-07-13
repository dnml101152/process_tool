from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button


class MyLayout(BoxLayout):
    def __init__(self, **kwargs):
        super(MyLayout, self).__init__(orientation='vertical', **kwargs)

        self.label = Label(text="Hello, Kivy!", font_size=24)
        self.add_widget(self.label)

        self.text_input = TextInput(hint_text="Enter your name", multiline=False)
        self.add_widget(self.text_input)

        self.button = Button(text="Greet Me")
        self.button.bind(on_press=self.on_button_press)
        self.add_widget(self.button)

    def on_button_press(self, instance):
        name = self.text_input.text
        if name.strip():
            self.label.text = f"Hello, {name}!"
        else:
            self.label.text = "Please enter your name."


class MyApp(App):
    def build(self):
        return MyLayout()


if __name__ == "__main__":
    MyApp().run()
