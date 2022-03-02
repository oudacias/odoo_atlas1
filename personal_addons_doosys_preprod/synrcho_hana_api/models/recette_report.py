from odoo import api, fields, models,  _


class recette_report(models.Model):
    _name =  'recette.report'

    date  =  fields.Datetime('Date' , default=fields.Datetime.now())
    recette_id = fields.Many2one('petrol.station.recette', string="Recette")
    station_id = fields.Many2one('petrol.station', string="Station")
    report = fields.Text("Rapport")
    erreur =  fields.Text("Erreur")
    synchro_report_id = fields.Many2one('sap.synchro.report', string="Synchonisation global")

    state = fields.Selection([
        ('passe','Passe'),
        ('erreur','Erreur')
    ])