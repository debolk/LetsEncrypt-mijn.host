"""
Import http.client to handle GET and PUT requests to mijn.host
Import json to format responses to dicts
"""
import http.client
import json
import logging
from typing import Any, Callable, Optional

from certbot import errors
from certbot.plugins import dns_common
from certbot.plugins.dns_common import CredentialsConfiguration

logger = logging.getLogger(__name__)


class MijnHostConnection:
	"""
	Handles DNS record changes for mijn.host
	Needs api_key at init
	"""

	def __init__(self, api_key):
		self.conn = None
		self.headers = {
			'Accept': 'application/json',
			'User-Agent': 'certbot-dns-mijnhost/1.1.0',
			'Content-Type': 'application/json',
			'API-Key': api_key
		}
		self.api_key = api_key

	def get_domains(self) -> list[dict[str, Any]]:
		"""
		Gets list of domains
		:return:
		"""
		logger.info("Getting list of domains")
		self.conn = http.client.HTTPSConnection("mijn.host")
		self.conn.request("GET", f"/api/v2/domains", "", self.headers)
		res = self.conn.getresponse()
		data = json.loads(res.read().decode("utf-8"))

		if data["status"] != 200:
			raise errors.PluginError(f"Failed to get domains: {data["status_description"]}")

		return data["data"]["domains"]

	def find_parent_domain(self, domain: str) -> Optional[str]:
		"""
		Finds parent domain of subdomain

		:param domain: the subdomain to get the parent from
		:return: the parent domain if it exists, None otherwise
		"""
		domains = self.get_domains()
		for dom in domains:
			if dom["domain"] in domain:
				if dom["status"] != "Active":
					raise errors.PluginError(f"Parent domain {dom["domain"]} not active")
				return dom["domain"]
		raise errors.PluginError(f"Parent domain of {domain} not present in mijn.host account associated with this API key")

	def get_dns_records(self, domain: str) -> list[Any]:
		"""
		Returns all DNS records for a given domain

		:param domain: the Domain to query
		:return: the DNS records found, None if failure
		"""
		logger.info('Getting DNS records for domain: %s', domain)
		self.conn = http.client.HTTPSConnection("mijn.host")
		self.conn.request("GET", f"/api/v2/domains/{domain}/dns", "", self.headers)
		res = self.conn.getresponse()
		data = json.loads(res.read().decode("utf-8"))
		logger.debug("Response: %s", data)
		if data["status"] != 200:
			raise errors.PluginError(f"{data["status"]}: {data["status_description"]}")

		return data["data"]["records"]

	def put_dns_records(self, domain, payload):
		"""
		Updates DNS records for a given domain with new DNS records

		:param domain: the Domain to update
		:param payload: the DNS records to update, stringified JSON
		:return: True if success
		"""
		logger.debug("Payload: %s", payload)

		self.conn = http.client.HTTPSConnection("mijn.host")
		self.conn.request("PUT", f"/api/v2/domains/{domain}/dns", payload, self.headers)
		res = self.conn.getresponse()
		data = json.loads(res.read().decode("utf-8"))

		if data["status"] != 200:
			raise errors.PluginError(f"{data['status']}: {data['status_description']}")

		return True

	def get_domain_record(self, domain, record_name):
		"""
		Searches for a DNS record for a given domain name and record type.

		:param self: the MijnHostConnection object
		:param domain: Domain name to search for
		:param record_name: Record name to search for

		:return: Record for a given domain name and record type, None if no record found
		:rtype: dict
		"""

		records = self.get_dns_records(domain)

		# search for dns record
		for record in records:

			if record["name"] == record_name:
				return record

		return None

	def update_domain_record(self, domain, record_name, record_new_value, ttl=-1):
		"""
		Updates a DNS TXT record for a given record_name or adds it.

		:param self: the MijnHostConnection object
		:param domain: Domain name to search for
		:param record_name: Record name to search for
		:param record_new_value: New value for the record
		:param ttl: Time To Live to set, default: -1 (don't change)
		:return: True if record was updated, json response otherwise
		"""
		records = self.get_dns_records(domain)

		logger.debug("Attempting to update %s to %s", record_name, record_new_value)

		if record_name[-1] != ".":
			logger.debug("Record name lacks trailing .: %s", record_name)
			record_name += "."
			logger.debug("Sanitized record name: %s", record_name)

		updated = False

		# search for dns record and update if applicable
		for record in records:

			if record["name"] == record_name:

				record["value"] = record_new_value
				if ttl > 0:
					record["ttl"] = ttl
				updated = True

		if not updated:
			record = {
				"type": "TXT",
				"name": record_name,
				"value": record_new_value,
				"ttl": ttl if ttl > 0 else 900
			}
			records.append(record)

		payload = json.dumps({"records": records})

		logger.info("Updating DNS TXT record: %s", record_name)

		return self.put_dns_records(domain, payload)

	def delete_domain_record(self, domain, record_name):
		"""
		Deletes a DNS record for a given domain name and record type.

		:param self: the MijnHostConnection object
		:param domain: the Domain name to search for
		:param record_name: the Record name to delete
		:return: True if record was deleted
		"""
		records = self.get_dns_records(domain)

		if record_name[-1] != ".":
			logger.debug("Record name lacks trailing .: %s", record_name)
			record_name += "."
			logger.debug("Sanitized record name: %s", record_name)

		# search for dns record and update if applicable
		for record in records:

			if record["name"] == record_name:
				records.remove(record)

		payload = json.dumps({"records": records})

		logger.info("Deleting DNS TXT record: %s", record_name)
		return self.put_dns_records(domain, payload)


class Authenticator(dns_common.DNSAuthenticator):
	"""mijn.host Authenticator"""

	description = "Obtain certificates using a DNS TXT record specifically for mijn.host"

	def __init__(self, *args: Any, **kwargs: Any) -> None:
		super().__init__(*args, **kwargs)
		logger.info("Initializing mijn.host authenticator")
		self.connection = None
		self.api_key = None
		self.credentials: Optional[CredentialsConfiguration] = None

	@classmethod
	def add_parser_arguments(cls, add: Callable[..., None],
							default_propagation_seconds: int = 20) -> None:
		super().add_parser_arguments(add, default_propagation_seconds)
		add('credentials', help='Mijn.host credentials INI file')

	def more_info(self) -> str:
		return ("This plugin configures a DNS TXT record in mijn.host " +
				"to respond to a dns-01 challenge, using their API.")

	@staticmethod
	def _validate_credentials(credentials: CredentialsConfiguration) -> None:
		key = credentials.conf('api-key')
		if not key:
			raise errors.PluginError(f"No API key configured in {credentials.confobj.filename}")

	def _setup_credentials(self) -> None:
		self.credentials = self._configure_credentials(
			"credentials",
			"Mijn.host credentials INI file",
			None,
			self._validate_credentials
		)
		self.api_key = self.credentials.conf('api_key')

		logger.debug("API key: %s", self.api_key)
		if self.api_key is not None:
			self.connection = MijnHostConnection(self.api_key)
		else:
			raise errors.PluginError("mijn.host API key not provided")

	def _perform(self, domain: str, validation_name: str, validation: str) -> None:
		self._get_connection().update_domain_record(domain, validation_name, validation, 900)

	def _cleanup(self, domain: str, validation_name: str, validation: str) -> None:
		self._get_connection().delete_domain_record(domain, validation_name)

	def _get_connection(self) -> "MijnHostConnection":
		if self.connection is None:
			raise errors.Error("Credentials are not configured.")
		return self.connection
