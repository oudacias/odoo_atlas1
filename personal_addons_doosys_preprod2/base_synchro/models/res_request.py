# See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api


class ResRequest(models.Model):
    _name = 'res.request'
    _order = 'date desc'
    _description = 'Request'

    name = fields.Char('Subject', required=True)
    date = fields.Datetime()
    act_from = fields.Many2one('res.users', 'From')
    act_to = fields.Many2one('res.users', 'To')
    body = fields.Text(string='Request')


class StationSynchroReport(models.Model):
    _name =  "station.synchro.report"
    _order = 'id desc'

    date  = fields.Datetime("Date ")
    db_name = fields.Char("Data base")
    address_ip = fields.Char("Adresse ip local")
    address_ip_client = fields.Char("Adresse ip")
    etat =  fields.Selection([
        ('no_erreur', 'Passe'),
        ('erreur', 'Erreur'),
    ], string="Etat")
    erreur =  fields.Text(string="Erreurs")
    user_name =  fields.Char("Utilisateur")
    raport = fields.Text("Rapport")
    station_station_remote_id = fields.Integer("Station ID")
    station_id =  fields.Many2one("petrol.station",string="Station", compute="_station_id")
    url = fields.Char("URL")


    @api.multi
    @api.depends("station_station_remote_id")
    def _station_id(self):
        for rec in self:
            if rec.station_station_remote_id:
                station_id = self.env["petrol.station"].search([('id','=',rec.station_station_remote_id)],limit=1)
                if station_id:
                    rec.station_id = station_id