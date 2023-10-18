from flask import Flask
from flask import request
import random

app = Flask(__name__)

games = {
}

@app.route("/create_new_game", methods=['GET'])
def create_new_game():
    game_code = str(random.randint(100000, 999999))
    games[game_code] = {}
    return game_code, 200

@app.route("/push", methods=['POST'])
def push():
    content_type = request.headers.get('Content-Type')

    if (content_type == 'application/json'):
        body = request.json

        game_code = body.get('game_code')
        game_data = body.get('game_data')
        
        games[game_code] = game_data

        print(body)

        return 'Success', 200
    else:
        return 'Content-Type not supported!'

@app.route("/get", methods=['GET'])
def get():
    game_code = request.args.get('game_code')
    return games[game_code]

@app.route("/get_current_state", methods=['GET'])
def get_current_state():
    game_code = request.args.get('game_code')
    return str(len(game_code))

app.run("127.0.0.1", 4433, debug=False)