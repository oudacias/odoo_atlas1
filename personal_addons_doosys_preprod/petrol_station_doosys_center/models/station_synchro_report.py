# See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api


class StationSynchroReport(models.Model):
    _inherit =  "station.synchro.report"

    @api.model
    def create(self, vals):
        res = super(StationSynchroReport, self).create(vals)
        template_id = self.env.ref('petrol_station_doosys_center.mail_sycnhonisation_report').id
        try:
            self.env['mail.template'].browse(template_id).send_mail(res.id, force_send=True)
        except Exception as e:
            pass
        return res