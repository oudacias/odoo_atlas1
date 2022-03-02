# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
import threading

class BaseSynchroServer(models.Model):
    _inherit = "base.synchro.server"


    station_remote_id = fields.Integer('station id', required=True,default=0)

    station_synch_id = fields.Many2one('base.synchro.obj.line')
    station_id = fields.Many2one('petrol.station' )


    @api.multi
    @api.onchange('station_remote_id','station_id')
    def change_station_remote_id(self):
        self.ensure_one()

        if self.station_remote_id and self.station_id:

            if not self.station_synch_id:

                self.station_synch_id = self.env['base.synchro.obj.line'].create({
                    'local_id': self.station_id.id,
                    'remote_id': self.station_remote_id,
                    'obj_id': self.env.ref('base_synchro_station.synchro_petrol_station').id
                })
            else:
                self.station_synch_id.write({
                    'local_id': self.station_id.id,
                    'remote_id': self.station_remote_id,
                    'obj_id': self.env.ref('base_synchro_station.synchro_petrol_station').id
                })


    @api.model
    def cron_synchro(self):
        recs = self.search([])
        for rec in recs:
                synchro_id = self.env['base.synchro'].create({
                    'server_url': rec.id,
                    'user_id': 1 #rec.user_id.id
                })

                threaded_synchronization = threading.Thread(
                    target=synchro_id.upload_download())
                threaded_synchronization.run()


        return None

class BaseSynchroObj(models.Model):

    _inherit = "base.synchro.obj"

    station_remote_id = fields.Integer(related="server_id.station_remote_id")

    initial = fields.Boolean(string="initial")

class BaseSynchroObjLine(models.Model):
    _inherit = "base.synchro.obj.line"

    @api.model
    def cron_initial(self):
        obj_ids = self.env['base.synchro.obj'].search([('initial','=',True)])
        for obj_id in obj_ids:
            objs = self.env[obj_id.model_id.model].search([])
            for obj in objs:
                    print(obj)
                    self.env['base.synchro.obj.line'].create({
                        'obj_id': obj_id.id,
                        'local_id': obj.id,
                        'remote_id': obj.id
                    })





