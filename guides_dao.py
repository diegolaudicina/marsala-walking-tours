import sqlite3, os

db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "mwt.db")


def get_guide_from_email(p_email):
	query = "SELECT * FROM GUIDES where email_address = ?"
	
	conn = sqlite3.connect(db_path)
	conn.row_factory = sqlite3.Row
	cursor = conn.cursor()
	
	cursor.execute(query, (p_email,))
	
	guide = cursor.fetchone()
	
	conn.commit()
	cursor.close()
	conn.close()
	
	return guide

def new_guide(p_first, p_last, p_email, p_password, p_profile_image, languages=None):
	query = ("INSERT INTO GUIDES (first_name, last_name, email_address, password, profile_image) VALUES (?,?,?,?,?)")
	lang_query = "INSERT INTO SPEAKS (g_id, language) VALUES (?, ?)"
	
	conn = sqlite3.connect(db_path)
	cursor = conn.cursor()
	
	try:
		cursor.execute(query, (p_first, p_last, p_email, p_password, p_profile_image,))
		guide_id = cursor.lastrowid
		
		if languages:
			for lang in languages:
				cursor.execute(lang_query, (guide_id, lang))
		
		conn.commit()
		return guide_id

	except sqlite3.Error as err:
		conn.rollback()
		raise err

	finally:
		cursor.close()
		conn.close()

def get_guide_by_id(guide_id):
	query = "SELECT * FROM GUIDES WHERE id = ?"
	
	conn = sqlite3.connect(db_path)
	conn.row_factory = sqlite3.Row
	cursor = conn.cursor()
	
	cursor.execute(query, (guide_id,))
	
	guide = cursor.fetchone()
	
	conn.commit()
	cursor.close()
	conn.close()
	
	return guide

def get_all_languages():
	query = "SELECT * FROM LANGUAGES"
	
	conn = sqlite3.connect(db_path)
	conn.row_factory = sqlite3.Row
	cursor = conn.cursor()
	
	cursor.execute(query)
	languages = cursor.fetchall()
	
	conn.commit()
	cursor.close()
	conn.close()
	
	return languages

def add_guide_languages(guide_id, languages):
	query = "INSERT INTO SPEAKS (g_id, language) VALUES (?, ?)"
	
	conn = sqlite3.connect(db_path)
	cursor = conn.cursor()
	
	try:
		for lang in languages:
			cursor.execute(query, (guide_id, lang))
		conn.commit()
	except sqlite3.Error as err:
		conn.rollback()
		raise err
	finally:
		cursor.close()
		conn.close()
 
def get_languages_spoken_by_guide(guide_id):
	query = "SELECT language FROM SPEAKS WHERE g_id = ?"
	
	conn = sqlite3.connect(db_path)
	conn.row_factory = sqlite3.Row
	cursor = conn.cursor()
	
	cursor.execute(query, (guide_id,))
	languages = cursor.fetchall()
	
	conn.commit()
	cursor.close()
	conn.close()
	
	return languages