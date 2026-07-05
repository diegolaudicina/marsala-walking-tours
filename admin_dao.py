import sqlite3, os

db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "mwt.db")

def get_admin_dashboard_stats():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    #number of guide accounts
    cursor.execute("SELECT COUNT(*) FROM GUIDES")
    total_guides = cursor.fetchone()[0]
    
    #number of participant accounts
    cursor.execute("SELECT COUNT(*) FROM PARTICIPANTS")
    total_participants = cursor.fetchone()[0]
    
    #number of tours created
    cursor.execute("SELECT COUNT(*) FROM TOURS")
    total_tours = cursor.fetchone()[0]
    
    #number of total reservations
    cursor.execute("SELECT COUNT(*) FROM RESERVATIONS")
    total_reservations = cursor.fetchone()[0]
    
    #number of reservations per tour language
    cursor.execute('''
        SELECT T.language, COUNT(R.id) as count
        FROM RESERVATIONS R
        JOIN DATES D ON R.d_id = D.id
        JOIN TOURS T ON D.t_id = T.id
        GROUP BY T.language
    ''')
    reservations_per_language = [dict(row) for row in cursor.fetchall()]
    
    #retrieving guides
    cursor.execute("SELECT * FROM GUIDES")
    guides_rows = cursor.fetchall()

    guides = []
    for g_row in guides_rows:
        guide = dict(g_row)
        
        cursor.execute("SELECT language FROM SPEAKS WHERE g_id = ?", (guide['id'],))
        guide['languages'] = [row['language'] for row in cursor.fetchall()]
        
        cursor.execute("SELECT title, language, duration, description, meeting_point, max_participants FROM TOURS WHERE g_id = ?", (guide['id'],))
        guide['tours'] = [dict(row) for row in cursor.fetchall()]
        
        guides.append(guide)
        
    #retrieving post tour reports
    cursor.execute('''
        SELECT D.id, D.date, D.actual_participants, D.report_photo, T.title, G.first_name, G.last_name
        FROM DATES D
        JOIN TOURS T ON D.t_id = T.id
        JOIN GUIDES G ON T.g_id = G.id
        WHERE D.report_photo IS NOT NULL AND D.report_photo != ''
        ORDER BY D.date DESC
    ''')
    reports = [dict(row) for row in cursor.fetchall()]
        
    conn.close()
    
    return {
        'total_guides': total_guides,
        'total_participants': total_participants,
        'total_tours': total_tours,
        'total_reservations': total_reservations,
        'reservations_per_language': reservations_per_language,
        'guides': guides,
        'reports': reports
    }
