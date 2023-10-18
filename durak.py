import json
import os, keyboard
import threading
import time
import random
import sys
import requests
import ast

HOST = "127.0.0.1"
PORT = 4433

selector = "ᐞ"
selected_counter = 2

require_update = True
you_win = False
you_lose = False
post_requested = False
sync_locked = False
dont_add = False
dont_deal = False
taking = False
taking_accepted = False
debug = False
trump = ["Ace Spades"]


def clear():
    if os.name == 'nt':
        os.system("cls")
    else:
        os.system("clear")

def shuffle_cards(deck):
    cards = list(deck.keys())
    random.shuffle(cards)

    shuffled_deck = {}
    for card in cards:
        shuffled_deck[card] = deck[card]

    return shuffled_deck

def deal_cards(num_cards):
    try:
        global playing_deck
        global trump
        global dont_deal

        if dont_deal:
            return []
        if debug:
            with open("log.txt", "a") as f:
                f.write(str(len(playing_deck)) + "\n")
        
        if num_cards > len(list(playing_deck.items())):
            playing_deck[trump] = playing_deck_preserved[trump]
            trump = ""
            dont_deal = True

        if num_cards > len(list(playing_deck.items())):
            num_cards = len(list(playing_deck.items()))

        dealt_cards = []

        for _ in range(0, num_cards):
            card = list(playing_deck.items())[0][0]
            dealt_cards.append(card)
            #print(card)
            #with open("cards.txt", "a") as f:
                #f.write(card + "\n")
            del playing_deck[card]

        return dealt_cards
    except Exception as e:
        #print("deal_cards: " + str(e))
        return []

def move_left():
    global selected_counter
    global require_update

    if selected_counter > min_cards:
        selected_counter -= 1
    
    require_update = True

def move_right():
    global selected_counter
    global require_update

    if selected_counter < max_cards:
        selected_counter += 1

    require_update = True

def can_play(card):
    global trump_suit
    global require_update
    global dont_add
    card_rank = card.split(" ")[0]
    card_suit = card.split(" ")[1]
    if your_turn:
        if table_cards_enemy == [] and table_cards_your == [] and table_cards_your_defended == [] and table_cards_enemy_defended == []:
            return True
        
        for card in table_cards_your:
            if card.split(" ")[0] == card_rank:
                return True
        
        for card in table_cards_enemy:
            if card.split(" ")[0] == card_rank:
                return True
        
        for card in table_cards_your_defended:
            if card.split(" ")[0] == card_rank:
                return True
        
        for card in table_cards_enemy_defended:
            if card.split(" ")[0] == card_rank:
                return True
    else:
        if table_cards_enemy == []:
            require_update = True
            return False
        for counter in range(0, len(table_cards_enemy)):
            if table_cards_enemy[counter] not in table_cards_enemy_defended:
                card_enemy = table_cards_enemy[counter]
                break
        enemy_card_suit = card_enemy.split(" ")[1]
        if card_suit == enemy_card_suit or card_suit == trump_suit:
            defend_weight = playing_deck_preserved.get(card).get("weight")
            attack_weight = playing_deck_preserved.get(card_enemy).get("weight")
            if defend_weight > attack_weight:
                table_cards_enemy_defended.append(card_enemy)
                table_cards_your_defended.append(card)

                table_cards_enemy.remove(card_enemy)
                dont_add = True
                return True
            
        return False

def action():
    global post_requested
    global your_cards
    global enemy_cards
    global sync_locked
    global your_turn
    global taking
    global taking_accepted
    global require_update

    sync_locked = True
    if debug:
        with open("log.txt", "at") as f:
            f.write(str(table_cards_enemy) + "\n")
            f.write(str(table_cards_your) + "\n")
            f.write(str(table_cards_enemy_defended) + "\n")
            f.write(str(table_cards_your_defended) + "\n")

    if your_turn:
        if taking:
            taking_accepted = True
            post_requested = True
            sync_locked = False
            require_update = True
            return

        if table_cards_enemy + table_cards_your == []:
            flush()
            
            enemy_cards_amount = len(enemy_cards)
            your_cards_amount = len(your_cards)

            if your_turn:
                if your_cards_amount < 6:
                    your_cards.extend(deal_cards(6 - your_cards_amount))
                if enemy_cards_amount < 6:
                    enemy_cards.extend(deal_cards(6 - enemy_cards_amount))
            
            else:
                if enemy_cards_amount < 6:
                    enemy_cards.extend(deal_cards(6 - enemy_cards_amount))
                if your_cards_amount < 6:
                    your_cards.extend(deal_cards(6 - your_cards_amount))
            
            your_turn = not your_turn
    else:
        if table_cards_enemy + table_cards_your + table_cards_enemy_defended + table_cards_your_defended != []:
            taking = True
            
            if not taking_accepted:
                post_requested = True
                sync_locked = False
                require_update = True

                return
            
            taking = False
            taking_accepted = False

            grab()

            enemy_cards_amount = len(enemy_cards)
            your_cards_amount = len(your_cards)

            if your_turn:
                if your_cards_amount < 6:
                    your_cards.extend(deal_cards(6 - your_cards_amount))
                if enemy_cards_amount < 6:
                    enemy_cards.extend(deal_cards(6 - enemy_cards_amount))
            else:
                if enemy_cards_amount < 6:
                    enemy_cards.extend(deal_cards(6 - enemy_cards_amount))
                if your_cards_amount < 6:
                    your_cards.extend(deal_cards(6 - your_cards_amount))
    
    post_requested = True
    sync_locked = False
    # except Exception as e:
    #     print(e)
    #     post_requested = True
    #     sync_locked = False
        #raise Exception("Test")
def weight(card):
    return playing_deck_preserved.get(card).get("weight")

def sort(cards: list):
    spades = []
    diamonds = []
    clubs = []
    hearts = []

    for card in cards:
        card_suit = card.split(" ")[1]

        #print(card_suit)

        if card_suit == "Spades":
            spades.append(card)
            
        if card_suit == "Diamonds":
            diamonds.append(card)

        if card_suit == "Clubs":
            clubs.append(card)

        if card_suit == "Hearts":
            hearts.append(card)
    
    spades.sort(key=weight)
    diamonds.sort(key=weight)
    clubs.sort(key=weight)
    hearts.sort(key=weight)

    cards = spades + diamonds + clubs + hearts

    return cards


def grab():
    global table_cards_enemy
    global table_cards_your
    global table_cards_your_defended
    global table_cards_enemy_defended
    global your_cards
    global require_update
    global your_turn

    your_cards.extend(table_cards_enemy)
    your_cards.extend(table_cards_your)
    your_cards.extend(table_cards_your_defended)
    your_cards.extend(table_cards_enemy_defended)

    with open("log.txt", "at") as f:
        f.write("Grabbed!")

    table_cards_enemy = []
    table_cards_your = []
    table_cards_your_defended = []
    table_cards_enemy_defended = []

    require_update = True


def flush():
    global table_cards_enemy
    global table_cards_your
    global table_cards_your_defended
    global table_cards_enemy_defended
    global your_cards
    global enemy_cards
    global require_update
    global your_turn

    table_cards_enemy = []
    table_cards_your = []
    table_cards_your_defended = []
    table_cards_enemy_defended = []

    if debug:
        with open("log.txt", "at") as f:
            f.write("your_turn = " + str(your_turn) + "\n")

    require_update = True



def play(cards):
    global require_update
    global your_cards
    global max_cards
    global selected_counter
    global post_requested
    global sync_locked
    global dont_add

    sync_locked = True

    if len(cards) == 0:
        sync_locked = False
        return

    card = cards[selected_counter - 1]

    if not can_play(card):
        sync_locked = False
        return

    if selected_counter == 1:
        pass
        #selected_counter += 1
    else:
        selected_counter -= 1

    your_cards.remove(card)

    max_cards = len(your_cards)
    
    if not dont_add:
        table_cards_your.append(card)
    else:
        dont_add = False

    sync_locked = False
    require_update = True
    post_requested = True
    

def set_as_trump(deck, suit):
    for card in deck:
        if suit in card:
            deck[card]["weight"] += 9
        
    return deck

def get_first_turn():
    your_trumps = [999]
    enemy_trumps = [999]

    for card in your_cards:
        weight = playing_deck_preserved.get(card).get("weight")
        if weight >= 15:
            your_trumps.append(weight)

    for card in enemy_cards:
        weight = playing_deck_preserved.get(card).get("weight")
        if weight >= 15:
            enemy_trumps.append(weight)
    
    if min(enemy_trumps) == min(your_trumps):
        return random.choice([True, False])

    if min(enemy_trumps) < min(your_trumps):
        return False
    
    return True

cards_dict = {
    'Six Spades': {'unicode': '🂦', 'weight': 6},
    'Seven Spades': {'unicode': '🂧', 'weight': 7},
    'Eight Spades': {'unicode': '🂨', 'weight': 8},
    'Nine Spades': {'unicode': '🂩', 'weight': 9},
    'Ten Spades': {'unicode': '🂪', 'weight': 10},
    'Jack Spades': {'unicode': '🂫', 'weight': 11},
    'Queen Spades': {'unicode': '🂭', 'weight': 12},
    'King Spades': {'unicode': '🂮', 'weight': 13},
    'Ace Spades': {'unicode': '🂡', 'weight': 14},

    'Six Hearts': {'unicode': '🂶', 'weight': 6},
    'Seven Hearts': {'unicode': '🂷', 'weight': 7},
    'Eight Hearts': {'unicode': '🂸', 'weight': 8},
    'Nine Hearts': {'unicode': '🂹', 'weight': 9},
    'Ten Hearts': {'unicode': '🂺', 'weight': 10},
    'Jack Hearts': {'unicode': '🂻', 'weight': 11},
    'Queen Hearts': {'unicode': '🂽', 'weight': 12},
    'King Hearts': {'unicode': '🂾', 'weight': 13},
    'Ace Hearts': {'unicode': '🂱', 'weight': 14},

    'Six Diamonds': {'unicode': '🃆', 'weight': 6},
    'Seven Diamonds': {'unicode': '🃇', 'weight': 7},
    'Eight Diamonds': {'unicode': '🃈', 'weight': 8},
    'Nine Diamonds': {'unicode': '🃉', 'weight': 9},
    'Ten Diamonds': {'unicode': '🃊', 'weight': 10},
    'Jack Diamonds': {'unicode': '🃋', 'weight': 11},
    'Queen Diamonds': {'unicode': '🃍', 'weight': 12},
    'King Diamonds': {'unicode': '🃎', 'weight': 13},
    'Ace Diamonds': {'unicode': '🃁', 'weight': 14},
    
    'Six Clubs': {'unicode': '🃖', 'weight': 6},
    'Seven Clubs': {'unicode': '🃗', 'weight': 7},
    'Eight Clubs': {'unicode': '🃘', 'weight': 8},
    'Nine Clubs': {'unicode': '🃙', 'weight': 9},
    'Ten Clubs': {'unicode': '🃚', 'weight': 10},
    'Jack Clubs': {'unicode': '🃛', 'weight': 11},
    'Queen Clubs': {'unicode': '🃝', 'weight': 12},
    'King Clubs': {'unicode': '🃞', 'weight': 13},
    'Ace Clubs': {'unicode': '🃑', 'weight': 14}
}

playing_deck = shuffle_cards(cards_dict)
playing_deck_preserved = dict(playing_deck)

your_cards = deal_cards(6)

enemy_cards = deal_cards(6)

min_cards = 1
max_cards = len(your_cards)

table_cards_your = []
table_cards_enemy = []
table_cards_your_defended = []
table_cards_enemy_defended = []

trump = deal_cards(1)[0]
trump_suit = trump.split(" ")[1]

playing_deck_preserved = set_as_trump(playing_deck_preserved, trump_suit)

your_turn = get_first_turn()

# keyboard.add_hotkey("enter", lambda: play(your_cards))
# keyboard.add_hotkey("f", lambda: action())
# keyboard.add_hotkey('left', lambda: move_left())
# keyboard.add_hotkey('right', lambda: move_right())
#keyboard.add_hotkey("g", lambda: get_card())

running = True

def async_sync(game_code):
    global save
    global running
    global playing_deck, playing_deck_preserved, your_cards, enemy_cards, table_cards_your, table_cards_enemy, table_cards_your_defended, table_cards_enemy_defended, trump, trump_suit, your_turn, taking, taking_accepted
    global require_update
    global post_requested

    while running:
        if sync_locked:
            if debug:
                with open("log.txt", "at") as f:
                    f.write("Sync locked!" + "\n")
            time.sleep(0.1)
            continue

        if post_requested:
            if debug:
                with open("log.txt", "at") as f:
                    f.write("Post requested!" + "\n")
            if connection_type == "create":
                save = {
                    'playing_deck': playing_deck,
                    'playing_deck_preserved': playing_deck_preserved,
                    'your_cards': your_cards,
                    'enemy_cards': enemy_cards,
                    'table_cards_your': table_cards_your,
                    'table_cards_enemy': table_cards_enemy,
                    'table_cards_your_defended': table_cards_your_defended,
                    'table_cards_enemy_defended': table_cards_enemy_defended,
                    'trump': trump,
                    'trump_suit': trump_suit,
                    'your_turn': your_turn,
                    'taking': taking,
                    'taking_accepted': taking_accepted
                }
            else:
                save = {
                    'playing_deck': playing_deck,
                    'playing_deck_preserved': playing_deck_preserved,
                    'your_cards': enemy_cards,
                    'enemy_cards': your_cards,
                    'table_cards_your': table_cards_enemy,
                    'table_cards_enemy': table_cards_your,
                    'table_cards_your_defended': table_cards_enemy_defended,
                    'table_cards_enemy_defended': table_cards_your_defended,
                    'trump': trump,
                    'trump_suit': trump_suit,
                    'your_turn': not your_turn,
                    'taking': taking,
                    'taking_accepted': taking_accepted
                }

            params = {
                'game_code': game_code,
                'game_data': save
            }

            req = requests.post(url=f"http://{HOST}:{PORT}/push", json=params).text + "\n"

            if debug:
                with open("log.txt", "at") as f:
                    f.write(req)

            post_requested = False
            continue
        
        if debug:
            with open("log.txt", "at") as f:
                f.write("Working!" + "\n")

        try:
            new_save = json.loads(requests.get(url=f"http://{HOST}:{PORT}/get", params={"game_code": game_code}).text)
        except ConnectionError:
            if debug:
                with open("log.txt", "at") as f:
                    f.write("Closed!" + "\n")
            clear()
            print("[ERROR] Lost connection! Closing...")
            time.sleep(3)
            sys.exit()

        if save != new_save:
            trump = new_save["trump"]
            trump_suit = new_save["trump_suit"]
            playing_deck = new_save["playing_deck"]
            playing_deck_preserved = new_save["playing_deck_preserved"]
            taking = new_save["taking"]
            taking_accepted = new_save["taking_accepted"]

            if connection_type == "create":
                your_cards = new_save["your_cards"]
                enemy_cards = new_save["enemy_cards"]
                table_cards_your = new_save["table_cards_your"]
                table_cards_enemy = new_save["table_cards_enemy"]
                table_cards_your_defended = new_save["table_cards_your_defended"]
                table_cards_enemy_defended = new_save["table_cards_enemy_defended"]
                your_turn = new_save["your_turn"]
            else:
                your_cards = new_save["enemy_cards"]
                enemy_cards = new_save["your_cards"]
                table_cards_your_defended = new_save["table_cards_enemy_defended"]
                table_cards_enemy_defended = new_save["table_cards_your_defended"]
                table_cards_your = new_save["table_cards_enemy"]
                table_cards_enemy = new_save["table_cards_your"]
                your_turn = not new_save["your_turn"]

            save = new_save

            require_update = True

        time.sleep(3)

def post():
    if connection_type == "create":
        save = {
            'playing_deck': playing_deck,
            'playing_deck_preserved': playing_deck_preserved,
            'your_cards': your_cards,
            'enemy_cards': enemy_cards,
            'table_cards_your': table_cards_your,
            'table_cards_enemy': table_cards_enemy,
            'table_cards_enemy_defended': table_cards_enemy_defended,
            'table_cards_your_defended': table_cards_your_defended,
            'trump': trump,
            'trump_suit': trump_suit,
            'your_turn': your_turn,
            'taking': taking,
            'taking_accepted': taking_accepted
        }
    else:
        save = {
            'playing_deck': playing_deck,
            'playing_deck_preserved': playing_deck_preserved,
            'your_cards': enemy_cards,
            'enemy_cards': your_cards,
            'table_cards_your': table_cards_enemy,
            'table_cards_enemy': table_cards_your,
            'table_cards_enemy_defended': table_cards_your_defended,
            'table_cards_your_defended': table_cards_enemy_defended,
            'trump': trump,
            'trump_suit': trump_suit,
            'your_turn': not your_turn,
            'taking': taking,
            'taking_accepted': taking_accepted
        }

    params = {
        'game_code': game_code,
        'game_data': save
    }

    req = requests.post(url=f"http://{HOST}:{PORT}/push", json=params).text + "\n"

    if debug:
        with open("log.txt", "at") as f:
            f.write(req)

def Update():
    global max_cards
    global your_cards

    your_cards = sort(your_cards)
    #print(your_cards)
    if not debug:
        clear()
    max_cards = len(your_cards)

    if you_win:
        print("You WIN!")
        input()
        sys.exit()
    if you_lose:
        print("You LOSE!")
        input()
        sys.exit()
    for card in enemy_cards:
        #print(cards_dict.get(card).get("unicode"), end="")
        print("🂠", end="")
    
    if taking and your_turn:
        print(" ⋄", end="")
        
    
    print("\n", end="")

    for card in table_cards_enemy_defended + table_cards_enemy:
        print(cards_dict.get(card).get("unicode"), end="")
    if trump != "":
        print("     ", cards_dict.get(trump).get("unicode"), end="")
    if playing_deck != {}:
        print("🂠", end="")
    
    print("\n", end="")

    for card in table_cards_your_defended + table_cards_your:
        print(cards_dict.get(card).get("unicode"), end="")

    print("\n", end="")
        
    

    for card in your_cards:
        print(cards_dict.get(card).get("unicode"), end="")
    if your_turn:
        print(" ☜", end="")
    
    if taking and not your_turn:
        print(" ⋄", end="")

    print(f"\n{selector:>{selected_counter}}")

connection_type = input("Connection type: ")

if not debug:
    keyboard.add_hotkey("enter", lambda: play(your_cards))
    keyboard.add_hotkey("f", lambda: action())
    keyboard.add_hotkey('left', lambda: move_left())
    keyboard.add_hotkey('right', lambda: move_right())

if connection_type == "create":
    clear()
    if debug:
        keyboard.add_hotkey("enter", lambda: play(your_cards))
        keyboard.add_hotkey("f", lambda: action())
        keyboard.add_hotkey('left', lambda: move_left())
        keyboard.add_hotkey('right', lambda: move_right())

    game_code = requests.get(url=f"http://{HOST}:{PORT}/create_new_game").text

    post()

    save = json.loads(requests.get(url=f"http://{HOST}:{PORT}/get", params={"game_code": game_code}).text)

    input(f"Room code is {game_code}.\nPress ENTER when your friend connects. ")
    #post_requested = True
else:
    if debug:
        keyboard.add_hotkey("shift+enter", lambda: play(your_cards))
        keyboard.add_hotkey("shift+f", lambda: action())
        keyboard.add_hotkey('shift+left', lambda: move_left())
        keyboard.add_hotkey('shift+right', lambda: move_right())

    game_code = input("Game code (XXXXXX): ")

    save = json.loads(requests.get(url=f"http://{HOST}:{PORT}/get", params={"game_code": game_code}).text)

    playing_deck = save["playing_deck"]
    playing_deck_preserved = save["playing_deck_preserved"]
    your_cards = save["enemy_cards"]
    enemy_cards = save["your_cards"]
    table_cards_your = save["table_cards_enemy"]
    table_cards_enemy = save["table_cards_your"]
    table_cards_your_defended = save["table_cards_enemy_defended"]
    table_cards_enemy_defended = save["table_cards_your_defended"]
    trump = save["trump"]
    trump_suit = save["trump_suit"]
    your_turn = not save["your_turn"]
    taking = save["taking"]
    taking_accepted = save["taking_accepted"]

# Create two threads
thread1 = threading.Thread(target=async_sync, args=(game_code,))

# Start the threads
thread1.start()

#time.sleep(1)

while True:
    if taking and taking_accepted and not your_turn:
        action()
    try:
        if require_update:
            

            Update()

            require_update = False

        if your_cards == [] and playing_deck == {}:
            clear()
            print("You WIN!")
            time.sleep(10)
            running = False
            break

        if enemy_cards == [] and playing_deck == {}:
            clear()
            print("You LOSE!")
            time.sleep(10)
            running = False
            break
        time.sleep(0.1)
    except KeyboardInterrupt:
        running = False
        break

