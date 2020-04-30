from api.auth.data_encryptor import DataEncryptor
from api import utils
from api.models import event as models

data_encryptor = DataEncryptor


class UserAuthFail(Exception):
	pass


class Authenticator:
	inst = None

	def __init__(self):
		if Authenticator.inst:
			raise Exception("Use Authenticator.get_instance() method")

		self.auth_user = None

	@classmethod
	def get_instance(cls):
		if cls.inst is None:
			cls.inst = Authenticator()
		return cls.inst

	def authenticate(self, request):
		token = ""
		if 'Authorization' in request.headers and request.headers['Authorization'] is not None:
			token = self.strip_bearer(request.headers['Authorization'])
		claims = data_encryptor.decrypt(token, key=utils.ENCRYPTION_KEY)
		if claims:
			user = models.User.get_user(claims['id'])
			user_login_session = user.get_login_session()
			if not user_login_session or user_login_session.session_token != token:
				raise UserAuthFail()
			self.set_auth_user(user)
			return True
		# raise UserAuthFail()

	def set_auth_user(self, auth_user):
		self.auth_user = auth_user

	def get_auth_user(self):
		return self.auth_user

	@staticmethod
	def strip_bearer(token):
		bearer = "Bearer"
		return token[len(bearer):].strip()