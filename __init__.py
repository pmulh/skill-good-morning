# Copyright 2016 Mycroft AI, Inc.
#
# This file is part of Mycroft Core.
#
# Mycroft Core is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Mycroft Core is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Mycroft Core.  If not, see <http://www.gnu.org/licenses/>.

from adapt.intent import IntentBuilder
from mycroft import MycroftSkill, intent_handler
from mycroft.util import play_mp3
from time import sleep
from datetime import datetime
from dateutil import tz
import pytz
from mycroft.messagebus.message import Message
import json
from mycroft.audio import wait_while_speaking
import requests

class GoodMorningSkill(MycroftSkill):
    def __init__(self):
        """ The __init__ method is called when the Skill is first constructed.
        It is often used to declare variables or perform setup actions, however
        it cannot utilise MycroftSkill methods as the class does not yet exist.
        """
        super().__init__()
        self.learning = True

    def initialize(self):
        """ Perform any final setup needed for the skill here.
        This function is invoked after the skill is fully constructed and
        registered with the system. Intents will be registered and Skill
        settings will be available."""
        my_setting = self.settings.get('my_setting')

#    @intent_handler(IntentBuilder('ThankYouIntent').require('ThankYouKeyword'))
#    def handle_thank_you_intent(self, message):
#        """ This is an Adapt intent handler, it is triggered by a keyword."""
#        self.speak_dialog("welcome")

#    @intent_handler('HowAreYou.intent')
#    def handle_how_are_you_intent(self, message):
#        """ This is a Padatious intent handler.
#        It is triggered using a list of sample phrases."""
#        self.speak_dialog("how.are.you")
    
    @intent_handler('GoodMorning.intent')
    def handle_good_morning_intent(self, message):
        """ This is a Padatious intent handler.
        It is triggered using a list of sample phrases."""
        self.play_alarm_sounds(num_plays = 5, secs_between_plays = 40)

        timezone = pytz.timezone('Europe/Dublin')
        now = datetime.now(timezone)
        day = now.strftime('%A')
        month = now.strftime('%B')
        date = now.strftime('%d')
        date_int = int(date)
        if 4 <= date_int <= 20 or 24 <= date_int <= 30:
            suffix = "th"
        else:
            suffix = ["st", "nd", "rd"][date_int % 10 - 1]
        time = now.strftime('%H:%M')
        date_dialog = "it's " + time + ' on ' + day + ', the ' + date + suffix + ' of ' + month
        self.speak_dialog("good.morning")
        self.speak_dialog(date_dialog)
        # TODO - add dialog for 'sunrise is/was at <sunrise time>'; similarly for sunset
        r = requests.get('https://api.sunrise-sunset.org/json', params={'lat': 54.607868, 'lng': -5.926437}).json()['results']
        # convert returned UTC times into local times
        utc_sunrise = datetime.strptime(datetime.now().strftime('%y%m%d')+r['sunrise'], '%y%m%d%I:%M:%S %p').replace(tzinfo=tz.tzutc())
        utc_sunset = datetime.strptime(datetime.now().strftime('%y%m%d')+r['sunset'], '%y%m%d%I:%M:%S %p').replace(tzinfo=tz.tzutc())
        local_sunrise = utc_sunrise.astimezone(tz.tzlocal())
        local_sunrise_strf = local_sunrise.strftime('%I:%M %p')
        local_sunset = utc_sunset.astimezone(tz.tzlocal())
        local_sunset_strf = local_sunset.strftime('%I:%M %p')
        if now > local_sunrise:
            sunrise_sunset_dialog = 'Sunrise was at ' + local_sunrise_strf
        else:
            sunrise_sunset_dialog = 'Sunrise will be at ' + local_sunrise_strf
        sunrise_sunset_dialog = sunrise_sunset_dialog + ', and sunset will be at ' + local_sunset_strf
        self.speak_dialog(sunrise_sunset_dialog)
        self.bus.emit(Message(msg_type="recognizer_loop:utterance",
                              data={"utterances": ['tell me the weather forecast']}))
        wait_while_speaking()
        sleep(2) # To give time for the forecast to complete before the reminders are read
        self.parse_reminders(date = now.strftime('%d/%m/%y'))
        wait_while_speaking()
        self.speak_dialog("have a great day")
        wait_while_speaking()
        self.bus.emit(Message(msg_type="recognizer_loop:utterance",
                              data={"utterances": ['tell me the news']}))
        # TODO: Turn on radio after about half an hour (when news should be finished)

    def play_alarm_sounds(self, num_plays = 3, secs_between_plays = 30):
        alarm_sound = '/home/pi/mycroft-core/skills/mycroft-alarm.mycroftai/sounds/chimes.mp3'
        alarm_sound_duration = 22
        play_count = 0
        while play_count < num_plays:
            play_count = play_count + 1
            play_mp3(alarm_sound)
            sleep(alarm_sound_duration + secs_between_plays)
        return

    def parse_reminders(self, date):
        with open('/home/pi/.mycroft/skills/GoodMorningSkill/reminders.json') as f:
            data = json.load(f)
        if date in data.keys():
            self.log.info(data[date])
            for reminder in data[date]:
                self.log.info(reminder)
                if reminder['type'] == 'birthday':
                    birthday_dialog = "Don't forget that today is " + reminder['details'] + "'s birthday"
                    self.speak_dialog(birthday_dialog)
                elif reminder['type'] == 'todo':
                    todo_dialog = "You have a reminder for today to " + reminder['details']
                    self.speak_dialog(todo_dialog)
        else:
            self.speak_dialog('You have no reminders for today')
        return 

    def stop(self):
        pass


def create_skill():
    return GoodMorningSkill()
