{
    'name': 'Portalweb GR',
    'version': '1.0',
    'summary': 'Portal para gestión de facturas XML contra órdenes de compra',
    'description': 'Permite a proveedores subir XMLs y validarlos contra OC',
    'category': 'Portal',
    'author': 'Quinde-Solution',
    'license': 'LGPL-3',
    'depends': ['purchase', 'portal', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'views/gr_xml_upload_views.xml',
        'views/purchase_order_inherit.xml',
        'views/portal_gr_template.xml',
        'views/portal_purchase_inherit.xml',
    ],
    'installable': True,
    'application': False,
}
