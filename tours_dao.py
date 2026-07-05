import sqlite3, os
from datetime import datetime, timedelta

db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "mwt.db")

def new_tour(tour):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    #Boolean variable to track success (or failure) of db insertion
    success = False
    
    #error handling block
    try:
        # Insertion on main table TOURS
        tours_query = "INSERT INTO TOURS(title, language, duration, description, meeting_point, max_participants, g_id) VALUES (?, ?, ?, ?, ?, ?, ?)"
        
        cursor.execute(tours_query, (
            tour.get('title'), 
            tour.get('language'), 
            tour.get('duration'), 
            tour.get('description'), 
            tour.get('meeting_point'), 
            tour.get('max_participants'), 
            tour.get('g_id')
        ))
        
        # lastrowid to retrieve the id of the newly created tour
        tour_id = cursor.lastrowid
        
        # Insertion on SCHEDULES table
        if 'schedules' in tour:
            for schedule in tour['schedules']:
                schedule_query = "INSERT INTO SCHEDULE(day_of_week, start_time, t_id) VALUES (?, ?, ?)"
                cursor.execute(schedule_query,
                               (schedule.get('day_of_week'), schedule.get('start_time'), tour_id))
                               
        # Insertion on STOPS table
        if 'stops' in tour:
            for stop in tour['stops']:
                stops_query = "INSERT INTO STOPS(stop, t_id) VALUES (?, ?)"
                cursor.execute(stops_query, (stop, tour_id))
                               
        # Insertion on PHOTOS table
        if 'photos' in tour:
            for photo in tour['photos']:
                photos_query = "INSERT INTO PHOTOS(photo, t_id) VALUES (?, ?)"
                cursor.execute(photos_query, (photo, tour_id))
                               
        # Commit changes
        conn.commit()
        #No errors so far -> everything correctly inserted
        success = True
        
    except sqlite3.Error as err:
        # In case of error, rollback of all changes (to avoid inconsistent data)
        conn.rollback()
        print(f"Error while adding tour to database: {err}")
        
    finally:
        # in every case, error or success
        conn.close()

    return success

def get_all_tours():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Selecting all tours and a random photo as "cover_photo"
    query = "SELECT T.*, (SELECT photo FROM PHOTOS WHERE t_id = T.id ORDER BY RANDOM() LIMIT 1) as cover_photo FROM TOURS T"
    cursor.execute(query)
    
    # Converting the results to dictionary for easy management in Jinja
    tours = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return tours

# Lazy instantiation approach for translating the schedule to actual dates
def get_upcoming_tour_dates(tour_id, max_participants, limit=20):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Retrieving tour weekly schedule
    cursor.execute('SELECT day_of_week, start_time FROM SCHEDULE WHERE t_id = ?', (tour_id,))
    schedules = cursor.fetchall()
    
    #If the schedule is empty
    if not schedules:
        conn.close()
        return []
        
    # Quick mapping for the days-of-the-week
    days_map = {
        'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 
        'Thursday': 3, 'Friday': 4, 'Saturday': 5, 'Sunday': 6
    }
    
    # Calculating occurrences (20 days from now at least)
    today = datetime.now().date()
    upcoming_datetimes = []
    
    for i in range(20):
        current_date = today + timedelta(days=i)
        for sched in schedules:
            if current_date.weekday() == days_map.get(sched['day_of_week']):
                # date string format: YYYY-MM-DD HH:MM
                date_str = f"{current_date.strftime('%Y-%m-%d')} {sched['start_time']}"
                
                dt_obj = datetime.strptime(date_str, '%Y-%m-%d %H:%M')
                # Excluding already elapsed dates
                if dt_obj > datetime.now():
                    upcoming_datetimes.append(dt_obj)
                
    # Chronological ordering and sorting until limit
    upcoming_datetimes.sort()
    upcoming_datetimes = upcoming_datetimes[:limit]
    
    # Reconversion to string for db querying
    date_strings = [dt.strftime('%Y-%m-%d %H:%M') for dt in upcoming_datetimes]
    
    if not date_strings:
        conn.close()
        return []
        
    # Querying DATES table to see how many people already reserved a spot in these specific dates
    placeholders = ','.join(['?'] * len(date_strings))
    query = f"""
        SELECT date, actual_participants 
        FROM DATES 
        WHERE t_id = ? AND date IN ({placeholders})
    """
    cursor.execute(query, [tour_id] + date_strings)
    
    # Quick dictionary { "2026-06-24 10:00": 3 }
    booked_dates = {row['date']: row['actual_participants'] for row in cursor.fetchall()}
    
    conn.close()
    
    # Final result assembly
    result = []
    for date_str in date_strings:
        actual_participants = booked_dates.get(date_str, 0) #If non existent in DB, 0 participants
        available_spots = max_participants - actual_participants
        
        result.append({
            "full_date": date_str,  # eg: "2026-06-24 10:00"
            "display_date": datetime.strptime(date_str, '%Y-%m-%d %H:%M').strftime('%d/%m/%Y %H:%M'), # Eg: "24/06/2026 10:00" for visualization
            "available_spots": available_spots,
            "is_full": available_spots <= 0
        })
        
    return result

def get_upcoming_tour_dates_with_current(tour_id, max_participants, current_date, current_reservation_spots, limit=20):
    
    dates = get_upcoming_tour_dates(tour_id, max_participants, limit)
    
    found = False
    for d in dates:
        if d['full_date'] == current_date:
            found = True
            # Adding back the spots held by the current reservation
            # so the JS logic can allow adding up to the total available spots
            d['available_spots'] = d['available_spots'] + current_reservation_spots
            d['is_full'] = False
            break
            
    if not found:
        from datetime import datetime
        dates.append({
            "full_date": current_date,
            "display_date": datetime.strptime(current_date, '%Y-%m-%d %H:%M').strftime('%d/%m/%Y %H:%M'),
            "available_spots": current_reservation_spots,
            "is_full": False
        })
        # Chronological order
        dates.sort(key=lambda x: x['full_date'])
        
    return dates

def get_tour_by_id(tour_id):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get main tour details and guide info
    query = """
        SELECT T.*, G.first_name as guide_first, G.last_name as guide_last, G.profile_image as guide_profile_image
        FROM TOURS T
        JOIN GUIDES G ON T.g_id = G.id
        WHERE T.id = ?
    """
    cursor.execute(query, (tour_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return None
        
    tour = dict(row)
    
    # Get photos
    cursor.execute('SELECT photo FROM PHOTOS WHERE t_id = ?', (tour_id,))
    tour['photos'] = [r['photo'] for r in cursor.fetchall()]
    
    # Get stops
    cursor.execute('SELECT stop FROM STOPS WHERE t_id = ?', (tour_id,))
    tour['stops'] = [r['stop'] for r in cursor.fetchall()]
    
    # Get schedules
    cursor.execute('SELECT day_of_week, start_time FROM SCHEDULE WHERE t_id = ?', (tour_id,))
    tour['schedules'] = [dict(r) for r in cursor.fetchall()]
    
    conn.close()
    return tour

def get_all_tours_for_guide(g_id):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = "SELECT * FROM TOURS WHERE g_id = ?"

    cursor.execute(query, (g_id, ))
    tours = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return tours

def edit_tour_by_id(t_id, title, language, duration, description, meeting_point, max_participants, stops, schedules, photo_names):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    success = False

    try:
        # Check if tour has any reservations
        cursor.execute("SELECT COUNT(*) FROM DATES WHERE t_id = ? AND actual_participants > 0", (t_id,))
        has_reservations = cursor.fetchone()[0] > 0

        if has_reservations:
            query = """UPDATE TOURS
                SET title = ?,
                    description = ?
                WHERE id = ?"""
            cursor.execute(query, (title, description, t_id))
        else:
            query = """UPDATE TOURS
                SET title = ?,
                    language = ?,
                    duration = ?,
                    description = ?,
                    meeting_point = ?,
                    max_participants = ?
                WHERE id = ?"""
            cursor.execute(query, (title, language, duration, description, meeting_point, max_participants, t_id))
            
            # Update SCHEDULES only if no reservations
            cursor.execute("DELETE FROM SCHEDULE WHERE t_id = ?", (t_id,))
            for schedule in schedules:
                cursor.execute("INSERT INTO SCHEDULE(day_of_week, start_time, t_id) VALUES (?, ?, ?)", 
                               (schedule.get('day_of_week'), schedule.get('start_time'), t_id))
    
        # Update STOPS
        cursor.execute("DELETE FROM STOPS WHERE t_id = ?", (t_id,))
        for stop in stops:
            cursor.execute("INSERT INTO STOPS(stop, t_id) VALUES (?, ?)", (stop, t_id))
                           
        # Update PHOTOS if new photos are provided
        if photo_names:
            cursor.execute("DELETE FROM PHOTOS WHERE t_id = ?", (t_id,))
            for photo in photo_names:
                cursor.execute("INSERT INTO PHOTOS(photo, t_id) VALUES (?, ?)", (photo, t_id))

        conn.commit()
        success = True

    except sqlite3.Error as err:
        conn.rollback()
        print(f"Error while updating tour in database: {err}")

    finally:
        conn.close()

    return success