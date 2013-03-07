from collections import namedtuple
#import logging

from sqlalchemy import Table
from sqlalchemy import MetaData
from sqlalchemy import and_, asc

from wiregui_server.log_ import loggerFactory
from wiregui_server.addressbook import AddressBookPluginBase, AddressBookNode, AddressBookContact, AddressBookPhone

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
		self._last_id = 1
		self._ids_contactos = {}
		self._phone_ids = {}

	@dbsession
	def public(self,dbsession):
		''' Return proper addressbook format (json) '''
		entries = AddressBookNode(0, 'Public Address Book', [])
		for empresa in dbsession.query(self.empresas).filter(self.empresas.columns.Calificacion=='DIRECTORIO').order_by(asc(self.empresas.columns.Empresa)).all():
			id_empresa = self._ids_empresas.get(empresa.IDEmpresa)
			if id_empresa is None:
				self._last_id = self._last_id +1
				id_empresa = self._last_id
				self._ids_empresas[empresa.IDEmpresa] = self._last_id

			contacts = []
			for c in dbsession.query(self.contacts).filter(and_(empresa.IDEmpresa == self.contacts.columns.IDEmpresa, self.contacts.columns.Bloqueado == 0)).all():
				print empresa.Empresa, c.Nombre, c.Apellido
				id_contacto = self._ids_contactos.get(c.IDContacto)
				if id_contacto is None:
					self._last_id = self._last_id +1
					id_contacto = self._last_id
					self._ids_contactos[c.IDContacto] = self._last_id

				phones = []
				email = ''
				try:
					email = dbsession.query(self.emails.columns.Direccion).filter(self.emails.columns.IDref == c.IDContacto).first()[0]
				except:
					pass
				contactObj = AddressBookContact(id_contacto, '%s %s' % (c.Nombre, c.Apellido), email, phones, id_contacto)
				for phone in dbsession.query(self.telefonos).filter(self.telefonos.columns.IDref2 == c.IDContacto).all():
					id_phone = self._phone_ids.get(phone.RecID)
					if id_phone is None:
						self._last_id = self._last_id +1
						id_phone = self._last_id
						self._phone_ids[phone.RecID] = self._last_id
					phones.append(AddressBookPhone(id_phone, phone.Tipo, phone.numero, contactObj, phone.numero))
				contactObj.phone_numbers = phones
				contacts.append(contactObj)

			entries.children.append(AddressBookNode(id_empresa, empresa.Empresa, contacts))

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
					id_phone = self._phone_ids.get(phone.RecID)
					if id_phone is None:
						self._last_id = self._last_id +1
						id_phone = self._last_id
						self._phone_ids[phone.RecID] = self._last_id
					phones.append(AddressBookPhone(id_phone, phone.Tipo, phone.numero))
				email = ''
				try:
					email = dbsession.query(self.emails.columns.Direccion).filter(self.emails.columns.IDref == id_empresa).first()[0]
				except:
					pass
				c = AddressBookContact(email, phones)
				return AddressBookNode('%s %s'% (contact.Nombre, contact.Apellido), c)