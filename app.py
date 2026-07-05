from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

#Importing werkzeug.security for password management
from werkzeug.security import check_password_hash, generate_password_hash

#Pillow and datetime import for image manipulation
from PIL import Image
from datetime import datetime, timedelta


from models import User
#Importing database DAOs
import guides_dao, participants_dao, tours_dao, reservations_dao, admin_dao
#Importing regex operation library
import re

import os
BASE_DIR = os.path.abspath(os.path.dirname(__file__))


app = Flask(__name__)
app.config["SECRET_KEY"] = "MWT AUTHENTICATION KEY"

login_manager = LoginManager()
login_manager.init_app(app)

#Configuring standard profile image height
PROFILE_IMG_HEIGHT = 130

@app.route("/")
def home():
	tours = tours_dao.get_all_tours()
	return render_template("index.html", tours = tours)

@app.route("/signup")
def registration_page():
	#Retrieving all languages for registration
	languages = guides_dao.get_all_languages()

	return render_template("register.html", languages=languages)

@app.route("/register", methods=["POST"])
def register():
	role = request.form.get("role")
	email = request.form.get("email")
	first_name = request.form.get("first_name")
	last_name = request.form.get("last_name")
	password = generate_password_hash(request.form.get("password"))
	
	if not first_name or not re.match(r"^[A-Za-z]+$", first_name) or len(first_name) < 2:
		flash("Invalid first name format.", "danger")
		return redirect(url_for("registration_page"))
	if not last_name or not re.match(r"^[A-Za-z]+$", last_name) or len(last_name) < 2:
		flash("Invalid last name format.", "danger")
		return redirect(url_for("registration_page"))
 
	img_name = ""
	
	try:
		if role == "guide":
			profile_image = request.files["profile_image"]
			
			#Image manipulation with Pillow
			img = Image.open(profile_image)
			
			width, height = img.size
			
			new_width = PROFILE_IMG_HEIGHT * width / height
			size = new_width, PROFILE_IMG_HEIGHT
			img.thumbnail(size, Image.Resampling.LANCZOS)
			
			left = new_width / 2 - PROFILE_IMG_HEIGHT / 2
			top = 0
			right = new_width / 2 + PROFILE_IMG_HEIGHT / 2
			bottom = PROFILE_IMG_HEIGHT
	  
			img = img.crop((left, top, right, bottom))
	  
			secs = int(datetime.now().timestamp())
			ext = profile_image.filename.split(".")[-1]
			
			img_name = f"pfp_{secs}.{ext}"
			pfp_dir = os.path.join(BASE_DIR, "static", "images", "profile_images")
			os.makedirs(pfp_dir, exist_ok=True)  # Creates folder if not exists
			img.save(os.path.join(pfp_dir, img_name))

			
			selected_languages = request.form.getlist("languages")
			guides_dao.new_guide(first_name, last_name, email, password, "/images/profile_images/" + img_name, selected_languages)
				
			flash("Registration successful! You can now log in.", "success")

		elif role == "participant":
			participants_dao.new_participant(first_name, last_name, email, password)
			flash("Registration successful! You can now log in.", "success")
			
		return redirect(url_for("login_page"))

	except Exception:
		flash("Something went wrong while registering, retry", "danger")
		return redirect(url_for("registration_page"))

@app.route("/login")
def login_page():
	return render_template("login.html")

@app.route("/authenticate", methods=["POST"])
def authenticate():
	role = request.form.get("role")
	email = request.form.get("email")
	password = request.form.get("password")

	
	#Admin account
	if email == "diegol@admin.com" and password == "admin":
		user = User(
			role="admin",
			id=0,
			first_name="Diego",
			last_name="Laudicina",
			email=email,
			password=generate_password_hash("admin"),
			profile_image=None
		)
		result = login_user(user)
		flash("Admin Login successful!", "success")
		return redirect(url_for("admin_dashboard"))

	#retrieving user based on role
	if role == "guide":
		db_user = guides_dao.get_guide_from_email(email)
	elif role == "participant":
		db_user = participants_dao.get_participant_from_email(email)
	else:
		return redirect(url_for("login_page"))
		
	#Checking if user and password exists
	if not db_user or not check_password_hash(db_user["password"], password):
		flash("Invalid email or password", "danger")
		return redirect(url_for("login_page"))
	else:
		# Creating user object
		if role == "guide":
			user = User(
				role="guide", 
				id=db_user["id"], 
				first_name=db_user["first_name"],
				last_name=db_user["last_name"], 
				email=db_user["email_address"],
				password=db_user["password"], 
				profile_image=db_user["profile_image"]
			)
		else:
			user = User(
				role="participant", 
				id=db_user["id"], 
				first_name=db_user["first_name"],
				last_name=db_user["last_name"], 
				email=db_user["email_address"],
				password=db_user["password"], 
				profile_image=None
			)
		
		#Creating user session
		result = login_user(user)
		if result: 
			flash(f"Login successful! Welcome, {user.first_name}", "success")
		else:
			flash("Login failed", "danger")
			
		return redirect(url_for("home"))

@login_required
@app.route("/profile")
def profile():
	if current_user.role == 'participant':
		reservations = reservations_dao.get_reservations_for_participant(current_user.id)
		#Current date
		now = datetime.now()
		upcoming_reservations = [r for r in reservations if datetime.strptime(r['raw_date'], '%Y-%m-%d %H:%M') >= now]

		past_reservations = [r for r in reservations if datetime.strptime(r['raw_date'], '%Y-%m-%d %H:%M') < now]

		return render_template("profile_participant.html", upcoming_reservations=upcoming_reservations, past_reservations=past_reservations)
	
	elif current_user.role == 'guide':

		tours = tours_dao.get_all_tours_for_guide(current_user.id)
		
		for tour in tours:
			tour['dates'] = reservations_dao.get_dates_and_reservations_for_tour(tour['id'])
		return render_template("profile_guide.html", tours = tours)

	elif current_user.role == 'admin':
		return redirect(url_for("admin_dashboard"))

@login_required
@app.route("/admin_dashboard")
def admin_dashboard():
	if current_user.role != 'admin':
		return redirect(url_for('home'))
		
	stats = admin_dao.get_admin_dashboard_stats()
	return render_template("admin_dashboard.html", **stats)

@app.route("/tours")
def tours_page():
	tours = tours_dao.get_all_tours()
	
	# Fetch filters from the URL
	date_start_str = request.args.get("date_start")
	date_end_str = request.args.get("date_end")
	max_duration = request.args.get("duration")
	languages = request.args.getlist("language")
	
	# Map HTML language values to the database values
	lang_map = {'it': 'Italian', 'en': 'English', 'es': 'Spanish', 'pt': 'Portuguese', 'de': 'German'}
	selected_langs = [lang_map.get(lang) for lang in languages if lang in lang_map]

	filtered_tours = []
	
	# Parse dates if present
	start_date = None
	end_date = None
	if date_start_str:
		start_date = datetime.strptime(date_start_str, "%Y-%m-%d").date()
	if date_end_str:
		end_date = datetime.strptime(date_end_str, "%Y-%m-%d").date()
		
	for tour in tours:
		# Filter by duration
		if max_duration and int(tour['duration']) > int(max_duration):
			continue
			
		# Filter by language
		if selected_langs and tour['language'] not in selected_langs:
			continue
			
		# Calculate upcoming dates (lazy evaluation)
		upcoming_dates = tours_dao.get_upcoming_tour_dates(tour['id'], tour['max_participants'])
		valid_dates = [d for d in upcoming_dates if not d['is_full']]
		
		if date_start_str or date_end_str:
			has_valid_date = False
			
			for date_info in valid_dates:
				tour_date = datetime.strptime(date_info['full_date'], '%Y-%m-%d %H:%M').date()
				valid_start = (start_date is None or tour_date >= start_date)
				valid_end = (end_date is None or tour_date <= end_date)
				
				if valid_start and valid_end:
					has_valid_date = True
					break
			
			if not has_valid_date:
				continue
				
		# Attach the first 3 upcoming dates to the tour object for displaying
		tour['upcoming_dates'] = valid_dates[:3]
		filtered_tours.append(tour)

	filters = {
		'date_start': date_start_str or '',
		'date_end': date_end_str or '',
		'duration': max_duration or 360,
		'languages': languages
	}

	return render_template("tours.html", tours=filtered_tours, filters=filters)

@app.route("/tour/<int:tour_id>")
def tour_page(tour_id):
	tour = tours_dao.get_tour_by_id(tour_id)
	if not tour:
		return redirect(url_for('tours_page'))
	
	upcoming_dates = tours_dao.get_upcoming_tour_dates(tour_id, tour['max_participants'])
	valid_dates = [d for d in upcoming_dates if not d['is_full']]

	#If there is a logged in participant, it retrieves all the tours booked by that participant
	user_booked_dates = []
	if current_user.is_authenticated and current_user.role == 'participant':
		user_booked_dates = reservations_dao.get_user_booked_dates_for_tour(current_user.id, tour_id)
		user_schedule = reservations_dao.get_user_schedule(current_user.id)
		
		for d in valid_dates:
			d['is_overlap'] = False
			if d['full_date'] in user_booked_dates:
				continue
				
			new_start = datetime.strptime(d['full_date'], '%Y-%m-%d %H:%M')
			new_end = new_start + timedelta(minutes=tour['duration'])
			
			for block in user_schedule:
				if new_start < block['end'] and block['start'] < new_end:
					d['is_overlap'] = True
					break
	
	return render_template("tour.html", tour=tour, upcoming_dates=valid_dates, user_booked_dates=user_booked_dates)

@login_required
@app.route("/book_tour/<int:tour_id>")
def book_tour_page(tour_id):
	if current_user.role != 'participant':
		return redirect(url_for('tours_page'))
		
	tour = tours_dao.get_tour_by_id(tour_id)
	if not tour:
		return redirect(url_for('tours_page'))
	
	#Recalculating upcoming tour dates
	upcoming_dates = tours_dao.get_upcoming_tour_dates(tour_id, tour['max_participants'])
	valid_dates = [d for d in upcoming_dates if not d['is_full']]
	
	# Retrieve the pre-selected date from query string if available
	selected_date = request.args.get('booking_date')
	
	user_booked_dates = reservations_dao.get_user_booked_dates_for_tour(current_user.id, tour_id)
	user_schedule = reservations_dao.get_user_schedule(current_user.id)
	
	for d in valid_dates:
		d['is_overlap'] = False
		if d['full_date'] in user_booked_dates:
			continue
			
		new_start = datetime.strptime(d['full_date'], '%Y-%m-%d %H:%M')
		new_end = new_start + timedelta(minutes=tour['duration'])
		
		for block in user_schedule:
			if new_start < block['end'] and block['start'] < new_end:
				d['is_overlap'] = True
				break
				
	return render_template("book_tour.html", tour=tour, upcoming_dates=valid_dates, selected_date=selected_date, user_booked_dates=user_booked_dates)

@login_required
@app.route("/confirm_booking", methods=["POST"])
def confirm_booking():
	if current_user.role != 'participant':
		return redirect(url_for('home'))
		
	tour_id = request.form.get("tour_id")
	booking_date = request.form.get("booking_date")
	
	# Retrieving extra participants, if present
	extra_participants = []
	for i in range(1, 4):
		first = request.form.get(f"person_{i}_first")
		last = request.form.get(f"person_{i}_last")
		if first and last:
			if not re.match(r"^[A-Za-z]+$", first) or len(first) < 2 or not re.match(r"^[A-Za-z]+$", last) or len(last) < 2:
				flash("Invalid name format for additional participants.", "danger")
				return redirect(url_for('book_tour_page', tour_id=tour_id))
			extra_participants.append({"first_name": first, "last_name": last})
			
	
	result = reservations_dao.new_reservation(tour_id, current_user.id, booking_date, extra_participants)
	
	if result == True:
		flash("Reservation created successfully!", "success")
	else:
		flash("Reservation failed.", "danger")
		
	return redirect(url_for('tours_page'))

@login_required
@app.route("/edit_booking/<int:r_id>", methods=['GET', 'POST'])
def edit_booking_page(r_id):
	if current_user.role != 'participant':
		return redirect(url_for('home'))

	reservation = reservations_dao.get_reservation_by_id(r_id)
	if not reservation or reservation['p_id'] != current_user.id:
		return redirect(url_for('profile'))

	# Check 24 hours constraint
	booking_datetime = datetime.strptime(reservation['date'], '%Y-%m-%d %H:%M')
	if datetime.now() > booking_datetime - timedelta(hours=24):
		return redirect(url_for('profile'))

	tour = tours_dao.get_tour_by_id(reservation['tour_id'])
	extra_participants = reservations_dao.get_extra_participants_for_reservation(r_id)

	if request.method == 'POST':
		new_booking_date = request.form.get("booking_date")
		
		new_extra = []
		for i in range(1, 4):
			first = request.form.get(f"person_{i}_first")
			last = request.form.get(f"person_{i}_last")
			if first and last:
				if not re.match(r"^[A-Za-z]+$", first) or len(first) < 2 or not re.match(r"^[A-Za-z]+$", last) or len(last) < 2:
					flash("Invalid name format for additional participants.", "danger")
					return redirect(url_for('edit_booking_page', r_id=r_id))
				new_extra.append({"first_name": first, "last_name": last})

		reservations_dao.update_reservation(r_id, current_user.id, tour['id'], reservation['d_id'], new_booking_date, new_extra)
		flash("Reservation updated successfully!", "success")
		return redirect(url_for('profile'))

	current_reservation_spots = 1 + len(extra_participants)
	upcoming_dates = tours_dao.get_upcoming_tour_dates_with_current(tour['id'], tour['max_participants'], reservation['date'], current_reservation_spots)
	
	user_booked_dates = reservations_dao.get_user_booked_dates_for_tour(current_user.id, tour['id'])
	
	return render_template("book_tour.html", 
						   tour=tour, 
						   upcoming_dates=upcoming_dates, 
						   reservation=reservation,
						   selected_date=reservation['date'],
						   extra_participants=extra_participants,
						   user_booked_dates=user_booked_dates)

@login_required
@app.route("/delete_booking/<int:r_id>", methods=["POST"])
def delete_booking(r_id):
	if current_user.role != 'participant':
		return redirect(url_for('home'))
		
	reservation = reservations_dao.get_reservation_by_id(r_id)
	if not reservation or reservation['p_id'] != current_user.id:
		return redirect(url_for('profile'))
		
	# Check 24 hours constraint
	booking_datetime = datetime.strptime(reservation['date'], '%Y-%m-%d %H:%M')
	if datetime.now() > booking_datetime - timedelta(hours=24):
		#redirect back to profile
		return redirect(url_for('profile'))
		
	reservations_dao.delete_reservation(r_id)
	flash("Reservation cancelled successfully!", "success")
	return redirect(url_for('profile'))


@login_required
@app.route("/create_tour")
def create_tour():
	#Check if current user is not a guide
	if current_user.role != 'guide':
		return redirect(url_for(home))
	
	languages = guides_dao.get_languages_spoken_by_guide(current_user.id)
	return render_template("create_tour.html", languages=languages, scheduled_days_map={})

@login_required
@app.route("/new_tour", methods=["POST"])
def new_tour():
	title = request.form.get("title")
	language = request.form.get("language")
	duration = request.form.get("duration")
	description = request.form.get("description")
	meeting_point = request.form.get("meeting_point")
	max_participants = request.form.get("max_participants")

	
	# for every stop, a text field with the stop name 
	raw_stops = request.form.getlist("stops")
	stops = [stop.strip() for stop in raw_stops if stop.strip()]
	
	if len(stops) < 4:
		flash("Validation error: at least 4 stops are required.", "danger")
		return redirect(url_for('create_tour'))
	
	#days are checkboxes 
	# corresponding starting times are formatted as time_dayname">
	selected_days = request.form.getlist("days")
	schedules = []
	for day in selected_days:
		time = request.form.get(f"time_{day}")
		if time:
			schedules.append({"day_of_week": day, "start_time": time})
			
	uploaded_photos = request.files.getlist("photos")
	valid_photos = [p for p in uploaded_photos if p and p.filename]
	photo_names = []
	
	if len(valid_photos) != 5:
		flash("You need to upload exactly 5 promotional photos for the tour.", "danger")
		return redirect(url_for('create_tour'))
	
	for index, photo in enumerate(valid_photos):
		if photo and photo.filename:
			img = Image.open(photo)

			secs = int(datetime.now().timestamp())
			ext = photo.filename.split(".")[-1]
			img_name = f"tour_{secs}_{index}.{ext}"
			
			#photo names list for db insertion
			photo_names.append(f"tours/{img_name}")

			# Image Optimization
			max_size = (1920, 1080)
			img.thumbnail(max_size, Image.Resampling.LANCZOS)
			tours_dir = os.path.join(BASE_DIR, "static", "images", "tours")
			os.makedirs(tours_dir, exist_ok=True)
			img.save(os.path.join(tours_dir, img_name), optimize=True, quality=80)

			
	tour_data = {
		"title": title,
		"language": language,
		"duration": duration,
		"description": description,
		"meeting_point": meeting_point,
		"max_participants": max_participants,
		"g_id": current_user.id,
		"stops": stops,
		"schedules": schedules,
		"photos": photo_names
	}
	
	result = tours_dao.new_tour(tour_data)
	if result:
		flash("Tour created successfully!", "success")
		return redirect(url_for('tours_page'))
	else:
		flash("Something went wrong creating the tour.", "danger")
		return redirect(url_for('create_tour'))

@login_required
@app.route("/edit_tour/<int:tour_id>", methods = ['GET', 'POST'])
def edit_tour_page(tour_id):
	# Check if current user is not a guide
	if current_user.role != 'guide':
		return redirect(url_for('home'))

	tour = tours_dao.get_tour_by_id(tour_id)

	if not tour:
		return redirect(url_for('home'))
		
	# Ensure the logged-in guide is the owner of the tour
	if tour['g_id'] != current_user.id:
		return redirect(url_for('home'))
		
	# Check if the tour has reservations
	has_reservations = bool(reservations_dao.get_dates_and_reservations_for_tour(tour_id))

	if request.method == 'POST':
		new_title = request.form.get("title")
		new_language = request.form.get("language")
		new_duration = request.form.get("duration")
		new_description = request.form.get("description")
		new_meeting_point = request.form.get("meeting_point")
		new_max_participants = request.form.get("max_participants")

		raw_stops = request.form.getlist("stops")
		stops = [stop.strip() for stop in raw_stops if stop.strip()]
		
		if len(stops) < 4:
			flash("Validation error: at least 4 stops are required.", "danger")
			return redirect(url_for('edit_tour_page', tour_id=tour_id))
		
		selected_days = request.form.getlist("days")
		schedules = []
		for day in selected_days:
			time = request.form.get(f"time_{day}")
			if time:
				schedules.append({"day_of_week": day, "start_time": time})
				
		uploaded_photos = request.files.getlist("photos")
		valid_photos = [p for p in uploaded_photos if p and p.filename]
		photo_names = []
		
		if len(valid_photos) > 0:
			if len(valid_photos) != 5:
				flash("You need to upload exactly 5 photos to edit them, or zero to leave the original ones", "danger")
				return redirect(url_for('edit_tour_page', tour_id=tour_id))
				
			for index, photo in enumerate(valid_photos):
				img = Image.open(photo)
				secs = int(datetime.now().timestamp())
				ext = photo.filename.split(".")[-1]
				img_name = f"tour_{secs}_{index}.{ext}"
				photo_names.append(f"tours/{img_name}")
				
				# Image Optimization
				max_size = (1920, 1080)
				img.thumbnail(max_size, Image.Resampling.LANCZOS)
				tours_dir = os.path.join(BASE_DIR, "static", "images", "tours")
				os.makedirs(tours_dir, exist_ok=True)
				img.save(os.path.join(tours_dir, img_name), optimize=True, quality=80)


		tours_dao.edit_tour_by_id(tour_id, new_title, new_language, new_duration, new_description, new_meeting_point, new_max_participants, stops, schedules, photo_names)
		flash("Tour updated successfully!", "success")
		return redirect(url_for('profile'))

	languages = guides_dao.get_languages_spoken_by_guide(current_user.id)
	
	scheduled_days_map = {}
	if tour and tour.get('schedules'):
		for s in tour['schedules']:
			scheduled_days_map[s['day_of_week']] = s['start_time']
			
	return render_template('create_tour.html', languages=languages, tour=tour, scheduled_days_map=scheduled_days_map, has_reservations=has_reservations)


@login_required
@app.route("/report/<int:d_id>")
def report_tour_page(d_id):
	if current_user.role != 'guide':
		return redirect(url_for('home'))

	date_info = reservations_dao.get_date_by_id(d_id)
	if not date_info:
		return redirect(url_for('profile'))

	tour = tours_dao.get_tour_by_id(date_info['t_id'])
	if not tour or tour['g_id'] != current_user.id:
		return redirect(url_for('profile'))

	# Check if date has passed
	tour_date = datetime.strptime(date_info['date'], '%Y-%m-%d %H:%M')
	if tour_date >= datetime.now():
		return redirect(url_for('profile'))

	return render_template("tour_report.html", date_info=date_info, tour=tour)

@login_required
@app.route("/submit_report/<int:d_id>", methods=["POST"])
def submit_report(d_id):
	if current_user.role != 'guide':
		return redirect(url_for('home'))

	date_info = reservations_dao.get_date_by_id(d_id)
	if not date_info:
		return redirect(url_for('profile'))

	tour = tours_dao.get_tour_by_id(date_info['t_id'])
	if not tour or tour['g_id'] != current_user.id:
		return redirect(url_for('profile'))

	# Check if date has passed
	tour_date = datetime.strptime(date_info['date'], '%Y-%m-%d %H:%M')
	if tour_date >= datetime.now():
		return redirect(url_for('profile'))

	attended_participants = request.form.get("attended_participants")
	photo_name = date_info.get("report_photo")

	report_photo = request.files.get("report_photo")
	if report_photo and report_photo.filename:
		img = Image.open(report_photo)
		secs = int(datetime.now().timestamp())
		ext = report_photo.filename.split(".")[-1]
		img_name = f"report_{d_id}_{secs}.{ext}"

		# Image Optimization
		max_size = (1920, 1080)
		img.thumbnail(max_size, Image.Resampling.LANCZOS)
		reports_dir = os.path.join(BASE_DIR, "static", "images", "reports")
		os.makedirs(reports_dir, exist_ok=True)
		img.save(os.path.join(reports_dir, img_name), optimize=True, quality=80)
		photo_name = img_name

	is_edit = bool(date_info.get("report_photo"))
	reservations_dao.update_date_report(d_id, attended_participants, photo_name)
	
	if is_edit:
		flash("Report updated successfully!", "success")
	else:
		flash("Report created successfully!", "success")

	return redirect(url_for('profile'))

#User loader function
@login_manager.user_loader
def load_user(user_id):
	try:
		role, actual_id = user_id.split("-")
		actual_id = int(actual_id)
	except ValueError:
		return None

	if role == "guide":
		db_user = guides_dao.get_guide_by_id(actual_id)
		if db_user:
			user = User(
				role="guide", 
				id=db_user["id"], 
				first_name=db_user["first_name"],
				last_name=db_user["last_name"], 
				email=db_user["email_address"],
				password=db_user["password"], 
				profile_image=db_user["profile_image"]
			)
	elif role == "participant":
		db_user = participants_dao.get_participant_by_id(actual_id)
		if db_user:
			# Participants are not supposed to have a profile picture, so it will be assigned to "None"
			user = User(
				role="participant", 
				id=db_user["id"], 
				first_name=db_user["first_name"],
				last_name=db_user["last_name"], 
				email=db_user["email_address"],
				password=db_user["password"], 
				profile_image=None
			)
	elif role == "admin":
		user = User(
			role="admin",
			id=0,
			first_name="Diego",
			last_name="Laudicina",
			email="diegol@admin.com",
			password=generate_password_hash("admin"),
			profile_image=None
		)
	else:
		user = None
	return user

#Logout function
@app.route("/logout")
@login_required
def logout():
	logout_user()
	flash("Logout successful!", "success")
	return redirect(url_for("home"))