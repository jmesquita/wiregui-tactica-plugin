#!/usr/bin/env python
from setuptools import setup, find_packages
 
setup (
    name = "wiregui_tactica_plugin",
    version = "0.1",
    description="WireGui Tactica CRM Plugin",
    long_description="""\
    Implements various actions to integrate Tactica CRM with WireGui
    """,
    author="Indicium SRL",
    author_email="jmesquita@indicium.com.ar",
    packages = find_packages(),
    install_requires = ['SQLAlchemy'],
    entry_points = {
    'wiregui.addressbook' : ['tactica = wiregui_tactica_plugin.addressbook:PublicAddressBook']
    },
    include_package_data=True,
    zip_safe = False
)
