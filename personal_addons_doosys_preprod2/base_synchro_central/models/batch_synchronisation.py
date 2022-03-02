# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class batch_synchronisation(models.Model):
    _name = "batch.synchronisation"

    station_id  = fields.Many2one('petrol.station', string="Station" )
    hour = fields.Float("Heur de lancement ")
    last_synchonisation_date =  fields.Datetime("Date deriner synchonisation ")
    etat = fields.Selection([
        ('demarre','Demarre'),
        ('en_cours','En cours'),
        ('termine','Terminé')
    ], string="Etat")
    nombre_tentatives = fields.Integer("Nombre tentatives")
    method = fields.Selection([
        ('manuel','Manuel'),
        ('auto','Auto')
    ], string="Method")

