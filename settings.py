from os import environ

SESSION_CONFIGS = [
    dict(
        name='auktion_experiment',
        app_sequence=["auction_app"],
        num_demo_participants=5,
        real_world_currency_per_point = 0.01,
        exceeding_sellers =  0# has to be multiple of 2!
        # when number of players is odd, then the number of buyers 
        # is automatically one more than the number of sellers (without exceeding sellers)
    ),
]

# if you set a property in SESSION_CONFIG_DEFAULTS, it will be inherited by all configs
# in SESSION_CONFIGS, except those that explicitly override it.
# the session config can be accessed from methods in your apps as self.session.config,
# e.g. self.session.config['participation_fee']

SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=1.00, participation_fee=0.00, doc=""
)

ROOMS = [
    dict(
        name="auktion_experiment", 
        display_name="Auktionsexperiment in GVWL",
        participant_label_file='_rooms/auction_ids.txt',
        use_secure_urls=False
    ),
]

PARTICIPANT_FIELDS = ["is_buyer"]
SESSION_FIELDS = []

# ISO-639 code
# for example: de, fr, ja, ko, zh-hans
LANGUAGE_CODE = 'en'

# e.g. EUR, GBP, CNY, JPY
REAL_WORLD_CURRENCY_CODE = 'EUR'
USE_POINTS = True

ADMIN_USERNAME = 'admin'
# for security, best to set admin password in an environment variable
ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD')

DEMO_PAGE_INTRO_HTML = """ """

SECRET_KEY = '8725285549134'