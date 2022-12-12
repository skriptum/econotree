from otree.api import *
import time
import random


doc = "Experimental Auction Market as described in Smith (1965). Tests the efficiency of markets and the ability of participants to predict the market price."


class C(BaseConstants):
    NAME_IN_URL = 'auction_app'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 2
    ITEMS_PER_SELLER = 1
    VALUATION = cu(420)
    PRODUCTION_COSTS = cu(310)

class Subsession(BaseSubsession):
    pass
    

def creating_session(subsession: Subsession):
    
    players = subsession.get_players()
    if subsession.round_number == 1:
        buyers = []
        for p in players:
            buyer = p.id_in_group % 2 == 0
            if buyer:
                p.participant.is_buyer = True
                buyers.append(p)
            else:
                p.participant.is_buyer = False
        # this means if the player's ID is a multiple of 2, they are a buyer.

        
        # radnomly choose a buyer and convert to seller
        # based on the number of exceeding sellers set in SESSION_CONFIGS

        exceeding_sellers = int(subsession.session.config['exceeding_sellers'])
        #check if number of exceeding sellers is smaller than number of players
        if exceeding_sellers > len(players):    
            exceeding_sellers = len(players) - 2
            # if not, set to number of players minus 2
            print("Number of exceeding sellers has to be smaller than number of players. Number of exceeding sellers has been set to " + str(exceeding_sellers))

        #check if number of exceeding sellers is a multiple of 2
        if exceeding_sellers % 2 != 0:
            exceeding_sellers -= 1
            # if not, reduce by 1
            print("Number of exceeding sellers has to be a multiple of 2. Number of exceeding sellers has been set to " + str(exceeding_sellers))
    
        # randomly flip a buyer to seller
        for i in range(exceeding_sellers//2):  
            # because every flip produces an excess of 2 sellers (one more seller, one less buyer)
            random.choice(buyers).participant.is_buyer = False



        buyers_updated = [p for p in players if p.participant.is_buyer]

        #print functions for testing
        print(f"Number of Players: {len(players)}")
        print(f"Number of Buyers: {len(buyers_updated)}")
        print(f"Number of Sellers: {len(players) - len(buyers_updated)}")
        print(f"Excess Sellers: {(len(players)-len(buyers_updated)) - len(buyers_updated) } ")

        



    for p in players:
        if p.participant.is_buyer:
            p.is_buyer = 1
        else:
            p.is_buyer = 0
        
        p.success = False
        if p.is_buyer:
            p.num_items = 0
            p.break_even_point = C.VALUATION
            p.current_offer = cu(0)
        else:
            p.num_items = C.ITEMS_PER_SELLER
            p.break_even_point = C.PRODUCTION_COSTS
            p.current_offer = cu(420)


class Group(BaseGroup):
    start_timestamp = models.IntegerField()


class Player(BasePlayer):
    is_buyer = models.BooleanField()
    current_offer = models.CurrencyField()
    break_even_point = models.CurrencyField()
    num_items = models.IntegerField()
    success = models.BooleanField()
    transaction_price = models.CurrencyField()
    transaction_seconds = models.IntegerField(doc="Timestamp (seconds since beginning of trading)")


class Transaction(ExtraModel):
    group = models.Link(Group)
    buyer = models.Link(Player)
    seller = models.Link(Player)
    price = models.CurrencyField()
    seconds = models.IntegerField(doc="Timestamp (seconds since beginning of trading)")






# -------------------------------------------------------------------
# Trading Logic

def find_match(buyers, sellers):
    for buyer in buyers:
        for seller in sellers:
            if seller.num_items > 0 and seller.current_offer <= buyer.current_offer:
                # return as soon as we find a match (the rest of the loop will be skipped)
                return [buyer, seller]


def live_method(player: Player, data):
    group = player.group
    players = group.get_players()
    buyers = [p for p in players if p.is_buyer]
    sellers = [p for p in players if not p.is_buyer]
    news = None
    if data:
        offer = int(data['offer'])
        player.current_offer = offer
        if player.is_buyer:
            match = find_match(buyers=[player], sellers=sellers)
        else:
            match = find_match(buyers=buyers, sellers=[player])
        if match:
            [buyer, seller] = match
            price = buyer.current_offer
            Transaction.create(
                group=group,
                buyer=buyer,
                seller=seller,
                price=price,
                seconds=time.time() - group.start_timestamp,
            )
            buyer.num_items += 1
            seller.num_items -= 1
            buyer.payoff += buyer.break_even_point - price
            seller.payoff += price - seller.break_even_point

            #change player variable to success, so that it shows they sold/bought something
            buyer.success = True
            seller.success = True

            #change offers of the players to 0/higher than allowed, so that they cannot buy/sell again
            buyer.current_offer = 0  
            seller.current_offer = C.VALUATION + 1

            #record transaction price and time
            buyer.transaction_price = price
            seller.transaction_price = price
            buyer.transaction_seconds = int(time.time() - group.start_timestamp)
            seller.transaction_seconds = int(time.time() - group.start_timestamp)

            #publihs news to javascript
            news = dict(buyer=buyer.id_in_group, seller=seller.id_in_group, price=price)

    bids = sorted([p.current_offer for p in buyers if p.current_offer > 0], reverse=True)
    asks = sorted([p.current_offer for p in sellers if p.current_offer <= C.VALUATION])
    highcharts_series = [[tx.seconds, tx.price] for tx in Transaction.filter(group=group)]

    return {
        p.id_in_group: dict(
            num_items=p.num_items,
            current_offer=p.current_offer,
            payoff=p.payoff,
            bids=bids,
            asks=asks,
            highcharts_series=highcharts_series,
            news=news,
        )
        for p in players
    }




# -------------------------------------------------------------------
# PAGES
class WaitToStart(WaitPage):
    @staticmethod
    def after_all_players_arrive(group: Group):
        group.start_timestamp = int(time.time())


class Trading(Page):
    live_method = live_method

    @staticmethod
    def js_vars(player: Player):
        return dict(id_in_group=player.id_in_group, is_buyer=player.is_buyer)

    @staticmethod
    def get_timeout_seconds(player: Player):
        import time

        group = player.group
        return (group.start_timestamp + 2 * 60) - time.time()


class ResultsWaitPage(WaitPage):
    pass


class Results(Page):
    pass


page_sequence = [WaitToStart, Trading, ResultsWaitPage, Results]

