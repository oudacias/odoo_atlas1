#
from odoo import api, fields, models, _

class SapSynchroWizard(models.TransientModel):
    _name = 'sap.synchro.wizard'

    message  = fields.Text('Message')

    @api.multi
    def upload_download_multi_thread(self):
        recs = self.env['sap.objects'].search([('active_field', "=", True)])
        message = recs.sycnhro()
        view_rec = self.env.ref('synrcho_hana_api.view_lance_synchro_finish',
                                raise_if_not_found=False)
        print("view_rec",view_rec,view_rec.id)
        print("message : ",message)
        action = self.env.ref(
            'synrcho_hana_api.action_view_lance_synchro', raise_if_not_found=False
        ).read([])[0]
        action['views'] = [(view_rec and view_rec.id or False, 'form')]
        action['context'] = {
            'default_message' : message
        }
        return action


