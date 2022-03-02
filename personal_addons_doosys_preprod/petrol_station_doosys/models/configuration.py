# -*- coding: utf-8 -*-

from odoo import models, fields, api

class petrol_station(models.Model):
    _name = 'petrol.station'      
    name = fields.Char(string="Nom", required=True)
    code_station= fields.Char(string="Code Station")
    pricelist_id= fields.Many2one('product.pricelist',string='Listes de prix')
    client_comptant_id = fields.Many2one("res.partner", string="Clients au comptant")
    bon_drh_client_id = fields.Many2one("res.partner",string='Bon drh Client')


class petrol_station_pompe(models.Model):
    _name = 'petrol.station.pompe'      
    name = fields.Char(string="Nom" , required=True)
    product_id=fields.Many2one('product.product', related="reservoirs_id.product_id", string="Produit", domain="[('sale_ok','=',True),('categ_id','ilike','Carburant')]")
    station_id=fields.Many2one('petrol.station',related="reservoirs_id.station_id", string="Station")
    reservoirs_id=fields.Many2one('petrol.station.reservoir', string="Réservoirs")
    compteur=fields.Float( string="Compteur")
    _sql_constraints = [
        ('pompe_uniq', 'unique(name, station_id)', ' Pompe doit être unique par station'),
    ]
class petrol_statio_pompe(models.Model):
    _name = 'type.paiement'      
    name = fields.Char(string="Type de paiement",  required=True)
    type = fields.Selection([
            ('banque','Banque'),
            ('confrere', 'Confrère'),
            ('espece', 'Espècce'),
        ], string='Type', index=True)
    refacture=fields.Boolean( string="refacturer ", default=False)
    #required fields for recette
    req_produit_rec=fields.Boolean( string="produit obligatoire recette  ", default=False)
    req_km_rec=fields.Boolean( string="kilométrage obligatoire recette", default=False)
    req_ref_rec=fields.Boolean( string="référence obligatoire recette", default=False)
    req_client_rec=fields.Boolean( string="Client obligatoire recette", default=False)
    
    req_produit=fields.Boolean( string="produit obligatoire ", default=False)
    automatique_flux = fields.Selection([
            ('all_flux','bon de commande + Bon de livraion + Facture + payement'),
            ('commande_livraison', 'bon de commande + Bon de livraion'),
        ], string='Flux Autoamtique', index=True)
class res_partener(models.Model):
    _inherit = 'res.partner' 
    plafond =   fields.Float(string="Plafond mensuel")
    plafond_sap =  fields.Float(string="Plafond mensuel sap")
    plafond_annuel = fields.Float(string="Plafond annuel ")
    solde_client = fields.Float(string="Solde à payer")
    reste= fields.Float(string="Reste", compute='set_diff_plafond_solde', store=True)
    type_paiement = fields.Selection([
            ('banque','Banque'),
            ('confrere', 'Confrère'),
            ('espece', 'Espècce'),
        ], string='Type', index=True)
    commission = fields.Float(string="Commission")
    station_ids = fields.Many2many("petrol.station","res_petrol_station_partner","station_id","partner_id",string="Stations")
    facturable = fields.Boolean(string="Facturable Bon drh")
    credit_ids = fields.One2many('periodic.credit','partner_id',string="Historique Crédit")

    @api.model
    def create(self, vals):
        if vals.get("plafond_sap"):
            vals['plafond'] = vals.get("plafond_sap")

        res = super(res_partener, self).create(vals)

        return res



    @api.multi
    def write(self, vals):
        res =  super(res_partener, self).write(vals)
        if vals.get("plafond_sap"):
            vals['plafond'] = vals.get("plafond_sap")
        res = super(res_partener, self).write(vals)
        return res

    @api.one
    @api.depends('plafond','solde_client')
    def set_diff_plafond_solde(self):
        self.reste=self.plafond - self.solde_client
    @api.one
    def reset_solde(self):
        self.solde_client=0
        self.reste=0


class petrol_station_reservoir(models.Model):
    _name = 'petrol.station.reservoir'      
    name = fields.Char(string="Nom" , required=True)
    pompe_ids=fields.One2many('petrol.station.pompe', 'reservoirs_id')
    product_id=fields.Many2one('product.product', string="Produit" , required=True, domain="[('sale_ok','=',True),('categ_id','ilike','Carburant')]")
    station_id=fields.Many2one('petrol.station', string="Station", required=True)
    stock_initiale=fields.Float( string="Stock Initial (jaugeage)")
    location_id = fields.Many2one('stock.location', 'Emplacements')

    _sql_constraints = [
        ('pompe_uniq', 'unique(name, station_id)', 'Reservoir doit être unique par station'),
    ]
class petrol_station_moyen_paiement(models.Model):
    _name = 'petrol.station.moyen.paiement'      
    name = fields.Char(string="Numéro" , required=True)
    type_paiement_id=fields.Many2one('type.paiement', string="Type de paiement", required=True) 
    type_client=fields.Selection([
            ('banque','Banque'),
            ('confrere', 'Confrère'),
            ('espece', 'Espècce'),
        ], string='Type',  related='type_paiement_id.type', readonly=True)
    client_id=fields.Many2one('res.partner', string="partenaire", required=True, domain="[('type_paiement','=',type_client),('supplier','=',True)]")


class SaleOrder(models.Model):
    _inherit = 'sale.order' 
    recette_id =   fields.Many2one('petrol.station.recette', string="Recette")
class PurchaseOrder(models.Model):
    _inherit = 'purchase.order' 
    recette_id =   fields.Many2one('petrol.station.recette', string="Recette")
class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line' 
    recette_id =   fields.Many2one('petrol.station.recette', string="Recette")
class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line' 
    recette_id =   fields.Many2one('petrol.station.recette', string="Recette")

  


