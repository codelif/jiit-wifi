"""
Used to login/logout of Campus Wifi easily on Android
"""

from io import BytesIO
import toga
import requests
from toga.style import Pack
from toga.style.pack import COLUMN, ROW, LEFT, CENTER
from toga.colors import RED, GREEN, WHITE
import json
import os
import time
import xml.etree.ElementTree as ET



class JIITWiFi(toga.App):
    def startup(self):
        """Construct and show the Toga application.

        Usually, you would add your application to a main content box.
        We then create a main window (with a name matching the app), and
        show the main window.
        """
        main_box = toga.Box()
        user_box = toga.Box()
        pass_box = toga.Box()

        self.DATAFILE = "data.json"
        self.basep = self.paths.cache
        self.path = os.path.join(self.basep, self.DATAFILE)

        self.sophos = Sophos()

        id_value = None
        pass_value = None
        if (d:=self.get_data()):
            id_value = d["id"]
            pass_value = d["pswd"]

        user_label = toga.Label("UserID: ", style=Pack(text_align=LEFT))
        pass_label = toga.Label("Pass: ", style=Pack(text_align=LEFT))
        self.confirm_label = toga.Label("", style=Pack(text_align=CENTER))


        self.user_input = toga.TextInput(style=Pack(), value=id_value)
        self.pass_input = toga.PasswordInput(style=Pack(), value=pass_value)

        user_box.add(user_label)
        user_box.add(self.user_input)

        pass_box.add(pass_label)
        pass_box.add(self.pass_input)

        login_button = toga.Button(
                "Login",
                on_press=self.login,
                style=Pack(padding=5),
                )

        logout_button = toga.Button(
                "Logout",
                on_press=self.logout,
                style=Pack(padding=5),
                )

        main_box.add(user_box)
        main_box.add(pass_box)
        main_box.add(login_button)
        main_box.add(logout_button)
        main_box.add(self.confirm_label)

        main_box.style.update(direction=COLUMN, padding=10)
        user_box.style.update(direction=ROW, padding=5)
        pass_box.style.update(direction=ROW, padding=5)

        self.user_input.style.update(flex=1)
        self.pass_input.style.update(flex=1)

        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = main_box
        self.main_window.show()
    

    def cache_inputs(self):
        user = self.user_input.value
        pswd = self.pass_input.value
        
        self.save_data({"id":user, "pswd": pswd})
        return user,pswd

    def login(self, widget):
        user, pswd = self.cache_inputs()
        if not (user and pswd):
            return

        rtmsg = self.sophos.login(user, pswd)
        new_text = ""
        new_color = WHITE

        if rtmsg.startswith("You are signed in as "):
            new_text = "Successfully logged in!"
            new_color=GREEN
        elif "Invalid user name/password." in rtmsg:
            new_text = "Invalid user name/password"
            new_color=RED
        elif "You have reached the maximum login limit." in rtmsg:
            new_text = "Max Login Limit. Signout from other device."
            new_color=RED
        else:
            new_text = "Some error has occured. Please open a issue on github."
            new_color=RED
        
        
        self.confirm_label.text = new_text
        self.confirm_label.style.update(color=new_color)
    

    
    def logout(self, widget):
        user, pswd = self.cache_inputs()
        if not (user and pswd):
            return
        rtmsg = self.sophos.logout(user)

        new_text = ""
        new_color = WHITE

        if "ve signed out" in rtmsg:
            new_text = "Successfully logged out!"
            new_color=GREEN
        else:
            new_text = "Some error has occured. Please open a issue on github."
            new_color=RED
        
        
        self.confirm_label.text = new_text
        self.confirm_label.style.update(color=new_color)

    def get_data(self):
        try:
            with open(self.path) as f:
                data = json.load(f)
            return data
        except Exception:
            return None
        
    def save_data(self, data):
        self.basep.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w+") as f:
            json.dump(data, f)


class Sophos():
    def __init__(self):
        self.GATEWAY = "http://172.16.68.6:8090/"
        self.LOGIN_LINK = "login.xml"
        self.LOGOUT_LINK = "logout.xml"
    
    def __getmilliepoch(self):
        return str(int(time.time()*100))

    def login(self, user: str, pswd: str) -> str:
        LINK = self.GATEWAY + self.LOGIN_LINK
        data = {
                "mode": "191",
                "username": user,
                "password": pswd,
                "a": self.__getmilliepoch(),
                "producttype": "0"
        }

        resp = requests.post(LINK, data=data)
        return self.get_message(resp.content)

    def logout(self, user: str) -> str:
        LINK = self.GATEWAY + self.LOGOUT_LINK
        data = {
                "mode": "193",
                "username": user,
                "a": self.__getmilliepoch(),
                "producttype": "0"
        }

        resp = requests.post(LINK, data=data)
        return self.get_message(resp.content)

    def log(self, prefix: str, content):
        with open(f"/tmp/jiit_wifi_{prefix}_{int(time.time())}.xml", "w+") as f:
            f.write(content)

    def get_message(self, response):
        f = BytesIO(response)
        tree = ET.parse(f)

        root = tree.getroot()
        return root.find("./message").text

def main():
    return JIITWiFi()
