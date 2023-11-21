from otree.api import *
import time
import random


doc = "Experimental Auction Market as described in Smith (1965). Tests the efficiency of markets and the ability of participants to predict the market price."


class C(BaseConstants):
    NAME_IN_URL = 'auction_app'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 7 #just stop after x number of rounds 
    ITEMS_PER_SELLER = 1
    VALUATION = cu(420)
    PRODUCTION_COSTS = cu(310)

class Subsession(BaseSubsession):
    #models for number of players, sellers and buyers
    number_players = models.IntegerField()
    number_sellers = models.IntegerField()
    number_buyers = models.IntegerField()
    

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

        #save the number of sellers and buyers in the group
        subsession.number_players = len(players)
        subsession.number_sellers = len(players) - len(buyers_updated)
        subsession.number_buyers = len(buyers_updated)


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
            p.current_offer = cu(C.VALUATION)


class Group(BaseGroup):
    start_timestamp = models.IntegerField()



class Player(BasePlayer):
    is_buyer = models.BooleanField()
    current_offer = models.CurrencyField()
    break_even_point = models.CurrencyField()
    num_items = models.IntegerField()
    success = models.BooleanField()
    transaction_price = models.CurrencyField()
    transaction_seconds = models.FloatField(doc="Timestamp (seconds since beginning of trading)")

    def custom_export(players):
        yield ["Buyer, Seller, Round, Price, Seconds"]
        transactions = Transaction.filter()
        for t in transactions:
            yield [t.buyer.id_in_group, t.seller.id_in_group, t.buyer.round_number, t.price, t.seconds]


class Transaction(ExtraModel):
    group = models.Link(Group)
    buyer = models.Link(Player)
    seller = models.Link(Player)
    price = models.CurrencyField()
    seconds = models.IntegerField(doc="Timestamp (seconds since beginning of trading)")






# -------------------------------------------------------------------
# Trading Logic

def find_match(buyers, sellers):
    """
    
    """
    
    for buyer in buyers:
        for seller in sellers:
            if seller.num_items > 0 and seller.current_offer <= buyer.current_offer:
                if seller.current_offer > C.VALUATION or buyer.current_offer < C.PRODUCTION_COSTS:
                    print("Offer is out of range")
                    
                else:
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
        player.current_offer = cu(offer)
            
        if player.is_buyer:
            match = find_match(buyers=[player], sellers=sellers)
        else:
            match = find_match(buyers=buyers, sellers=[player])

        # if player.current_offer > C.VALUATION or player.current_offer < C.PRODUCTION_COSTS:
        #     news = dict(buyer="AAA", seller="BBB", price="CCC")
        #     match = None
        #     print("Offer is out of range")

        if match:
            [buyer, seller] = match
            price = buyer.current_offer
            if price > C.VALUATION or player.current_offer < C.PRODUCTION_COSTS:
                news = dict(buyer="AAA", seller="AAA", price="AAA")
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
            buyer.transaction_seconds = time.time() - group.start_timestamp
            seller.transaction_seconds = time.time() - group.start_timestamp

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

def vars_for_admin_report(subsession):
    prices = sorted([p.transaction_price for p in subsession.get_players() if p.success and p.is_buyer])
    return dict(prices=prices)


# -------------------------------------------------------------------
# PAGES
class WaitToStart(WaitPage):
    @staticmethod
    def after_all_players_arrive(group: Group):
        group.start_timestamp = int(time.time())

class BeforeTrading(Page):

    # only display this page in the first round
    @staticmethod
    def is_displayed(player: Player):

        if player.subsession.round_number == 1:
            return True
        else:
            return False
    
    @staticmethod
    def vars_for_template(player: Player):
        return dict(num_rounds=player.subsession.session.config['num_rounds'])
    

class Trading(Page):
    live_method = live_method

    @staticmethod
    def js_vars(player: Player):
        return dict(id_in_group=player.id_in_group, is_buyer=player.is_buyer)

    @staticmethod
    def get_timeout_seconds(player: Player):
        import time

        group = player.group
        return (group.start_timestamp + 45) - time.time()


class ResultsWaitPage(WaitPage):
    pass


class Results(Page):
    timeout_seconds = 11

    #filter out all successfol transactions
    @staticmethod
    def js_vars(player: Player):
        series = []
        for p in player.subsession.get_players():
            #if successful and only if buyer (so that it does not show up twice)
            if p.success and p.is_buyer:
                series.append([p.transaction_seconds, p.transaction_price])
        return dict(series=series)

class AfterTrading(Page):
    
        # only display this page in the last round
        @staticmethod
        def is_displayed(player: Player):
    
            num_rounds = player.subsession.session.config['num_rounds']
            if player.subsession.round_number == num_rounds:
                return True
            else:
                return False

        @staticmethod
        def vars_for_template(player: Player):
            num_rounds = player.subsession.session.config['num_rounds']

            payoff_buyers = 0
            payoff_sellers = 0
            for p in player.get_others_in_subsession():
                if p.is_buyer:
                    payoff_buyers += p.payoff
                else:
                    payoff_sellers += p.payoff
            
            combined_payoff = payoff_buyers + payoff_sellers

            return dict(
                num_players=player.subsession.session.num_participants,
                num_rounds=num_rounds,
                payoff_buyers=payoff_buyers,
                payoff_sellers=payoff_sellers,
                combined_payoff=combined_payoff,
            )

page_sequence = [ BeforeTrading, WaitToStart, Trading, ResultsWaitPage, Results, AfterTrading]

