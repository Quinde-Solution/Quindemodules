from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    generate_gr = fields.Boolean(string="Generar GR", default=False)
    code_gr = fields.Char(string="Codigo GR", compute="_compute_code_gr")
    xml_ids = fields.One2many('gr.xml.upload', 'order_id', string="XMLs Subidos")
    xml_total_sum = fields.Monetary(string="Total XMLs", compute="_compute_xml_total", store=True)
    xml_validate = fields.Boolean(string="XMLs Validados", compute="_compute_xml_validate", store=True, readonly=True)
    currency_id = fields.Many2one(related='company_id.currency_id', readonly=True)  # Necesario para campo Monetary

    @api.depends('generate_gr', 'xml_validate', 'xml_ids')
    def _compute_code_gr(self):
        for order in self:
            if order.generate_gr and order.xml_validate and order.xml_ids:
                company_code = order.company_id.partner_id.name[:4].upper() if order.company_id else 'COMP'
                fecha = datetime.now().strftime('%y%m%d')
                po_number = str(order.id).zfill(4)
                order.code_gr = f"GR-{company_code}-{fecha}-{po_number}"
            else:
                order.code_gr = False
                
    @api.depends('xml_ids.total', 'xml_ids.validate')
    def _compute_xml_total(self):
        for order in self:
            order.xml_total_sum = sum(x.total for x in order.xml_ids)

    @api.depends('xml_ids', 'amount_total')
    def _compute_xml_validate(self):
        for order in self:
            total = sum(x.total for x in order.xml_ids if x.validate)
            rfcs_match = all(x.rfc_emisor == order.partner_id.vat for x in order.xml_ids if x.validate)
            order.xml_validate = total == order.amount_total and rfcs_match

    def action_create_invoice(self):
        for order in self:
            if order.generate_gr:
                if not order.xml_validate:
                    raise ValidationError("Los XMLs no están validados correctamente (RFC o total incorrecto).")
        return super().action_create_invoice()
