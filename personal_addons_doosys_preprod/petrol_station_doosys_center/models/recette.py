# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError


class petrol_station(models.Model):
    _inherit = 'petrol.station'

    magasin_code = fields.Char("Agence Code")
    compte_caisse = fields.Char("Compte caisse")
    compte_cheque = fields.Char("Compte chèque")
    compte_carte_credite = fields.Char("Compte  carte de crédit")
    compte_bancaires = fields.Char("compte bancaires")
    compte_commission = fields.Char("Compte caisse Commission")
    warehouse_sap = fields.Char(string="Magasin SAP")
    compte_client_comptant= fields.Char("Compte client comptant")
    mac_adress =  fields.Char("Adress mac")
    cart_id =  fields.Integer("Cart de credit")
    card_code = fields.Char("Fournisseur code")

class petrol_station_recette(models.Model):
    _inherit = 'petrol.station.recette'

    cloture_center = fields.Boolean(string="clotûre", default=False)
    magasin_code = fields.Char("Agence Code" , compute="_station_depends")
    warehouse_sap = fields.Char("Magasin SAP", compute="_station_depends")
    synchronisee = fields.Boolean("Synchronisée")

    volumconteur_ids = fields.One2many('petrol.station.volumcomteur', 'recette_id', string="Volumconteur log",domain=[('local_id','!=',0)])
    boncommande_ids = fields.One2many('petrol.station.boncommande', 'recette_id', string="Bon de Commande",domain=[('local_id','!=',0)])
    paiement_ids = fields.One2many('petrol.station.paiement', 'recette_id', string="Recette",domain=[('local_id','!=',0)])
    reglement_credits_ids = fields.One2many('petrol.station.paiement', 'recette_reglement_credits_id',
                                            string="Réglement crédits",domain=[('local_id','!=',0)])
    depense_ids = fields.One2many('petrol.station.depense', 'recette_id', string="Dépense",domain=[('local_id','!=',0)])
    vente_service_ids = fields.One2many('petrol.station.vente.service', 'recette_id', string="Ventes et Services",domain=[('local_id','!=',0)])
    stock_ids = fields.One2many('petrol.station.stock', 'recette_id', string="Stock",domain=[('local_id','!=',0)])


    ligne_volucompteur = fields.Integer("Ligne Volucompteurs" )
    ligne_boncommande = fields.Integer("Ligne boncommande" )
    ligne_paiement = fields.Integer("Ligne paiement" )
    ligne_reglement_credits = fields.Integer("Ligne reglement credits" )
    ligne_depense = fields.Integer("Ligne depense" )
    ligne_stock = fields.Integer("Ligne stock")

    ligne_center_volucompteur = fields.Integer("Ligne center Volucompteurs", compute="_ligne_center_nbr")
    ligne_center_boncommande = fields.Integer("Ligne center boncommande", compute="_ligne_center_nbr")
    ligne_center_paiement = fields.Integer("Ligne center paiement", compute="_ligne_center_nbr")
    ligne_center_reglement_credits = fields.Integer("Ligne  centerreglement credits", compute="_ligne_center_nbr")
    ligne_center_depense = fields.Integer("Ligne center depense", compute="_ligne_center_nbr")
    ligne_center_stock = fields.Integer("Ligne center stock", compute="_ligne_center_nbr")
    #ligne_center_vente_service = fields.Integer("Ligne  centervente service", compute="_ligne_center_nbr")

    have_double = fields.Boolean("Y a des double",compute="_ligne_center_nbr")
    #synchonise_station = fields.Boolean("bien synchniser avec station", compute="_synchonise_station", store=True)

    sale_ids  =  fields.One2many("sale.order","recette_id", string="Devis")



    """@api.multi
    @api.depends()
    def _synchonise_station(self):
        for rec in self:
            if rec.volume_compteur_prix == 0 or
                rec.synchonise_station = False
             elif"""

    @api.multi
    @api.depends("volumconteur_ids", "boncommande_ids", "paiement_ids", "reglement_credits_ids", "depense_ids",
                 "vente_service_ids", "stock_ids")
    def _ligne_center_nbr(self):
        for rec in self:
            rec.ligne_center_volucompteur = len(rec.volumconteur_ids)
            rec.ligne_center_boncommande = len(rec.boncommande_ids)
            rec.ligne_center_paiement = len(rec.paiement_ids)
            rec.ligne_center_reglement_credits = len(rec.reglement_credits_ids)
            rec.ligne_center_depense = len(rec.depense_ids)
            rec.ligne_center_vente_service = len(rec.vente_service_ids)
            rec.vente_center_stock = len(rec.stock_ids)

            if rec.ligne_center_volucompteur > rec.ligne_volucompteur:
                rec.have_double = True
            if rec.ligne_center_boncommande > rec.ligne_boncommande:
                rec.have_double = True
            if rec.ligne_center_paiement > rec.ligne_paiement:
                rec.have_double = True
            if rec.ligne_center_reglement_credits > rec.ligne_reglement_credits:
                rec.have_double = True
            if rec.ligne_center_depense > rec.ligne_depense:
                rec.have_double = True
            #if rec.ligne_center_vente_service > rec.ligne_vente_service:
            #    rec.have_double = True
            #if rec.vente_center_stock > rec.vente_stock:
            #    rec.have_double = True





    @api.one
    @api.constrains('date_recette')
    def _check_date_recette_uniq(self):
        recette_non_valide = self.env['petrol.station.recette'].search(
            [('valide', '=', False),('station_recette_id2','!=',0) ,('station_id', '=', self.station_id.id)])

        if len(recette_non_valide) > 1:
            raise UserError("une recette est encours")
        count_recette = self.env['petrol.station.recette'].search_count(
            [('date_recette', '=', self.date_recette), ('station_id', '=', self.station_id.id),('station_recette_id2','!=',0)])
        if count_recette > 1:
            count_recette_id = self.env['petrol.station.recette'].search(
                [('date_recette', '=', self.date_recette), ('station_id', '=', self.station_id.id),('station_recette_id2','!=',0)])
            print("count_recette_id : ",count_recette_id)
            raise UserError(('Date dois être unique par recette , date : '+self.date_recette))

        return True

    @api.multi
    def update_cloture(self):

        for rec in self.search([('cloture','=',True)]):
         for recette in rec.paiement_ids:
             if str(recette.type_paiement_id.name) != 'Chèque' and str(
                     recette.type_paiement_id.name) != 'CARTE CMI' and str(
                 recette.type_paiement_id.name) != 'Espèces':
                 if not recette.product_id:
                     rec.cloture = False
                 if not recette.client_id1:
                     rec.cloture = False


    @api.multi
    @api.depends("station_id")
    def _station_depends(self):
        for rec in self:
            if rec.station_id :
                rec.magasin_code =  rec.station_id.magasin_code
                rec.warehouse_sap =  rec.station_id.warehouse_sap

    def action_cloturer_recette_station_center(self):
        config = self.env.ref('petrol_station_doosys.petrol_station_confi_global')
        records = self.search([('cloture_center',"=",False),('date_recette', '>',config.date_synchonisation_sap),('date_recette', '<',config.date_end_synchonisation_sap),('station_id','in',config.station_ids.ids),('cloture',"=",True)], order='date_recette asc')
        print(records)
        for rec in records:
            print(rec,rec.station_recette_id2,rec.id)
            if rec.station_recette_id2 and  rec.cloture :
                
                print("station_recette_id2",rec.station_recette_id2 )
                non_cloture = self.env['petrol.station.recette'].search_count(
                    [('date_recette', '<', rec.date_recette), ('date_recette', '>',config.date_synchonisation_sap),('station_id', '=', rec.station_id.id),
                     ('cloture', '=', False)])
                if non_cloture:
                    continue

                if rec.diff <= 10 and rec.diff >= -10:
                    rec.action_cloturer_recette_station()
                    rec.cloture_center = True
                    self._cr.commit()


    def action_cloturer_recette_station(self):
        super(petrol_station_recette, self).action_cloturer_recette_station()
        self.cloture_center = True

    @api.multi
    def write(self, vals):
        #vals["cloture_center_ok"] = True

       # if self.cloture_center == True:
       #     raise UserError("Vous pouvez pas modifier une recette cloturée !!")

        res = super(petrol_station_recette, self).write(vals)

        return res

    @api.model
    def create(self, vals):

        res = super(petrol_station_recette, self).create(vals)
        if not vals.get('station_recette_id2') and 'cloture_center' not in self._fields:
            res.station_recette_id2 = res.id
        if  vals.get('station_recette_id2',False):
            recet_ids = self.search([('station_recette_id2','=',vals.get('station_recette_id2')),('station_id','=',vals.get('station_id'))])
            for recet_id in recet_ids:
                if recet_id.id != res.id:
                    recet_id.station_recette_id2 = 0




        return res


    """@api.multi
    @api.onchange("station_id")
    def onchange_station_id(self):
        if not self.station_id:
            return
        res = {}
        self.pricelist_id = self.station_id.pricelist_id.id
        recette_non_valide = self.env['petrol.station.recette'].search([('valide', '=', False)])

        # set defaults pompes
        pompes = self.env['petrol.station.pompe'].search([('station_id', '=', self.station_id.id)])
        if len(pompes) > 0:
            volumcompteur_line = []
            for pompe in pompes:
                products = self.env['product.pricelist.item'].search(
                    ['&', '&',   ('date_start', '<=', self.date_recette),
                     ('pricelist_id', '>=', self.pricelist_id.id), ('product_tmpl_id', '=', pompe.product_id.id)])
                if products:
                    prix_unitaire = products[0].fixed_price
                else:
                    raise UserError(
                        "vous devez vérifier votre listes de prix pour le produit %s" % pompe.product_id.name)
                data = {
                    'pompe_id': pompe.id,
                    'product_id': pompe.product_id.id,
                    'compteur1': pompe.compteur,
                    'compteur2': 0.00,
                    'prix_unitaire': prix_unitaire
                }
                new_volume_line = self.env['petrol.station.volumcomteur'].create(data)
                volumcompteur_line.append(new_volume_line.id)
            volumconteur_ids = [(4, id) for id in volumcompteur_line]
        self.volumconteur_ids = volumconteur_ids
        # set defaults reservoir
        reservoirs = self.env['petrol.station.reservoir'].search([('station_id', '=', self.station_id.id)])
        if len(reservoirs) > 0:
            stock_line = []

            for reservoir in reservoirs:
                products = self.env['product.pricelist.item'].search(
                    ['&', '&', ('date_start', '<=', self.date_recette),
                     ('pricelist_id', '>=', self.pricelist_id.id), ('product_tmpl_id', '=', reservoir.product_id.id)])
                if products:
                    prix_unitaire = products[0].fixed_price
                else:
                    raise UserError(
                        "vous devez vérifier votre listes de prix pour le produit %s" % reservoir.product_id.name)
                data = {
                    'reservoir_id': reservoir.id,
                    'product_id': reservoir.product_id.id,
                    'stock_initiale': reservoir.stock_initiale,
                    'prix_unitaire': prix_unitaire,
                }
                new_stock_line = self.env['petrol.station.stock'].create(data)
                stock_line.append(new_stock_line.id)
            stock_ids = [(4, id) for id in stock_line]
        self.stock_ids = stock_ids
        """

class petrol_station_velumcompteur(models.Model):

    _inherit = 'petrol.station.volumcomteur'

    local_id = fields.Integer("station Local ID")


class petrol_station_boncommande(models.Model):
    _inherit = 'petrol.station.boncommande'

    local_id = fields.Integer("station Local ID.")

class petrol_station_reservoir(models.Model):
    _inherit = 'petrol.station.stock'

    magasin_code = fields.Char(related="recette_id.magasin_code")
    card_code = fields.Char(related="recette_id.station_id.card_code")
    date_recette = fields.Date(related="recette_id.date_recette")
    warehouse_sap = fields.Char(related="recette_id.warehouse_sap")
    local_id = fields.Integer("station Local ID.")



class petrol_station_paiement(models.Model):
    _inherit = 'petrol.station.paiement'

    local_id = fields.Integer("station Local ID.")
    magasin_code = fields.Char(related="recette_id.magasin_code")
    date_recette2 = fields.Date(related="recette_id.date_recette")

class petrol_station_depense(models.Model):
    _inherit = 'petrol.station.depense'

    local_id = fields.Integer("station Local ID.")

class petrol_station_vente_service(models.Model):
    _inherit = 'petrol.station.vente.service'

    local_id = fields.Integer("station Local ID.")


class station_config(models.Model):
    _inherit = 'petrol.station.config'

    date_synchonisation_sap =  fields.Date("Date de sycnhonisation SAP" ,default="2020-12-08")
    date_end_synchonisation_sap = fields.Date("Date de fin sycnhonisation SAP", default="2020-12-09")
    station_ids = fields.Many2many("petrol.station",string="Les station à stycnhoniser avec SAP")

