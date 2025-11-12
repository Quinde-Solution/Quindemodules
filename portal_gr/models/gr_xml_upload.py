from odoo import models, fields, api
from odoo.exceptions import ValidationError
import base64
import xml.etree.ElementTree as ET

class GRXMLUpload(models.Model):
    _name = 'gr.xml.upload'
    _description = 'Carga de XML por proveedor'

    name = fields.Char(string="Nombre del archivo")
    file = fields.Binary(string="Archivo XML", required=True)
    order_id = fields.Many2one('purchase.order', string="Orden de Compra")
    rfc_emisor = fields.Char(string="RFC Emisor")
    total = fields.Monetary(string="Total", currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related='order_id.currency_id', string='Moneda', readonly=True)
    validate = fields.Boolean(string="¿Validado?", default=False)

    @api.model
    def create(self, vals):
        record = super().create(vals)
        record._parse_xml()
        return record

    def _parse_xml(self):
        for rec in self:
            try:
                xml_data = base64.b64decode(rec.file)
                root = ET.fromstring(xml_data)
                ns = {'cfdi': 'http://www.sat.gob.mx/cfd/4'}

                emisor = root.find('cfdi:Emisor', ns)
                total = root.attrib.get('Total')

                rec.rfc_emisor = emisor.attrib.get('Rfc')
                rec.total = float(total)
            except Exception as e:
                raise ValidationError("Error al leer el XML: %s" % str(e))

    def validar_xml_con_orden(self):
        for rec in self:
            if not rec.order_id:
                raise ValidationError("No hay orden relacionada.")

            if rec.rfc_emisor != rec.order_id.partner_id.vat:
                raise ValidationError("El RFC del XML no coincide con el proveedor.")

            total_xmls = sum(x.total for x in rec.order_id.xml_ids)
            if abs(total_xmls - rec.order_id.amount_total) > 1:
                raise ValidationError("El total no cuadra con la orden.")

            rec.validate = True
