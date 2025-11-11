# -*- coding: utf-8 -*-
{
    'name': "Download CFDI-SAT",
    'summary': """Download Received CFDIs From The SAT""",
    'description': """
        Download Received CFDIs From The SAT
    """,

    'author': "Quinde-Solution",
    'website': "",
    'license': 'LGPL-3',

    'category': 'Account',
    'version': '18.0.0.0',
    'depends': ['account'],
    'data': [
        'wizard/cfdi_parameters.xml',   
        'security/ir.model.access.csv',  
    ],
    'installable':True,
}
