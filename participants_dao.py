import sqlite3, os

db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "mwt.db")

def get_participant_from_email(p_email):
	query = "SELECT * FROM PARTICIPANTS where email_address = ?"
	
	conn = sqlite3.connect(db_path)
	conn.row_factory = sqlite3.Row
	cursor = conn.cursor()
	
	cursor.execute(query, (p_email,))
	
	participant = cursor.fetchone()
	
	conn.commit()
	cursor.close()
	conn.close()
	
	return participant

def new_participant(p_first, p_last, p_email, p_password):
	query = ("INSERT INTO PARTICIPANTS (first_name, last_name, email_address, password) VALUES (?,?,?,?)")
	
	conn = sqlite3.connect(db_path)
	cursor = conn.cursor()
	
	try:
		cursor.execute(query, (p_first, p_last, p_email, p_password,))
		conn.commit()
	except sqlite3.Error as err:
		conn.rollback()
		raise err
	finally:
		cursor.close()
		conn.close()

def get_participant_by_id(participant_id):
	query = "SELECT * FROM PARTICIPANTS WHERE id = ?"
	
	conn = sqlite3.connect(db_path)
	conn.row_factory = sqlite3.Row
	cursor = conn.cursor()
	
	cursor.execute(query, (participant_id,))
	
	participant = cursor.fetchone()
	
	conn.commit()
	cursor.close()
	conn.close()
	
	return participant