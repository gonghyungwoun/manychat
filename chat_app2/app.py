import random
from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, join_room, leave_room, send

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# In-memory storage for user points
user_points = {}

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        nickname = request.form['nickname']
        room = request.form['room']
        session['nickname'] = nickname
        session['room'] = room

        # Initialize user points if not already set
        if nickname not in user_points:
            user_points[nickname] = 0

        return redirect(url_for('chat'))
    return render_template('index.html')

@app.route('/chat')
def chat():
    nickname = session.get('nickname')
    room = session.get('room')
    if not nickname or not room:
        return redirect(url_for('index'))
    points = user_points.get(nickname, 0)
    return render_template('chat.html', nickname=nickname, room=room, points=points)

@socketio.on('join')
def handle_join(data):
    nickname = data['nickname']
    room = data['room']
    join_room(room)
    send(f'{nickname} 님이 입장하였습니다.', to=room)

@socketio.on('message')
def handle_message(data):
    room = data['room']
    nickname = data['nickname']
    message = data['msg']

    # Check if the message contains an emoji
    if any(emoji in message for emoji in ['😀', '😂', '😍', '😭', '😡']):
        if user_points[nickname] >= 10:
            user_points[nickname] -= 10
        else:
            send({'msg': "Not enough points to use an emoji!", 'nickname': "System"}, to=room)
            return
    else:
        user_points[nickname] += 1

    send({'msg': message, 'nickname': nickname, 'points': user_points[nickname]}, to=room)

@socketio.on('roulette')
def handle_roulette(data):
    nickname = data['nickname']
    room = data['room']

    if user_points[nickname] < 20:
        send({'msg': "Not enough points to spin the roulette!", 'nickname': "System"}, to=room)
        return

    # Deduct 20 points for spinning the roulette
    user_points[nickname] -= 20

    # Roulette logic
    result = random.choices(
        [100, 20, 0],
        [0.05, 0.85, 0.1]
    )[0]

    user_points[nickname] += result

    # Send the result message to the user
    if result == 100:
        send({'msg': "Congratulations! You won 100 points!", 'nickname': "System", 'points': user_points[nickname]}, to=room)
    elif result == 20:
        send({'msg': "You won 20 points!", 'nickname': "System", 'points': user_points[nickname]}, to=room)
    else:
        send({'msg': "You won nothing. Better luck next time!", 'nickname': "System", 'points': user_points[nickname]}, to=room)

@socketio.on('leave')
def handle_leave(data):
    nickname = data['nickname']
    room = data['room']
    leave_room(room)
    send(f'{nickname} has left the room.', to=room)

if __name__ == '__main__':
    socketio.run(app, debug=True)
