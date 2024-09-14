# app.py

from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from models import db, User, Vehicle, ParkingSpot, Reservation
from forms import RegistrationForm, LoginForm, VehicleForm, ReservationForm

# Initialize the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = '123456'  # Replace with a secure secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///parking_app.db'

# Initialize the database
db.init_app(app)

# Initialize the login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User loader callback
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Route for the home page
@app.route('/')
def index():
    return render_template('index.html')

# Route for user registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        new_user = User(
            full_name=form.full_name.data,
            email=form.email.data,
            phone_number=form.phone_number.data,
            password=hashed_password
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

# Route for user login
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'danger')
    return render_template('login.html', form=form)

# Route for user logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# Route for the user dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

# Route to add a vehicle
@app.route('/add_vehicle', methods=['GET', 'POST'])
@login_required
def add_vehicle():
    form = VehicleForm()
    if form.validate_on_submit():
        new_vehicle = Vehicle(
            user_id=current_user.id,
            vehicle_model=form.vehicle_model.data,
            vehicle_size=form.vehicle_size.data,
            license_plate=form.license_plate.data
        )
        db.session.add(new_vehicle)
        db.session.commit()
        flash('Vehicle added successfully!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('add_vehicle.html', form=form)

# Route to make a reservation
@app.route('/reserve', methods=['GET', 'POST'])
@login_required
def reserve():
    form = ReservationForm()
    form.vehicle_id.choices = [(v.id, f"{v.vehicle_model} ({v.license_plate})") for v in current_user.vehicles]
    if form.validate_on_submit():
        vehicle = Vehicle.query.get(form.vehicle_id.data)
        # Find an available spot that matches the vehicle size
        available_spot = ParkingSpot.query.filter_by(is_available=True, spot_type=vehicle.vehicle_size).first()
        if available_spot:
            new_reservation = Reservation(
                user_id=current_user.id,
                vehicle_id=vehicle.id,
                spot_id=available_spot.id,
                reservation_date_in=form.reservation_date_in.data,
                reservation_date_out=form.reservation_date_out.data,
                status='Confirmed'
            )
            available_spot.is_available = False
            db.session.add(new_reservation)
            db.session.commit()
            flash('Reservation successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('No available spots for the selected vehicle type.', 'danger')
    return render_template('reserve.html', form=form)

# Route to check in
@app.route('/checkin/<int:reservation_id>')
@login_required
def checkin(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    if reservation.user_id != current_user.id:
        flash('You are not authorized to check in this reservation.', 'danger')
        return redirect(url_for('dashboard'))
    reservation.check_in_time = datetime.utcnow()
    reservation.status = 'Checked-in'
    db.session.commit()
    flash('Checked in successfully!', 'success')
    return redirect(url_for('dashboard'))

# Route to check out
@app.route('/checkout/<int:reservation_id>')
@login_required
def checkout(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    if reservation.user_id != current_user.id:
        flash('You are not authorized to check out this reservation.', 'danger')
        return redirect(url_for('dashboard'))
    reservation.check_out_time = datetime.utcnow()
    reservation.status = 'Checked-out'
    reservation.spot.is_available = True
    db.session.commit()
    flash('Checked out successfully!', 'success')
    return redirect(url_for('dashboard'))

# Function to initialize parking spots
def initialize_parking_spots():
    spot_types = ['Compact', 'Handicap', 'Large']
    spot_counts = {'Compact': 15, 'Handicap': 5, 'Large': 5}
    spot_number = 1
    for spot_type, count in spot_counts.items():
        for _ in range(count):
            spot = ParkingSpot(spot_type=spot_type, spot_number=spot_number)
            db.session.add(spot)
            spot_number += 1
    db.session.commit()
    print("Parking spots initialized.")

# Initialize the database and create tables
with app.app_context():
    db.create_all()
    # Initialize parking spots if they don't exist
    if not ParkingSpot.query.first():
        initialize_parking_spots()

# Run the application
if __name__ == '__main__':
    app.run(debug=True)
