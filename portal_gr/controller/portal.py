import base64
from odoo.http import request
from odoo import http
from odoo.exceptions import ValidationError

class PortalGR(http.Controller):

    @http.route(['/my/gr'], auth="user", website=True)
    def portal_gr(self, **kwargs):
        user_partner_id = request.env.user.partner_id.id
        purchase_orders = request.env['purchase.order'].sudo().search([
            ('state', '=', 'purchase'),
            ('generate_gr', '=', 'True'),
            ('invoice_status', '!=', 'invoiced'),
            ('partner_id', '=', user_partner_id)
        ])
        return request.render('portalweb_gr.portal_gr_page', {
            'orders': purchase_orders,
            'error_msg': request.params.get('error'),
            'success_msg': request.params.get('success'),
        })
        
    @http.route(['/my/purchase/<int:order_id>'], auth="user", website=True)
    def portal_purchase_detail(self, order_id=None, **kwargs):
        order = request.env['purchase.order'].sudo().browse(order_id)
        return request.render("portalweb_gr.portal_purchase_detail", {
            'order': order,
        })

    @http.route(['/my/gr/upload'], type='http', auth="user", methods=['POST'], csrf=True, website=True)
    def upload_xml(self, **post):
        xml_file = post.get('xml_file')
        order_id = int(post.get('order_id'))

        if not xml_file or not order_id:
            return request.redirect('/my/gr?error=Falta+archivo+o+orden')

        try:
            xml_content = xml_file.read()
            xml_encoded = base64.b64encode(xml_content)

            po = request.env['purchase.order'].sudo().browse(order_id)
            if not po:
                return request.redirect('/my/gr?error=Orden+no+encontrada')

            xml_record = request.env['gr.xml.upload'].sudo().create({
                'name': xml_file.filename,
                'file': xml_encoded,
                'order_id': po.id,
            })

            xml_record.validar_xml_con_orden()

        except ValidationError as e:
            return request.redirect('/my/gr?error=%s' % str(e).replace(" ", "+"))

        return request.redirect('/my/gr?success=XML+subido+correctamente')

    @http.route(['/my/gr/delete_xml/<int:xml_id>'], auth="user", website=True)
    def delete_xml(self, xml_id, **kwargs):
        xml_record = request.env['gr.xml.upload'].sudo().browse(xml_id)
        if xml_record:
            xml_record.unlink()
        return request.redirect('/my/gr?success=Archivo+eliminado+correctamente')

    @http.route(['/my/purchase'], type='http', auth="user", website=True)
    def redirect_gr(self, **kwargs):
        return request.redirect('/my/gr')