from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, role, id, first_name, last_name, email, password, profile_image):
        self.id = id
        self.role = role
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.password = password
        self.profile_image = profile_image

    def get_id(self):
        return f"{self.role}-{self.id}"
