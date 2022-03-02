# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class petrol_station(models.Model):
    _inherit = 'petrol.station'

    id_remote = fields.Integer("Code station centrale")
    synchro_id = fields.Many2one("base.synchro.server",string="BaseSynchroServer",compute="_synchro_id")
    station_synch_id = fields.Many2one('base.synchro.obj.line')
    duplicate =  fields.Boolean("Dupliqué")
    forcer = fields.Boolean("Forcer la synchrinisation")

    @api.multi
    def forcer_synchronisation(self):
        self.ensure_one()
        self.forcer= True

    @api.multi
    def netoyer(self):
        for rec in self:
            line_ids = self.env['base.synchro.obj.line'].search([('obj_id','=',self.env.ref('base_synchro_station.synchro_petrol_station').id)])
            line_ids.unlink()

    @api.one
    @api.depends("id_remote")
    def _synchro_id(self):
        if self.id_remote and self.id:
            if not self.station_synch_id:

                self.station_synch_id = self.env['base.synchro.obj.line'].create({
                    'local_id': self.id,
                    'remote_id': self.id_remote,
                    'obj_id': self.env.ref('base_synchro_station.synchro_petrol_station').id
                })
            else:
                self.station_synch_id.write({
                    'local_id': self.id,
                    'remote_id': self.id_remote,
                    'obj_id': self.env.ref('base_synchro_station.synchro_petrol_station').id
                })

            self.synchro_id = self.env['base.synchro.server'].search([],limit=1)
            if self.synchro_id:
                self.synchro_id.write({
                    'station_remote_id': self.id_remote,
                    'station_id':self.id,
                    'station_synch_id':self.station_synch_id.id
                })
