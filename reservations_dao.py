import sqlite3, os
from datetime import datetime, timedelta

db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "mwt.db")

def new_reservation(tour_id, p_id, booking_date, extra_participants):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    success = False
    
    try:
        # Retrieving tour max capacity and duration from TOURS table
        cursor.execute('SELECT max_participants, duration FROM TOURS WHERE id = ?', (tour_id,))
        tour_row = cursor.fetchone()
        if not tour_row:
            return False
        max_participants = tour_row[0]
        new_tour_duration = tour_row[1]
        
        # Checking time overlaps
        new_start = datetime.strptime(booking_date, '%Y-%m-%d %H:%M')
        new_end = new_start + timedelta(minutes=new_tour_duration)
        
        cursor.execute('''
            SELECT D.date, T.duration 
            FROM RESERVATIONS R
            JOIN DATES D ON R.d_id = D.id
            JOIN TOURS T ON D.t_id = T.id
            WHERE R.p_id = ?
        ''', (p_id,))
        
        for row in cursor.fetchall():
            existing_start = datetime.strptime(row[0], '%Y-%m-%d %H:%M')
            existing_end = existing_start + timedelta(minutes=row[1])
            
            # Overlap condition
            if new_start < existing_end and existing_start < new_end:
                raise ValueError("Overlap: You already have a tour scheduled for this time.")
        
        total_new_participants = 1 + len(extra_participants)

        # Checking DATES table to see whether the selected date already exists
        cursor.execute('SELECT id, actual_participants FROM DATES WHERE t_id = ? AND date = ?', (tour_id, booking_date))
        date_row = cursor.fetchone()
        
        if date_row:
            d_id = date_row[0]
            current_participants = date_row[1]
            
            # Checking slots availability (added security)
            if current_participants + total_new_participants > max_participants:
                raise ValueError("Not enough spots available")
                
            # Updating the participants in DATES
            cursor.execute('UPDATE DATES SET actual_participants = actual_participants + ? WHERE id = ?', 
                           (total_new_participants, d_id))
        else:
            # The chosen date is not on the db, creating one
            if total_new_participants > max_participants:
                 raise ValueError("Not enough spots available")
                 
            # report_photo is initially NULL
            cursor.execute('INSERT INTO DATES (date, actual_participants, report_photo, t_id) VALUES (?, ?, NULL, ?)', 
                           (booking_date, total_new_participants, tour_id))
            d_id = cursor.lastrowid
            
        # Inserting the reservation in RESERVATIONS table
        cursor.execute('INSERT INTO RESERVATIONS (d_id, p_id) VALUES (?, ?)', (d_id, p_id))
        r_id = cursor.lastrowid
        
        # Inserting extra participants name if there are any
        if extra_participants:
            for person in extra_participants:
                extra_name_full = f"{person['first_name']} {person['last_name']}"
                cursor.execute('INSERT INTO EXTRA_NAMES (extra_name, r_id) VALUES (?, ?)', (extra_name_full, r_id))

        conn.commit()
        success = True
        
    except Exception as err:
        # In the event of an error, rollback
        conn.rollback()
        print(f"Error while booking tour: {err}")
        
    finally:
        conn.close()
        
    return success

def get_user_booked_dates_for_tour(p_id, t_id):
    #Returns a list of dates (format YYYY-MM-DD HH:MM) that are already booked for the specific tour
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT D.date 
        FROM RESERVATIONS R
        JOIN DATES D ON R.d_id = D.id
        WHERE R.p_id = ? AND D.t_id = ?
    ''', (p_id, t_id))
    
    dates = [row[0] for row in cursor.fetchall()]
    conn.close()
    return dates

def get_user_schedule(p_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT D.date, T.duration, R.id 
        FROM RESERVATIONS R
        JOIN DATES D ON R.d_id = D.id
        JOIN TOURS T ON D.t_id = T.id
        WHERE R.p_id = ?
    ''', (p_id,))
    
    schedule = []
    for row in cursor.fetchall():
        start = datetime.strptime(row[0], '%Y-%m-%d %H:%M')
        end = start + timedelta(minutes=row[1])
        schedule.append({'start': start, 'end': end, 'r_id': row[2]})
        
    conn.close()
    return schedule

def get_reservations_for_participant(p_id):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = """ SELECT r.id AS reservation_id,
                t.id AS tour_id,
                t.title AS tour_title,
                t.meeting_point,
                d.date AS raw_date,
                (1 + COUNT(e.id)) AS total_people,
                GROUP_CONCAT(e.extra_name, ', ') AS extra_names_list
                FROM reservations r
                JOIN DATES d ON r.d_id = d.id
                JOIN TOURS t ON d.t_id = t.id
                LEFT JOIN EXTRA_NAMES e ON e.r_id = r.id
                WHERE r.p_id = ?
                GROUP BY r.id
            """

    cursor.execute(query, (p_id, ))
    reservations = cursor.fetchall()
    
    res_list = []
    now = datetime.now()
    for row in reservations:
        r = dict(row)
        tour_date = datetime.strptime(r['raw_date'], '%Y-%m-%d %H:%M')
        r['can_cancel'] = (tour_date - timedelta(hours=24)) > now
        r['date'] = tour_date.strftime('%Y-%m-%d')
        r['start_time'] = tour_date.strftime('%H:%M')
        res_list.append(r)
        
    return res_list

def get_reservation_by_id(r_id):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('''
        SELECT r.id, r.p_id, r.d_id, d.date, d.t_id as tour_id 
        FROM RESERVATIONS r 
        JOIN DATES d ON r.d_id = d.id 
        WHERE r.id = ?
    ''', (r_id,))
    res = cursor.fetchone()
    conn.close()
    return dict(res) if res else None

def get_extra_participants_for_reservation(r_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT extra_name FROM EXTRA_NAMES WHERE r_id = ?', (r_id,))
    names = []
    for row in cursor.fetchall():
        parts = row[0].split(' ', 1)
        first = parts[0]
        last = parts[1] if len(parts) > 1 else ''
        names.append({'first_name': first, 'last_name': last})
    conn.close()
    return names

def update_reservation(r_id, p_id, tour_id, old_d_id, new_booking_date, new_extra_participants):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    success = False
    try:
        # Get max capacity and duration
        cursor.execute('SELECT max_participants, duration FROM TOURS WHERE id = ?', (tour_id,))
        tour_row = cursor.fetchone()
        max_participants = tour_row[0]
        new_tour_duration = tour_row[1]

        # Check time overlaps
        new_start = datetime.strptime(new_booking_date, '%Y-%m-%d %H:%M')
        new_end = new_start + timedelta(minutes=new_tour_duration)
        
        cursor.execute('''
            SELECT D.date, T.duration, R.id 
            FROM RESERVATIONS R
            JOIN DATES D ON R.d_id = D.id
            JOIN TOURS T ON D.t_id = T.id
            WHERE R.p_id = ?
        ''', (p_id,))
        
        for row in cursor.fetchall():
            if row[2] == r_id:
                continue # Skip current reservation
            existing_start = datetime.strptime(row[0], '%Y-%m-%d %H:%M')
            existing_end = existing_start + timedelta(minutes=row[1])
            if new_start < existing_end and existing_start < new_end:
                raise ValueError("Overlap: You already have a tour scheduled for this time.")

        # Participants count
        cursor.execute('SELECT COUNT(*) FROM EXTRA_NAMES WHERE r_id = ?', (r_id,))
        old_extra_count = cursor.fetchone()[0]
        old_total_participants = 1 + old_extra_count
        new_total_participants = 1 + len(new_extra_participants)

        # Get new_d_id or create date if doesn't exist
        cursor.execute('SELECT id, actual_participants FROM DATES WHERE t_id = ? AND date = ?', (tour_id, new_booking_date))
        date_row = cursor.fetchone()

        if date_row:
            new_d_id = date_row[0]
            current_participants = date_row[1]
        else:
            new_d_id = None
            current_participants = 0

        # Check spots
        if old_d_id == new_d_id:
            if current_participants - old_total_participants + new_total_participants > max_participants:
                 raise ValueError("Not enough spots available")
            cursor.execute('UPDATE DATES SET actual_participants = actual_participants - ? + ? WHERE id = ?', 
                           (old_total_participants, new_total_participants, old_d_id))
        else:
            if current_participants + new_total_participants > max_participants:
                 raise ValueError("Not enough spots available")
            
            cursor.execute('UPDATE DATES SET actual_participants = actual_participants - ? WHERE id = ?', 
                           (old_total_participants, old_d_id))
                           
            if new_d_id:
                cursor.execute('UPDATE DATES SET actual_participants = actual_participants + ? WHERE id = ?', 
                               (new_total_participants, new_d_id))
            else:
                cursor.execute('INSERT INTO DATES (date, actual_participants, report_photo, t_id) VALUES (?, ?, NULL, ?)', 
                               (new_booking_date, new_total_participants, tour_id))
                new_d_id = cursor.lastrowid
                
            cursor.execute('UPDATE RESERVATIONS SET d_id = ? WHERE id = ?', (new_d_id, r_id))

        # Update extra names
        cursor.execute('DELETE FROM EXTRA_NAMES WHERE r_id = ?', (r_id,))
        for person in new_extra_participants:
            extra_name_full = f"{person['first_name']} {person['last_name']}"
            cursor.execute('INSERT INTO EXTRA_NAMES (extra_name, r_id) VALUES (?, ?)', (extra_name_full, r_id))
            
        conn.commit()
        success = True
    except sqlite3.Error as err:
        conn.rollback()
        print(f"Error while updating booking: {err}")
    finally:
        conn.close()
        
    return success

def delete_reservation(r_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    success = False
    try:
        # Get reservation details
        cursor.execute('''SELECT d.id, 1 + (SELECT COUNT(*) FROM EXTRA_NAMES WHERE r_id = ?) 
                          FROM RESERVATIONS r JOIN DATES d ON r.d_id = d.id 
                          WHERE r.id = ?''', (r_id, r_id))
        row = cursor.fetchone()
        if not row:
            return False
            
        d_id = row[0]
        total_participants = row[1]
        
        # Delete extra names
        cursor.execute('DELETE FROM EXTRA_NAMES WHERE r_id = ?', (r_id,))
        # Delete reservation
        cursor.execute('DELETE FROM RESERVATIONS WHERE id = ?', (r_id,))
        # Update participants in DATES
        cursor.execute('UPDATE DATES SET actual_participants = actual_participants - ? WHERE id = ?', (total_participants, d_id))
        
        conn.commit()
        success = True
    except sqlite3.Error as err:
        conn.rollback()
        print(f"Error while deleting reservation: {err}")
    finally:
        conn.close()
    return success

def get_dates_and_reservations_for_tour(t_id):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # First get all dates that have reservations for this tour
    cursor.execute('''
        SELECT id, date, actual_participants, report_photo 
        FROM DATES 
        WHERE t_id = ? AND actual_participants > 0
        ORDER BY date ASC
    ''', (t_id,))
    
    dates_rows = cursor.fetchall()
    
    dates = []
    for d_row in dates_rows:
        tour_date = datetime.strptime(d_row['date'], '%Y-%m-%d %H:%M')
        date_dict = {
            'id': d_row['id'],
            'date': d_row['date'],
            'actual_participants': d_row['actual_participants'],
            'report_photo': d_row['report_photo'],
            'has_passed': tour_date < datetime.now(),
            'reservations': []
        }
        
        # Get reservations for this date
        cursor.execute('''
            SELECT r.id, p.first_name, p.last_name 
            FROM RESERVATIONS r
            JOIN PARTICIPANTS p ON r.p_id = p.id
            WHERE r.d_id = ?
        ''', (date_dict['id'],))
        
        res_rows = cursor.fetchall()
        for r_row in res_rows:
            res_dict = {
                'id': r_row['id'],
                'primary_participant': f"{r_row['first_name']} {r_row['last_name']}",
                'extra_participants': []
            }
            
            # Get extra participants
            cursor.execute('SELECT extra_name FROM EXTRA_NAMES WHERE r_id = ?', (res_dict['id'],))
            extra_rows = cursor.fetchall()
            for e_row in extra_rows:
                res_dict['extra_participants'].append(e_row['extra_name'])
                
            date_dict['reservations'].append(res_dict)
            
        dates.append(date_dict)
        
    conn.close()
    return dates

def get_date_by_id(d_id):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM DATES WHERE id = ?', (d_id,))
    date = cursor.fetchone()
    conn.close()
    return dict(date) if date else None

def update_date_report(d_id, attended_participants, photo_name):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    success = False
    try:
        cursor.execute('UPDATE DATES SET actual_participants = ?, report_photo = ? WHERE id = ?',
                       (attended_participants, photo_name, d_id))
        conn.commit()
        success = True
    except sqlite3.Error as err:
        conn.rollback()
        print(f"Error while updating report: {err}")
    finally:
        conn.close()
    return success