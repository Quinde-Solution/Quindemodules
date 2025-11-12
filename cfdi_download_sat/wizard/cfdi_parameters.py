import pytz
from odoo import models, fields
import base64
import datetime, os
from cfdiclient import Fiel, Autenticacion, SolicitaDescargaRecibidos, VerificaSolicitudDescarga, DescargaMasiva
import zipfile
import os
import shutil
from odoo import api, SUPERUSER_ID
import time

class CFDI_Downloaf_Wizard(models.TransientModel):
    _name = "cfdi.download.wizard"
    _description = "Wizard para descargar CFDI"
    
    starting_date = fields.Datetime(string="Fecha Inicial")
    
    end_date = fields.Datetime(string="Fecha Final")
    
    company_id = fields.Many2one('res.company', string='Compañía', default=lambda self: self.env.company.id)

    rfc = fields.Char(related='company_id.vat', string="RFC", readonly=True)
    
    def download_cfdi(self):
        try:
            tz = self.env.context.get('tz') or 'America/Mexico_City'
            timezone = pytz.timezone(tz)

            fecha_i = fields.Datetime.context_timestamp(self, self.starting_date).astimezone(timezone)
            fecha_f = fields.Datetime.context_timestamp(self, self.end_date).astimezone(timezone)
            
            fecha_inicial_dt = fecha_i.replace(tzinfo=None)
            fecha_final_dt = fecha_f.replace(tzinfo=None)
            
            # FIEL_CER = '/opt/odoo/brmx/cfdi_download/certificates/00001000000511931220.cer'
            # FIEL_KEY = '/opt/odoo/brmx/cfdi_download/certificates/Claveprivada_FIEL_BEN180223TI2_20220315_210910.key'
            # ZIP_DIR = "/opt/odoo/"
            # EXTRACT_DIR = "/opt/odoo/unzipped"
            
            FIEL_CER = '/home/odoo/src/user/cfdi_download/certificates/00001000000511931220.cer'
            FIEL_KEY = '/home/odoo/src/user/cfdi_download/certificates/Claveprivada_FIEL_BEN180223TI2_20220315_210910.key'
            ZIP_DIR = "/home/odoo/"
            EXTRACT_DIR = "/home/odoo/unzipped"
            FIEL_PAS = 'ben180223ti2'

            cer_der = open(FIEL_CER, 'rb').read()
            key_der = open(FIEL_KEY, 'rb').read()

            fiel = Fiel(cer_der, key_der, FIEL_PAS)

            auth = Autenticacion(fiel)
            token = auth.obtener_token()

            print("Token obtenido", token)
            solicita_recibidos = SolicitaDescargaRecibidos(fiel)


            id_recibidos = solicita_recibidos.solicitar_descarga(token=token, rfc_solicitante=self.rfc, fecha_inicial=fecha_inicial_dt, fecha_final=fecha_final_dt, rfc_receptor=self.rfc, tipo_solicitud='CFDI', estado_comprobante='Vigente')
            print('SOLICITUD 1:', id_recibidos)

            verifica = VerificaSolicitudDescarga(fiel)
            estado_recibidos = verifica.verificar_descarga(token, self.rfc, id_recibidos['id_solicitud'])

            verifica = VerificaSolicitudDescarga(fiel)

            # 🔁 Esperar a que el SAT procese la solicitud (puede tardar varios minutos)
            estado_recibidos = {}
            for intento in range(10):  # Reintenta hasta 10 veces (5 minutos en total)
                estado_recibidos = verifica.verificar_descarga(token, self.rfc, id_recibidos['id_solicitud'])
                print(f'Intento {intento+1}: Estado -> {estado_recibidos.get("estado_solicitud")}')
                
                # Si ya hay paquetes disponibles, sal del ciclo
                if estado_recibidos.get('paquetes'):
                    print("Paquetes disponibles:", estado_recibidos['paquetes'])
                    break
                
                # Si el SAT aún no genera los paquetes, esperar 30 segundos
                print("Esperando 30 segundos para volver a verificar...")
                time.sleep(30)


            print('SOLICITUD 2:', estado_recibidos)

            for paquete in estado_recibidos['paquetes']:
                print('PAQUETE A DESCARGAR: ', paquete)
                descarga = DescargaMasiva(fiel)

                descarga = descarga.descargar_paquete(token, self.rfc, paquete)

                print('PAQUETE: ', paquete)

                with open('{}.zip'.format(paquete), 'wb') as fp:

                    fp.write(base64.b64decode(descarga['paquete_b64']))
            
            
            for filename in os.listdir(ZIP_DIR):
                if filename.endswith(".zip"):
                    zip_path = os.path.join(ZIP_DIR, filename)
                    extract_path = os.path.join(EXTRACT_DIR, filename.replace(".zip", ""))
                    os.makedirs(extract_path, exist_ok=True)

                    # Descomprimir
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(extract_path)

                    # Subir archivos
                    for file_name in os.listdir(extract_path):
                        file_path = os.path.join(extract_path, file_name)
                        if os.path.isfile(file_path):
                            with open(file_path, "rb") as f:
                                file_data = f.read()
                            self.env['documents.document'].sudo().create({
                                'name': file_name,
                                'datas': base64.b64encode(file_data),
                                'mimetype': 'application/octet-stream',
                            })

                    # Eliminar ZIP y carpeta temporal
            os.remove(zip_path)
            shutil.rmtree(extract_path)                 
            
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Descarga completada',
                    'message': 'Los CFDI han sido descargados exitosamente. \r\nMensaje: {} \r\nCDFIs: {} '.format(id_recibidos['mensaje'], estado_recibidos['numero_cfdis']),
                    'type': 'success',  # Puedes usar 'warning', 'danger', 'info'
                    'sticky': False,    # True si quieres que el mensaje no desaparezca automáticamente
                }
            }
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error en la descarga',
                    'message': 'Ocurrió un error durante la descarga de los CFDI. \r\nError: {} '.format(str(e)),
                    'type': 'danger',  # Puedes usar 'warning', 'danger', 'info'
                    'sticky': True,    # True si quieres que el mensaje no desaparezca automáticamente
                }
            }