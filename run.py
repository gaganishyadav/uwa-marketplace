from dotenv import load_dotenv
load_dotenv()

from app import create_app, socketio
app = create_app()

if __name__ == '__main__':
    socketio.run(app, debug=True)
