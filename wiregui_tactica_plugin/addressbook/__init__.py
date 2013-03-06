from collections import namedtuple
#import logging

from sqlalchemy import Table
from sqlalchemy import MetaData
from sqlalchemy import and_, asc

from wiregui_server.log_ import loggerFactory
from wiregui_server.addressbook import AddressBookPluginBase

from wiregui_tactica_plugin.database import engine, dbsession

#log = logging.getLogger(__name__)

class PublicAddressBook(AddressBookPluginBase):
	""" Public addressbook provided from tactica module. """
	def __init__(self):
		super(PublicAddressBook, self).__init__()
		#log.debug('Tactica plugin was properly loaded.')
		self.meta = MetaData()
		self.contacts = Table('contactos', self.meta, autoload=True, autoload_with=engine)
		self.telefonos = Table('telefonos', self.meta, autoload=True, autoload_with=engine)
		self.emails = Table('direccionescorreo', self.meta, autoload=True, autoload_with=engine)
		self.empresas = Table('empresas', self.meta, autoload=True, autoload_with=engine)
		self._ids_empresas = {}
		self._last_id = 0
		self._ids_contactos = {}

	@dbsession
	def public(self,dbsession):
		''' Return proper addressbook format (json) '''
		entries = []
		for c in dbsession.query(self.contacts, self.empresas).filter(
										and_(self.empresas.columns.Calificacion!='DIRECTORIO',
											self.empresas.columns.IDEmpresa == self.contacts.columns.IDEmpresa)).order_by(
																							asc(self.empresas.columns.Empresa), asc(self.contacts.columns.Apellido)).all():
			id_empresa = self._ids_empresas.get(c.IDEmpresa)
			if id_empresa is None:
				self._last_id = self._last_id +1
				id_empresa = self._last_id
				self._ids_empresas[c.IDEmpresa] = self._last_id

			id_contacto = self._ids_contactos.get(c.IDContacto)
			if id_contacto is None:
				self._last_id = self._last_id +1
				id_contacto = self._last_id
				self._ids_contactos[c.IDContacto] = self._last_id

			empresa_exists = False
			for entry in entries:
				if entry.get('type') == 'group' and entry.get('id') == id_empresa:
					empresa_exists = True
					entry['children'].append({'type': 'contact', 'name': '%s %s' % (c.Nombre, c.Apellido), 'id': id_contacto})

			if not empresa_exists:
				entries.append({'name': c.Empresa, 'id': id_empresa, 'type': 'group', 'children': [{'type': 'contact', 'name': '%s %s' % (c.Nombre, c.Apellido), 'id': id_contacto}]})

		return entries
		
	@dbsession
	def getNode(self, id, dbsession):
		AddressBookNode = namedtuple('AddressBookNode', 'name, contact')
		AddressBookContact = namedtuple('AddressBookContact', 'email, phone_numbers')
		AddressBookPhone = namedtuple('AddressBookPhone', 'id, phone_type, number')
		for dbid, intid in self._ids_empresas.items():
			if intid == id:
				id_empresa = dbid
				empresa = dbsession.query(self.empresas.columns.Empresa).filter(self.empresas.columns.IDEmpresa == id_empresa).one()
				return AddressBookNode(empresa, None)
		for dbid, intid in self._ids_contactos.items():
			if intid == id:
				id_empresa = dbid
				contact = dbsession.query(self.contacts).filter(self.contacts.columns.IDContacto == id_empresa).one()
				phones = []
				for phone in dbsession.query(self.telefonos).filter(self.telefonos.columns.IDref2 == id_empresa).all():
					phones.append(AddressBookPhone('0', phone.Tipo, phone.numero))
				email = ''
				try:
					email = dbsession.query(self.emails.columns.Direccion).filter(self.emails.columns.IDref == id_empresa).first()[0]
					print email
				except:
					pass
				c = AddressBookContact(email, phones)
				return AddressBookNode('%s %s'% (contact.Nombre, contact.Apellido), c)