from flask import Flask

from pagelogic import index

app = Flask(__name__)

@app.route('/' , methods=['GET','POST'])
def index_page():
    return index.index()

if __name__ == '__main__':
    app.run(port=5000, host='0.0.0.0', debug=True)