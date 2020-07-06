from flask import Flask, request, render_template
from flask_restful import Resource, Api

app = Flask(__name__)
api = Api(app)


@app.route('/')
def home():
    return render_template('index.html')


clipboard = {'clipboard': ''}


class Clipboard(Resource):
    def get(self):
        return clipboard

    def put(self):
        clipboard['clipboard'] = request.form['data']
        return clipboard


api.add_resource(Clipboard, '/api/clipboard')

if __name__ == '__main__':
    from waitress import serve
    serve(app, host="0.0.0.0", port=8899)
