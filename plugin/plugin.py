"""
Import http.client to handle GET and PUT requests to mijn.host
Import json to format responses to dicts
"""
import http.client
import json
from typing import Iterable, Type, List, Optional, Any, Callable

from acme.challenges import Challenge, ChallengeResponse
from certbot import interfaces
from certbot.achallenges import AnnotatedChallenge
from certbot.plugins import dns_common
from certbot.plugins.dns_common import CredentialsConfiguration


class MijnHostConnection:
	"""
	Handles DNS record changes for mijn.host
	Needs api_key at init
	"""

	def __init__(self, api_key):
		self.conn = http.client.HTTPSConnection("mijn.host")
		self.headers = {
			'Accept': 'application/json',
			'User-Agent': 'my-application/1.0.0',
			'Content-Type': 'application/json',
			'API-Key': api_key
		}
		self.api_key = api_key

	def get_domain_record(self, domain, record_name):
		"""
		Searches for a DNS record for a given domain name and record type.

		:param self: the MijnHostConnection object
		:param domain: Domain name to search for
		:param record_name: Record name to search for

		:return: Record for a given domain name and record type, None if no record found
		:rtype: dict
		"""

		self.conn.request("GET", f"/api/v2/domains/{domain}/dns", "", self.headers)
		res = self.conn.getresponse()
		data = json.loads(res.read().decode("utf-8"))["data"]

		# search for dns record
		for record in data["records"]:

			if record["name"] == record_name:
				return record
		return None

	def update_domain_record(self, domain, record_name, record_type, record_new_value, ttl=-1):
		"""
		Updates a DNS record for a given domain name and record type.

		:param self: the MijnHostConnection object
		:param domain: Domain name to search for
		:param record_name: Record name to search for
		:param record_type: Record type for the Record
		:param record_new_value: Record value to set
		:param ttl: Time To Live to set, default: -1 (don't change)
		:return: True if record was updated, json response otherwise
		"""
		self.conn.request("GET", f"/api/v2/domains/{domain}/dns", "", self.headers)
		res = self.conn.getresponse()
		records = json.loads(res.read().decode("utf-8"))["data"]["records"]

		updated = False
		# search for dns record and update if applicable
		for record in records:

			if record["name"] == record_name:

				record["value"] = record_new_value
				if (ttl > 0):
					record["ttl"] = ttl
				updated = True

		if not updated:
			record = {
				"type": record_type,
				"name": record_name,
				"value": record_new_value,
				"ttl": ttl if ttl > 0 else 900
			}
			records.append(record)

		payload = json.dumps({"records": records})
		print(payload)
		self.conn.request("PUT", f"/api/v2/domains/{domain}/dns", payload, self.headers)
		response = self.conn.getresponse().read().decode

		return True if response["status"] == 200 else response


class Authenticator(dns_common.DNSAuthenticator):
	"""mijn.host Authenticator"""

	description = "Obtain certificates using a DNS TXT record specifically for mijn.host"

	def __init__(self, *args: Any, **kwargs: Any) -> None:
		super().__init__(*args, **kwargs)
		self.credentials: Optional[CredentialsConfiguration] = None
		self.connection: MijnHostConnection = MijnHostConnection(kwargs.get('api_key', None))

	@classmethod
	def add_parser_arguments(cls, add: Callable[..., None],
							default_propagation_seconds: int = 10) -> None:
		super().add_parser_arguments(add, default_propagation_seconds)
		add('api_key', help='Mijn.host API key')

	def more_info(self) -> str:
		return ("This plugin configures a DNS TXT record in mijn.host to respond to a "
				"dns-01 challenge, using their API.")

	def _setup_credentials(self) -> None:
		self.credentials = self._configure_credentials(

		)

	def _perform(self, domain: str, validation_name: str, validation: str) -> None:
		pass

	def _cleanup(self, domain: str, validation_name: str, validation: str) -> None:
		pass
