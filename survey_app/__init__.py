from otree.api import *


class C(BaseConstants):
    NAME_IN_URL = 'survey'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    age = models.IntegerField(label='Dein Alter?', min=13, max=125)
    gender = models.StringField(
        choices=['Männlich', 'Weiblich', 'Divers' ],
        label='Dein Gender?',
        widget=widgets.RadioSelect,
    )
    program = models.StringField(
        choices=["BWL", "VWL", "120 LP WiWi", "60 LP WiWi", "Lehramt", "anderes"],
        label="Dein Studiengang?"
    )
    



# FUNCTIONS
# PAGES
class Demographics(Page):
    form_model = 'player'
    form_fields = ['age', 'gender', 'program']

#Datenschutz
class Data(Page):
    form_model = 'player'
    form_fields = []

page_sequence = [Demographics, Data]
