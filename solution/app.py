from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///project.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

from flask import jsonify, request

class Country(db.Model):
    __tablename__ = "countries"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False, unique=True)
    alpha2 = db.Column(db.String(3))
    alpha3 = db.Column(db.String(4))
    region = db.Column(db.String(80))

    def to_dict(self):
        return {
            'name': self.name,
            'alpha2': self.alpha2,
            'alpha3': self.alpha3,
            'region': self.region
        }


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(31))
    email = db.Column(db.String(51))
    password = db.Column(db.String())
    country_code = db.Column(db.String(3), db.ForeignKey('countries.alpha2'))
    is_public = db.Column(db.Boolean())
    phone_number = db.Column(db.String(21))
    image = db.Column(db.String(201))

    def __init__(self, login, email, country_code, is_public, phone_number, image):
        self.login = login
        self.email = email
        self.country_code = country_code
        self.is_public = is_public
        self.phone_number = phone_number
        self.image = image


    def set_password(self, password: str):
        if len(password) < 6:
            return 0, 'length error'
        if not (set(password) & set('qwertyuiopasdfghjklzxcvbnm')):
            return 0, 'no latin symbols'
        if not (set(password) & set('1234567890')):
            return 0, 'no numbers'
        self.password = generate_password_hash(password)
        return 1, ''

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def to_dict(self):
        return {'login': self.login,
                'email': self.email,
                'countryCode': self.country_code,
                'isPublic': self.is_public,
                'phone': self.phone_number}

@app.route('/api/ping', methods=['GET'])
def send():
    return jsonify({"status": "ok"}), 200

@app.route('/api/countries', methods=['GET'])
def countries():
    regions = request.args.getlist('region')
    answer = Country.query.all()
    if regions:
        answer = Country.query.filter(Country.region.in_(regions)).all()

    if not answer:
        return jsonify({'reason': 'not found'}), 400
    answer = [i.to_dict() for i in answer]
    return jsonify(answer), 200

@app.route('/api/countries/<alpha2>')
def counties_by_alpha(alpha2):
    answer = Country.query.filter_by(alpha2=alpha2).first()
    if answer is None:
        return jsonify({'reason': 'not found'}), 404
    answer = answer.to_dict()
    return jsonify(answer), 200

@app.route('/api/auth/register', methods=['POST'])
def register():
    new_user_data = request.json
    print(new_user_data)
    login = new_user_data.get('login', '')
    email = new_user_data.get('email', '')
    password = new_user_data.get('password', '')
    country_code = new_user_data.get('countryCode', '')
    is_public = new_user_data.get('isPublic', True)
    phone = new_user_data.get('phone', '')
    image = new_user_data.get('image', '')

    if not login or not email or not password or not country_code:
        return jsonify({'reason': 'missing data'}), 400

    if not Country.query.filter_by(alpha2=country_code).first():
        return jsonify({'reason': 'no such country'}), 400

    if phone[0] != '+':
        return jsonify({'reason': 'bad phone number'}), 400

    if len(image) > 200:
        return jsonify({'reason': 'too long image'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'reason': 'not uniq email'}), 409

    if User.query.filter_by(login=login).first():
        return jsonify({'reason': 'not uniq login'}), 409

    new_user = User(login=login,
                    email=email,
                    country_code=country_code,
                    is_public=is_public,
                    image=image,
                    phone_number=phone)

    status, message = new_user.set_password(password)
    if not status:
        return jsonify({'reason': message}), 400

    db.session.add(new_user)
    db.session.commit()
    return jsonify({'profile': new_user.to_dict()}), 201



if __name__ == "__main__":

    app.run(port=57424, debug=True)