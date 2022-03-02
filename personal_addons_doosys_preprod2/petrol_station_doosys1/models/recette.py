# -*- coding: utf-8 -*-
import logging
from os import write
from odoo import models, fields, api
from odoo.exceptions import UserError, Warning, ValidationError
from datetime import datetime, timedelta, date
from odoo.addons import decimal_precision as dp
from odoo.addons.sale_automatic_workflow.models.automatic_workflow_job \
import savepoint
import datetime
import calendar
import os

_logger = logging.getLogger(__name__)
check_plafond = {}
check_paiement = {}
empty = False

class petrol_station_recette(models.Model):
    _name = 'petrol.station.recette'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'date_recette'
    _order = 'id desc'

    name = fields.Char(string="name")
    station_id = fields.Many2one('petrol.station', string="Nom de station",
                                 default=lambda self: self.env.user.station_id)
    pricelist_id = fields.Many2one('product.pricelist', compute="_pricelist_id", string='Listes de prix')
    list_prix_res = fields.Char('Prix Carburant')
    responsable_id = fields.Many2one('res.users', string="Responsable", default=lambda self: self.env.user.id)
    state = fields.Selection([
        ('volumeconteur', 'Volume compteur'),
        ('stock', 'Stock'),
        ('boncommande', 'Crédit client'),
        ('paiement', 'Recette'),
        ('depense', 'Dépense'),
        ('vente_service', 'Ventes et Services'),
        ('regement_credits', 'Régement crédits'),

    ], string='Status', index=True, default='stock', copy=False)
    date_recette = fields.Date(string='Date de recette',
                               readonly=False, index=True,
                               help="Date de recette", default=lambda self: date.today())
    # date_recette2 = fields.Date(string='Date de recette', default=lambda self: date.today())
    volumconteur_ids = fields.One2many('petrol.station.volumcomteur', 'recette_id', string="Volumconteur log")
    boncommande_ids = fields.One2many('petrol.station.boncommande', 'recette_id', string="Bon de Commande")
    paiement_ids = fields.One2many('petrol.station.paiement', 'recette_id', string="Recette")
    reglement_credits_ids = fields.One2many('petrol.station.paiement', 'recette_reglement_credits_id',
                                            string="Réglement crédits")
    depense_ids = fields.One2many('petrol.station.depense', 'recette_id', string="Dépense")
    vente_service_ids = fields.One2many('petrol.station.vente.service', 'recette_id', string="Ventes et Services")
    stock_ids = fields.One2many('petrol.station.stock', 'recette_id', string="Stock")
    diff = fields.Float(string="Equilibrer recette", compute="calcule_diff", readonly=True, store=True,
                        digits=dp.get_precision('Station Petrol Price'))
    volume_compteur_prix = fields.Float(string="Total Volume compteur", compute="calcule_total_compteur", readonly=True)
    total_credit_client_prix = fields.Float(string="Total Crédit client", compute="calcule_total_credit_client",
                                            readonly=True, digits=dp.get_precision('Station Petrol Price'))
    total_paiement = fields.Float(string="Total Recette", compute="calcule_total_paiement", readonly=True,
                                  digits=dp.get_precision('Station Petrol Price'))
    total_depense = fields.Float(string="Total Dépense", compute="calcule_total_depense", readonly=True,
                                 digits=dp.get_precision('Station Petrol Price'))
    total_vente_service = fields.Float(string="Total Ventes et Services", compute="calcule_total_vente_service",
                                       readonly=True, digits=dp.get_precision('Station Petrol Price'))
    total_reglement_credit = fields.Float(string="Total Régelement Crédit", compute="calcule_total_reglement_credit",
                                          readonly=True, digits=dp.get_precision('Station Petrol Price'))
    valide = fields.Boolean(string="valide", default=False)
    cloture = fields.Boolean(string="clotûre", default=False)
    justifier_ecart = fields.Text(string="justifier l'ecart ")
    cuve_espece = fields.Float(string="valeur cuve en espece", compute="calcule_valeur_cuve_espece", readonly=True,
                               digits=dp.get_precision('Station Petrol Price'))
    cuve_cheque = fields.Float(string="valeur cuve en cheque", compute="calcule_valeur_cuve_cheque", readonly=True,
                               digits=dp.get_precision('Station Petrol Price'))
    cuve_tpe = fields.Float(string="valeur cuve en tpe", compute="calcule_valeur_cuve_tpe", readonly=True,
                            digits=dp.get_precision('Station Petrol Price'))
    station_recette_id = fields.Integer("station recette ID" )
    station_recette_id2 = fields.Integer("station recette ID.")

    """_sql_constraints = [
        ('date_recette_uniq', 'unique(date_recette,station_id)', 'Date dois être unique par recette'),
        ('date_recette2_uniq', 'unique(date_recette2,station_id)', 'Date dois être unique par recette'),
    ]"""
    @api.model
    def update_cluture(self):
        recette_ids = self.env['petrol.station.recette'].search([('cloture','=',True),'|',('stock_ids.cloture','=',False),('paiement_ids.cloture','=',False)])
        print("recette_ids : ",recette_ids)
        for recette_id in recette_ids:
            recette_id.cloture=False
            self._cr.commit()
            recette_id.cloture = True
            self._cr.commit()

    @api.one
    @api.constrains('date_recette')
    def _check_date_recette_uniq(self):
        if(empty == True):
            today = fields.Date.today()
            print("today usf",today,self.date_recette)
            if today < self.date_recette :
                raise UserError("La date de recette doit être inférieur d'aujourd'hui")
            recette_non_valide = self.env['petrol.station.recette'].search([('valide', '=', False),('station_id', '=', self.station_id.id)])

            if len(recette_non_valide) > 1:
                raise UserError("une recette est encours")
            count_recette  =  self.env['petrol.station.recette'].search_count([('date_recette','=',self.date_recette),('station_id','=',self.station_id.id)])
            if count_recette > 1 :
                raise UserError(('Date dois être unique par recette'))
            recette_max =  self.env['petrol.station.recette'].search([('station_id','=',self.station_id.id)],limit=1,order='date_recette desc')
            if recette_max.date_recette > self.date_recette :
                raise UserError(('Date dois être supéreir à la dériner recette'))
            return True

    @api.multi
    @api.depends("station_id")
    def _pricelist_id(self):
        for rec in self:
            if rec.station_id:
                rec.pricelist_id = rec.station_id.pricelist_id


    @api.model
    def update_station_recette_id(self):
        recs = self.search([])
        print("update_station_recette_id")
        for rec in recs:
            if not rec.station_recette_id2:
                rec.station_recette_id2 = rec.id

    @api.onchange("date_recette", "station_id")
    def change_recette(self):

        for k,v in check_plafond.items():
            check_plafond[k] = [0]

        for k,v in check_paiement.items():
            check_paiement[k] = [0]
        if self.date_recette and self.station_id:
            if self.id:
                recette_count = self.search_count(
                    [('date_recette', '=', self.date_recette), ('station_id', '=', self.station_id.id),
                     ('id', '!=', self.id)])
            else:
                recette_count = self.search_count(
                    [('date_recette', '=', self.date_recette), ('station_id', '=', self.station_id.id)])

            print("coutn recette2", recette_count, self.date_recette, self.station_id.id)
            self.onchange_station_id()
            if recette_count:
                raise UserError("Date doit être unique par recette")

    @api.model
    def create(self, vals):
        
        if vals.get('date_recette2'):
            vals['date_recette'] = vals['date_recette2']
        res  = super(petrol_station_recette, self).create(vals)
        if not vals.get('station_recette_id2') and 'cloture_center' not in self._fields :
            res.station_recette_id2  = res.id
        return res

    @api.multi
    def write(self, vals):
        if vals.get('date_recette2'):
            vals['date_recette'] = vals['date_recette2']

        res = super(petrol_station_recette, self).write(vals)
        
        return res

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.valide :
                raise UserError("impossible de supprimer la recette ")
            rec.volumconteur_ids.unlink()
            rec.boncommande_ids.unlink()
            rec.paiement_ids.unlink()
            rec.reglement_credits_ids.unlink()
            rec.depense_ids.unlink()
            rec.vente_service_ids.unlink()
            rec.stock_ids.unlink()
        return super(petrol_station_recette, self).unlink()

    @api.onchange('pricelist_id')
    def concat_produit_prix(self):

        products = self.env['product.pricelist.item'].search(
            [('date_start', '<=', self.date_recette),('date_end', '>=', self.date_recette), ('pricelist_id', '=', self.pricelist_id.id)], limit=1,
            order="date_start desc, id desc")
        self.list_prix_res = ''
        for product in products:
            self.list_prix_res = str(self.list_prix_res) + ' (' + str(product.product_tmpl_id.name) + ':' + str(
                product.fixed_price) + ') '

    @api.multi
    def _get_printed_report_name(self):
        self.ensure_one()
        return "Rapport Journalier"

    @api.one
    @api.depends('paiement_ids', 'depense_ids', 'vente_service_ids')
    def calcule_valeur_cuve_espece(self):
        total_recette_espece = 0
        total_depense_espece = 0
        total_vente_espece = 0
        for recette in self.paiement_ids:
            if recette.type_paiement_id.name == 'Espèces':
                total_recette_espece = total_recette_espece + recette.montant
        for depense in self.depense_ids:
            if depense.type_paiement_id.name == 'Espèces':
                total_depense_espece = total_depense_espece + depense.montant
        for vente in self.vente_service_ids:
            if vente.type_paiement_id.name == 'Espèces':
                total_vente_espece = total_vente_espece + vente.montant
        self.cuve_espece = total_recette_espece - total_vente_espece + total_depense_espece

    @api.one
    @api.depends('paiement_ids', 'depense_ids', 'vente_service_ids')
    def calcule_valeur_cuve_tpe(self):
        total_recette_tpe = 0
        total_depense_tpe = 0
        total_vente_tpe = 0
        for recette in self.paiement_ids:
            if recette.type_paiement_id.name == 'CARTE CMI':
                total_recette_tpe = total_recette_tpe + recette.montant
        for depense in self.depense_ids:
            if depense.type_paiement_id.name == 'CARTE CMI':
                total_depense_tpe = total_depense_tpe + depense.montant
        for vente in self.vente_service_ids:
            if vente.type_paiement_id.name == 'CARTE CMI':
                total_vente_tpe = total_vente_tpe + vente.montant
        self.cuve_tpe = total_recette_tpe - total_vente_tpe + total_depense_tpe

    @api.one
    @api.depends('paiement_ids', 'depense_ids', 'vente_service_ids')
    def calcule_valeur_cuve_cheque(self):
        total_recette_cheque = 0
        total_depense_cheque = 0
        total_vente_cheque = 0
        for recette in self.paiement_ids:
            if recette.type_paiement_id.name == 'Chèque':
                total_recette_cheque = total_recette_cheque + recette.montant
        for depense in self.depense_ids:
            if depense.type_paiement_id.name == 'Chèque':
                total_depense_cheque = total_depense_cheque + depense.montant
        for vente in self.vente_service_ids:
            if vente.type_paiement_id.name == 'Chèque':
                total_vente_cheque = total_vente_cheque + vente.montant
        self.cuve_cheque = total_recette_cheque - total_vente_cheque + total_depense_cheque

    @api.one
    @api.depends('reglement_credits_ids')
    def calcule_total_reglement_credit(self):
        total_reglement_credit = 0
        for regelement in self.reglement_credits_ids:
            total_reglement_credit = total_reglement_credit + regelement.montant
        self.total_reglement_credit = total_reglement_credit

    @api.one
    @api.depends('vente_service_ids')
    def calcule_total_vente_service(self):
        total_vente_service = 0
        for vente in self.vente_service_ids:
            total_vente_service = total_vente_service + vente.montant
        self.total_vente_service = total_vente_service

    @api.one
    @api.depends('depense_ids')
    def calcule_total_depense(self):
        total_depense = 0
        for depense in self.depense_ids:
            total_depense = total_depense + depense.montant
        self.total_depense = total_depense

    @api.one
    @api.depends('paiement_ids')
    def calcule_total_paiement(self):
        total_paiement = 0
        for paiement in self.paiement_ids:
            total_paiement = total_paiement + paiement.montant
        self.total_paiement = total_paiement

    @api.onchange('volumconteur_ids')
    def mettre_a_jours_sortie_reservoirs(self):
        for stock in self.stock_ids:
            sortie = 0
            sortie2 = 0
            for volume in self.volumconteur_ids:
                if volume.pompe_id.reservoirs_id.id == stock.reservoir_id.id:
                    sortie = sortie + volume.sortie
                    sortie2 = sortie2 + volume.sortie

            stock.sortie = sortie
            stock.sortie2 = sortie2

    @api.one
    @api.depends('boncommande_ids')
    def calcule_total_credit_client(self):
        total_credit_client = 0
        for bon in self.boncommande_ids:
            total_credit_client = total_credit_client + bon.montant
        self.total_credit_client_prix = total_credit_client

    @api.one
    @api.depends('volumconteur_ids')
    def calcule_total_compteur(self):
        total_produit_vendu = 0
        for volumconteur in self.volumconteur_ids:
            if volumconteur.compteur2 >= volumconteur.compteur1:
                total_produit_vendu = total_produit_vendu +  volumconteur.ca_sortie

        self.volume_compteur_prix = total_produit_vendu

    @api.one
    @api.depends('volumconteur_ids', 'boncommande_ids', 'reglement_credits_ids', 'depense_ids', 'paiement_ids',
                 'vente_service_ids')
    def calcule_diff(self):
        total_bon_commande = 0
        for bncommande in self.boncommande_ids:  # Crédit client
            total_bon_commande = total_bon_commande + bncommande.montant
        total_paiement = 0
        for paiement in self.paiement_ids:  # Recette8069
            total_paiement = total_paiement + paiement.montant
        total_produit_vendu = 0
        for volumconteur in self.volumconteur_ids:  # VoluCompteur
            if volumconteur.compteur2 >= volumconteur.compteur1:
                total_produit_vendu = total_produit_vendu + volumconteur.ca_sortie
        total_service_vendu = 0
        for vente in self.vente_service_ids:
            if str(vente.type_paiement_id.name) == 'Espèces':  # vente
                total_service_vendu = total_service_vendu + vente.montant
        total_depense = 0
        for depense in self.depense_ids:
            if str(depense.type_paiement_id.name) == 'Espèces':  # Depense
                total_depense = total_depense + depense.montant
        total_reg_credit = 0
        # for reg_credit in self.reglement_credits_ids: #Régelement credit
        #    total_reg_credit=total_reg_credit+ reg_credit.montant
        self.diff = total_paiement - total_produit_vendu + total_bon_commande - total_service_vendu + total_depense - total_reg_credit

    @api.multi
    @api.onchange("station_id")
    def onchange_station_id(self):
        #print("POMPES -------------------")

        if not self.station_id:
            return
        res = {}
        self.pricelist_id = self.station_id.pricelist_id.id
        #recette_non_valide = self.env['petrol.station.recette'].search([('valide', '=', False)])
        #if len(recette_non_valide) > 0:
        #    raise UserError("une recette est encours")
        # set defaults pompes
        pompes = self.env['petrol.station.pompe'].search([('station_id', '=', self.station_id.id)])
        if len(pompes) > 0:
            print("POMPES -------------------")
            volumcompteur_line = []
            for pompe in pompes:
                products = self.env['product.pricelist.item'].search(
                    [ ('date_start', '<=', self.date_recette),('date_end', '>=', self.date_recette), ('pricelist_id', '=', self.pricelist_id.id),
                     ('product_tmpl_id', '=', pompe.product_id.id)], limit=1, order="date_start desc, id desc")
                if products:
                    prix_unitaire = products[0].fixed_price
                else:
                    raise UserError(
                        "2vous devez vérifier votre listes de prix pour le produit %s" % pompe.product_id.name)
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
        print("reservoirs",reservoirs)
        if len(reservoirs) > 0:
            stock_line = []

            for reservoir in reservoirs:
                products = self.env['product.pricelist.item'].search(
                    [('date_start', '<=', self.date_recette),('date_end', '>=', self.date_recette),  ('pricelist_id', '=', self.pricelist_id.id),
                     ('product_tmpl_id', '=', reservoir.product_id.id)], limit=1, order="date_start desc, id desc")
                if products:
                    prix_unitaire = products[0].fixed_price
                else:
                    raise UserError(
                        "3vous devez vérifier votre listes de prix pour le produit %s %s %s" % (
                        reservoir.product_id.name, reservoir.recette_id.date_recette, reservoir.recette_id.station_id.name)
                    )
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

    def action_suivant(self):

        if self.state == "volumeconteur":
            self.state = 'stock'
            return True
        if self.state == "stock":
            self.state = 'boncommande'
            return True
        if self.state == "boncommande":
            self.state = 'paiement'
            return True
        if self.state == "paiement":
            self.state = 'depense'
            return True
        if self.state == "depense":
            self.state = 'vente_service'
            return True
        if self.state == "vente_service":
            self.state = 'regement_credits'
            return True
        if self.state == "regement_credits":
            return True

    def action_avant(self):
        if self.state == "volumeconteur":
            return True
        if self.state == "stock":
            self.state = 'volumeconteur'
            return True
        if self.state == "boncommande":
            self.state = 'stock'
            return True
        if self.state == "paiement":
            self.state = 'boncommande'
            return True
        if self.state == "depense":
            self.state = 'paiement'
            return True
        if self.state == "vente_service":
            self.state = "depense"
            return True
        if self.state == "regement_credits":
            self.state = "vente_service"
            return True
   

    def action_cloturer_recette_station(self):

        #             if self.cloture==True:
        #                 raise UserError("La recette est déjà cloturée!!!")
        #
        #             if self.valide!=True:
        #                 raise UserError("Vous devez valider la journée avant!!!")
        #             elif self.diff!=0:
        #                 raise UserError("Vérifier votre recette !!!!!!")
        #             else:
        if self.valide != True:
          raise UserError("Vous devez valider la journée avant!!!")
        config = self.env.ref('petrol_station_doosys.petrol_station_confi_global')
        non_cloture = self.env['petrol.station.recette'].search_count([('date_recette', '>',config.date_limit_cloture),('date_recette','<',self.date_recette),('station_id','=',self.station_id.id),('cloture','=',False)])
        if non_cloture:
          raise UserError("Vous devez clôturer les recettes précédentes !!!!")
        if self.volumconteur_ids:
            """ stock    
            """

            for stock in self.stock_ids:
                partner_id = self.station_id.client_comptant_id  # self.env['res.partner'].search([('name','=','stock public')],limit=1)
                if not partner_id:
                    raise UserError("vous devez créer cleint au comptant")
                #picking_count = False
                if stock.entree > 0:
                    ###########################entree#########################""
                    location_dest_id1 = stock.reservoir_id.location_id
                    stock_move_entree = self.env['stock.move'].search_count(
                        [('recette_id', '=', self.id), ('name', '=', str(stock.recette_id.name) + str(stock.reservoir_id.name) + 'Entree')])


                    if not stock_move_entree:
                        picking2 = self.env['stock.picking'].sudo().create({
                            'location_id': self.env.ref('stock.stock_location_suppliers').id,
                            'location_dest_id': location_dest_id1.id,
                            'partner_id': partner_id.id,
                            'picking_type_id': self.env.ref('stock.picking_type_in').id,
                            'recette_id': self.id,
                            'station_id': self.station_id.id,

                        })
                        # move from shelf1
                        move2 = self.env['stock.move'].sudo().create({
                            'name': str(stock.recette_id.name) + str(stock.reservoir_id.name) + 'Entree',
                            'location_id': self.env.ref('stock.stock_location_suppliers').id,
                            'location_dest_id': location_dest_id1.id,
                            'picking_id': picking2.id,
                            'product_id': stock.reservoir_id.product_id.id,
                            'product_uom': stock.reservoir_id.product_id.uom_id.id,
                            'product_uom_qty': stock.entree,
                            'recette_id': self.id,
                            'station_id': self.station_id.id,
                        })

                        picking2.action_confirm()
                        picking2.action_assign()
                        """values = {
                            'move_id': move2.id,
                            'product_id': move2.product_id.id,
    
                            'product_uom_id': move2.product_uom.id,
                            'location_id': move2.location_id.id,
                            'location_dest_id': move2.location_dest_id.id,
                        }
                        values.update({
                            'qty_done': int(stock.entree),
    
                        })
                        move_line_ids = self.env['stock.move.line'].create(values)"""
                        move2.move_line_ids.qty_done = int(stock.entree)
                        move2.move_line_ids.n_bl = str(stock.n_bl)

                        print("move2", stock.entree, stock.reservoir_id.product_id)
                        picking2.action_done()
                if stock.sortie > 0:
                    # ##########################sortie#########################""
                    #                         tranf_interne_id= self.env['stock.picking.type'].search([('name','=','Internal Transfers')],limit=1)
                    location_dest_id = self.env['stock.location'].search([('name', '=', 'transit')], limit=1)
                    if not location_dest_id:
                        raise UserError("vous devez créer un emplacement de stock avec le nom transit")

                    stock_move_sortie = self.env['stock.move'].search_count(
                        [('recette_id', '=', self.id), ('name', '=', str(stock.recette_id.name) + str(stock.reservoir_id.name) + 'Sortie')])

                    if not stock_move_sortie:
                        picking = self.env['stock.picking'].sudo().create({
                            'location_id': stock.reservoir_id.location_id.id,
                            'location_dest_id': location_dest_id.id,
                            'partner_id': partner_id.id,
                            'picking_type_id': self.env.ref('stock.picking_type_internal').id,
                            'recette_id': self.id,
                            'station_id': self.station_id.id,


                        })
                        # move from shelf1
                        print("c " + stock.reservoir_id.product_id.name, stock.sortie)
                        move1 = self.env['stock.move'].sudo().create({
                            'name': str(stock.recette_id.name) + str(stock.reservoir_id.name) + 'Sortie',
                            'location_id': stock.reservoir_id.location_id.id,
                            'location_dest_id': location_dest_id.id,
                            'picking_id': picking.id,
                            'product_id': stock.reservoir_id.product_id.id,
                            'product_uom': stock.reservoir_id.product_id.uom_id.id,
                            'product_uom_qty': stock.sortie,
                            'recette_id': self.id,
                            'station_id': self.station_id.id,
                        })
                        picking.action_confirm()
                        picking.action_assign()

                        # if move1.move_line_ids:
                        values = {
                            'move_id': move1.id,
                            'product_id': move1.product_id.id,
                            'n_bl': stock.n_bl,
                            'product_uom_id': move1.product_uom.id,
                            'location_id': move1.location_id.id,
                            'location_dest_id': move1.location_dest_id.id,

                        }
                        values.update({
                            'qty_done': int(stock.sortie),

                        })
                        move_line_ids = self.env['stock.move.line'].sudo().create(values)
                        print("move1.move_line_ids", move1.move_line_ids)
                        # if move1.move_line_ids:
                        # move1.move_line_ids.qty_done =  int(stock.sortie) if   int(stock.sortie)  else  0
                        # print("move1",move1,move1.move_line_ids,move1.move_line_ids.qty_done)
                        # print("cc usf " + stock.reservoir_id.product_id.name, stock.sortie,move1.move_line_ids.qty_done)
                        picking.action_done()

            """ Objet standards pour: crédit cient : générer bon de commande + Bon de livraion """
            credit_client_flux_automatique_id = self.env['sale.workflow.process'].search(
                [('name', '=', 'Automatic crédit cient')], limit=1)
            if not credit_client_flux_automatique_id:
                raise UserError("vous devez créer un workflow automatic  de stock avec le nom Automatic crédit cient")
            if credit_client_flux_automatique_id:
                workflow_process_id_cmd = credit_client_flux_automatique_id.id
            else:
                workflow_process_id_cmd = False

            for bncommande in self.boncommande_ids:
                # I create a sales order
                if bncommande.recette_id and bncommande.product_id:
                    if not bncommande.client_id:
                        raise UserError("Merci de saisir les clients de votre onglet crédit client")
                    products = self.env['product.pricelist.item'].search(
                        [('date_start', '<=', bncommande.recette_id.date_recette),
                          ('date_end','>=',bncommande.recette_id.date_recette),
                         ('pricelist_id', '=', bncommande.recette_id.pricelist_id.id)
                            , ('product_tmpl_id', '=', bncommande.product_id.id)], limit=1,
                        order="date_start desc, id desc")

                    if products and products[0].fixed_price != 0:
                        prix_unitaire = products[0].fixed_price
                        if not bncommande.sale_order_id:
                            bncommande.sale_order_id = self.env['sale.order'].sudo().create({
                                'partner_id': bncommande.client_id.id,
                                'recette_id': bncommande.recette_id.id,
                                'workflow_process_id': workflow_process_id_cmd,
                                'note': 'Invoice after delivery',
                                'station_id': self.station_id.id,


                            })
                            # In the sales order I add some sales order lines. i choose event product
                            self.env['sale.order.line'].sudo().create({
                                'product_id': bncommande.product_id.id,
                                'recette_id': bncommande.recette_id.id,
                                'price_unit': prix_unitaire,
                                'product_uom': bncommande.product_id.uom_id.id,
                                'product_uom_qty': (bncommande.montant / prix_unitaire),
                                'order_id': bncommande.sale_order_id.id,
                                'name': bncommande.product_id.name,
                            })
                    else:
                        raise UserError(
                            "4vous devez vérifier votre listes de prix pour le produit %s" % bncommande.product_id.name)

            """ Objet standards pour: recette
            *pour espèce, chèque, TPE: générer bon de commande + Bon de livraion + Facture + payement
            *pour Bon, vignette, carte: générer bon de commande + Bon de livraion"""

            for recette in self.paiement_ids:
                # I create a sales order

                if str(recette.type_paiement_id.name) != 'Chèque' and str(
                        recette.type_paiement_id.name) != 'CARTE CMI' and str(
                        recette.type_paiement_id.name) != 'Espèces':
                    if not recette.product_id:
                        raise UserError("Merci de saisir les produits de votre onglet recette ")
                    if not recette.client_id1:
                        raise UserError("Merci de saisir les clients de votre onglet recette" + self.date_recette+ self.station_id.name+str(self.id))
                    if recette.recette_id and recette.product_id:
                        products = self.env['product.pricelist.item'].search(
                            [ ('date_start', '<=', recette.recette_id.date_recette),
                              ('date_end','>=',recette.recette_id.date_recette),
                             ('pricelist_id', '=', recette.recette_id.pricelist_id.id)
                                , ('product_tmpl_id', '=', recette.product_id.id)], limit=1,
                            order="date_start desc, id desc")
                        if products and products[0].fixed_price != 0:
                            prix_unitaire = products[0].fixed_price
                            print("usf automatique_flux", recette.type_paiement_id.name,
                                  recette.type_paiement_id.automatique_flux)
                            if recette.type_paiement_id.automatique_flux == 'all_flux':
                                recette_flux_automatique_id = self.env['sale.workflow.process'].search([('name', '=',
                                                                                                         'Automatic recette bon de commande + Bon de livraion + Facture + payement')],
                                                                                                       limit=1)
                                if not recette_flux_automatique_id:
                                    raise UserError(
                                        "Merci de saisir le workflow Automatic recette bon de commande + Bon de livraion + Facture + payement")
                                recette_payment_mode = self.env['account.payment.mode'].search([('name', '=',
                                                                                                 'Automatic recette bon de commande + Bon de livraion + Facture + payement')],
                                                                                               limit=1)
                                if not recette_payment_mode:
                                    raise UserError(
                                        "Merci de saisir le mode de payement Automatic recette bon de commande + Bon de livraion + Facture + payement")
                                if recette_payment_mode:
                                    recette_payment_mode_id = recette_payment_mode.id
                                else:
                                    recette_payment_mode_id = False

                            elif recette.type_paiement_id.automatique_flux == 'commande_livraison':
                                recette_flux_automatique_id = self.env['sale.workflow.process'].search(
                                    [('name', '=', 'Automatic recette bon de commande + Bon de livraion')], limit=1)
                                recette_payment_mode_id = False
                            if recette_flux_automatique_id:
                                workflow_process_id = recette_flux_automatique_id.id
                            else:
                                workflow_process_id = False
                            if not recette.sale_order_paiement_id:
                                recette.sale_order_paiement_id = self.env['sale.order'].sudo().create({
                                    'partner_id': recette.client_id1.id,
                                    'recette_id': recette.recette_id.id,
                                    'station_id': self.station_id.id,
                                    'workflow_process_id': workflow_process_id,
                                    'payment_mode_id': recette_payment_mode_id,
                                    "type_payement": recette.type_paiement_id.name,
                                    'note': '',
                                })
                                # In the sales order I add some sales order lines. i choose event product
                                self.env['sale.order.line'].sudo().create({
                                    'product_id': recette.product_id.id,
                                    'recette_id': recette.recette_id.id,
                                    'price_unit': prix_unitaire,
                                    'product_uom': recette.product_id.uom_id.id,
                                    'product_uom_qty': recette.montant / prix_unitaire,  # recette.qt,
                                    # 'price_subtotal':recette.amount_net,
                                    'order_id': recette.sale_order_paiement_id.id,
                                    'name': recette.product_id.name,
                                })

                                if recette.commission:
                                    recette_payment_mode = self.env['account.payment.mode'].search([('name', '=',
                                                                                                     'Automatic recette bon de commande + Bon de livraion + Facture + payement')],
                                                                                                   limit=1)
                                    payment_comm = self.env['account.payment'].sudo().create({
                                        'type_payement': 'Espèces',
                                        'station_id': self.station_id.id,
                                        'payment_method_id': self.env.ref('account.account_payment_method_manual_in').id,
                                        'recette_id': recette.recette_id.id,
                                        'partner_type': 'customer',
                                        'partner_id': recette.client_id1.id,
                                        'amount_rec': recette.commission,
                                        'amount': recette.commission,
                                        'journal_id': recette_payment_mode.fixed_journal_id.id,
                                        'payment_date': recette.recette_id.date_recette,
                                        'payment_type': 'inbound',
                                        'communication': 'Commission: ' + recette.client_id1.name
                                    })
                                    payment_comm.post()

                        else:
                            raise UserError(
                                "5vous devez vérifier votre listes de prix pour le produit %s %s %s" % (
                                    recette.product_id.name, self.date_recette,
                                    self.station_id.name) )

            ###############################facture reste stock avec trois paiement TPE espece cheque ##############
            print("AUTOMATIQUE FLUX AFTER")
            if self.paiement_ids:

                #                     recette_flux_automatique_id= self.env['sale.workflow.process'].search([('name','=','Automatic recette bon de commande + Bon de livraion + Facture + payement')],limit=1)
                recette_payment_mode = self.env['account.payment.mode'].search(
                    [('name', '=', 'Automatic recette bon de commande + Bon de livraion + Facture + payement')],
                    limit=1)
                partner_id = self.station_id.client_comptant_id  # self.env['res.partner'].search([('name','=','stock public')],limit=1)
                print("self.paiement_ids", self.paiement_ids)
                if not partner_id:
                    raise UserError("vous devez créer cleint au comptant")
                if not recette_payment_mode:
                    raise UserError(
                        "Merci de saisir le mode de payement Automatic recette bon de commande + Bon de livraion + Facture + payement")
                if recette_payment_mode:
                    recette_payment_mode_id = recette_payment_mode.id
                else:
                    recette_payment_mode_id = False
                product_carburant_ids = self.env['product.product'].search([('categ_id', 'ilike', 'Carburant')])
                order_reste_stock  = self.env['sale.order'].search_count([('recette_id','=',self.id),('partner_id','=',partner_id.id)])
                if not order_reste_stock:
                    sale_order_paiement_id = self.env['sale.order'].sudo().create({
                        'partner_id': partner_id.id,
                        'recette_id': self.id,
                        #                       'workflow_process_id': recette_flux_automatique_id.id,
                        'payment_mode_id': recette_payment_mode_id,
                        'station_id': self.station_id.id,
                        'note': '',
                    })
                    transit_location_id = self.env['stock.location'].search([('name', '=', 'transit')], limit=1)

                    for product_carburant in product_carburant_ids:
                        quantite_a_livree = 0
                        products = self.env['product.pricelist.item'].search(
                            [ ('date_start', '<=', self.date_recette),
                             ('date_end','>=',self.date_recette),
                             ('pricelist_id', '=', self.pricelist_id.id)
                                , ('product_tmpl_id', '=', product_carburant.id)], limit=1,
                            order="date_start desc, id desc")

                        if products and products[0].fixed_price != 0:
                            prix_unitaire = products[0].fixed_price

                            for recette in self.paiement_ids:
                                print("recette", recette, recette.type_paiement_id.name, recette.qt, recette.product_id.id,
                                      product_carburant.id)
                                if str(recette.type_paiement_id.name) != 'Chèque' and str(
                                        recette.type_paiement_id.name) != 'CARTE CMI' and str(
                                        recette.type_paiement_id.name) != 'Espèces':
                                    if recette.product_id.id == product_carburant.id:
                                        quantite_a_livree = quantite_a_livree + recette.qt
                            print("product_carburant", product_carburant.name, quantite_a_livree)
                            for credit_client in self.boncommande_ids:
                                if credit_client.product_id.id == product_carburant.id:
                                    quantite_a_livree = quantite_a_livree + credit_client.qt
                            available_qty = self.env['stock.quant']._get_available_quantity(product_carburant,
                                                                                            transit_location_id,
                                                                                            strict=True)
                            print("available_qty : ",available_qty,product_carburant.name,transit_location_id.name)
                            print("qte available_qty", available_qty)
                            available_qty = available_qty - quantite_a_livree
                            print("qt", available_qty, quantite_a_livree)
                            print('product Name', product_carburant.name)
                            print('product qttt', quantite_a_livree)
                            if available_qty > 0:
                                self.env['sale.order.line'].sudo().create({
                                    'product_id': product_carburant.id,
                                    'recette_id': self.id,
                                    'price_unit': prix_unitaire,
                                    'product_uom': product_carburant.uom_id.id,
                                    'product_uom_qty': available_qty,
                                    'order_id': sale_order_paiement_id.id,
                                    'name': product_carburant.name,
                                })

                            # else:
                            #    raise UserError(
                            #        "y a pas de recette pour  le produit %s" % product_carburant.name)



                        else:
                            raise UserError(
                                "vous devez vérifier votre listes de prix pour le produit %s %s %s" % (
                                    product_carburant.name, self.date_recette,
                                    self.station_id.name))


                    sale_order_paiement_id.action_confirm()
                    if sale_order_paiement_id.picking_ids:
                        picking = sale_order_paiement_id.picking_ids[0]
                        picking.location_id = transit_location_id
                        picking.action_confirm()
                        picking.action_assign()
                        for move1 in picking.move_lines:
                            #                               move1 = picking.move_lines[0]
                            move1.move_line_ids.qty_done = move1.product_uom_qty
                        #                                 move1.location_id = transit_location_id
                        #                                 move1.qty_done = move1.product_uom_qty
                        picking.action_done()

                    # for product_carburant in product_carburant_ids:
                    #     quants = self.env['stock.quant']._gather(product_carburant, transit_location_id)
                    #     if quants:
                    #         quants.sudo().unlink()

                    payment = self.env['sale.advance.payment.inv'].sudo().create(
                        {'advance_payment_method': 'all'})
                    print("sale_order_paiement_id", sale_order_paiement_id, sale_order_paiement_id.order_line)
                    if sale_order_paiement_id.order_line:
                        payment.with_context(active_ids=sale_order_paiement_id.ids).create_invoices()
                        invoice = sale_order_paiement_id.invoice_ids[0]
                        invoice.action_invoice_open()
                        sale_order_paiement_id.action_done()
                        partner_type = invoice.type in ('out_invoice', 'out_refund') and \
                                       'customer' or 'supplier'
                        with savepoint(self.env.cr):
                            payment_espece = self.env['account.payment'].sudo().create({
                                'invoice_ids': [(6, 0, invoice.ids)],
                                'amount': self.cuve_espece,
                                'payment_date': fields.Date.context_today(self),
                                'communication': invoice.reference or invoice.number,
                                'partner_id': partner_id.id,
                                'partner_type': 'customer',
                                'payment_type': 'inbound',
                                'payment_method_id': self.env.ref('account.account_payment_method_manual_in').id,
                                'type_payement': "Espèces",
                                'journal_id': recette_payment_mode.fixed_journal_id.id,
                                'station_id': self.station_id.id,
                                'recette_id': self.id,
                            })
                            print("payment_espece")
                            print({
                                'invoice_ids': [(6, 0, invoice.ids)],
                                'amount': self.cuve_espece,
                                'payment_date': fields.Date.context_today(self),
                                'communication': invoice.reference or invoice.number,
                                'partner_id': partner_id.id,
                                'partner_type': 'customer',
                                'payment_type': 'inbound',
                                'payment_method_id': invoice.payment_mode_id.payment_method_id.id,
                                'type_payement': "Espèces",
                                'journal_id': recette_payment_mode.fixed_journal_id.id,
                                'station_id': self.station_id.id,
                                'recette_id': self.id,
                            })
                            payment_espece.post()
                        #                         for l in payment_espece.move_line_ids:
                        #                             invoice.register_payment(l)
                        with savepoint(self.env.cr):
                            payment_cheque = self.env['account.payment'].sudo().create({'payment_type': 'inbound',
                                                                                        'payment_method_id': self.env.ref(
                                                                                            'account.account_payment_method_manual_in').id,
                                                                                        'partner_type': 'customer',
                                                                                        'partner_id': partner_id.id,
                                                                                        'invoice_ids': [
                                                                                            (6, 0, invoice.ids)],
                                                                                        'amount': self.cuve_cheque,
                                                                                        'payment_date': fields.Date.context_today(
                                                                                            self),
                                                                                        'journal_id': recette_payment_mode.fixed_journal_id.id,
                                                                                        'type_payement': "Chèque",
                                                                                        'station_id': self.station_id.id,
                                                                                        'recette_id': self.id,

                                                                                        })
                            payment_cheque.post()
                        #                         for l in payment_cheque.move_line_ids:
                        #                             invoice.register_payment(l)
                        with savepoint(self.env.cr):
                            payment_tpe = self.env['account.payment'].sudo().create({'payment_type': 'inbound',
                                                                                     'payment_method_id': self.env.ref(
                                                                                         'account.account_payment_method_manual_in').id,
                                                                                     'partner_type': 'customer',
                                                                                     'partner_id': partner_id.id,
                                                                                     'invoice_ids': [(6, 0, invoice.ids)],
                                                                                     'amount': self.cuve_tpe,
                                                                                     'payment_date': fields.Date.context_today(
                                                                                         self),
                                                                                     'journal_id': recette_payment_mode.fixed_journal_id.id,
                                                                                     'type_payement': "CARTE CMI",
                                                                                     'station_id': self.station_id.id,
                                                                                     'recette_id': self.id,
                                                                                     })
                            payment_tpe.post()
                #                         for l in payment_tpe.move_line_ids:
                #                             invoice.register_payment(l)

            """ Objet standards pour: vente & service
            * Générer bon de commande + Bon de livraion + Facture + payement"""
            """vente_service_flux_automatique_id= self.env['sale.workflow.process'].search([('name','=','Automatic vente service')],limit=1)
            v_s_payment_mode= self.env['account.payment.mode'].search([('name','=','Automatic vente service')],limit=1)
            if v_s_payment_mode:
                v_s_payment_mode_id= v_s_payment_mode.id
            else:
                v_s_payment_mode_id=False

            if vente_service_flux_automatique_id:
                workflow_process_id_vente= vente_service_flux_automatique_id.id
            else:
                workflow_process_id_vente= False"""
            v_s_payment_mode = self.env['account.payment.mode'].search([('name', '=', 'Automatic vente service')],
                                                                       limit=1)
            if v_s_payment_mode:
                v_s_payment_mode_id = v_s_payment_mode.id
            else:
                v_s_payment_mode_id = False
            for vente in self.vente_service_ids:
                if not vente.sale_order_id:
                    if vente.type_paiement_id.automatique_flux == 'all_flux':
                        recette_flux_automatique_id = self.env['sale.workflow.process'].search(
                            [('name', '=', 'Automatic recette bon de commande + Bon de livraion + Facture + payement')],
                            limit=1)
                        if not recette_payment_mode:
                            raise UserError(
                                "Merci de saisir le mode de payement Automatic recette bon de commande + Bon de livraion + Facture + payement")
                        if recette_payment_mode:
                            recette_payment_mode_id = recette_payment_mode.id
                        else:
                            recette_payment_mode_id = False
                    elif vente.type_paiement_id.automatique_flux == 'commande_livraison':
                        recette_flux_automatique_id = self.env['sale.workflow.process'].search(
                            [('name', '=', 'Automatic recette bon de commande + Bon de livraion')], limit=1)
                        recette_payment_mode_id = False
                    if recette_flux_automatique_id:
                        workflow_process_id = recette_flux_automatique_id.id
                    else:
                        workflow_process_id = False
                        # I create a sales order
                        partner_id = self.station_id.client_comptant_id  # self.env['res.partner'].search([('name','=','Ventes Public')])
                    if not partner_id:
                        raise UserError("vous devez créer cleint au comptant")
                    if partner_id:
                        vente.sale_order_id = self.env['sale.order'].sudo().create({
                            'partner_id': partner_id.id,
                            'recette_id': vente.recette_id.id,
                            'workflow_process_id': workflow_process_id,
                            'payment_mode_id': v_s_payment_mode_id,
                            'note': '',
                            'type_payement': vente.type_paiement_id.name,
                            'station_id': self.station_id.id,
                        })
                        # In the sales order I add some sales order lines. i choose event product
                        self.env['sale.order.line'].sudo().create({
                            'product_id': vente.produit_id.id,
                            'price_unit': vente.montant,
                            'recette_id': vente.recette_id.id,
                            'product_uom': vente.produit_id.uom_id.id,
                            'product_uom_qty': 1,
                            'order_id': vente.sale_order_id.id,
                            'name': vente.produit_id.name,
                        })
            """ Objet standards pour: dépense
            * Générer bon d'achat+ Bon de livraion + Facture + payement
                """
            for depense in self.depense_ids:
                # I create a sales order
                if not depense.purchase_order_id:
                    partner_id = self.station_id.client_comptant_id  # self.env['res.partner'].search([('name','=','Dépenses Public')],limit=1)
                    if not partner_id:
                        raise UserError("vous  devez créer cleint au comptant")
                    if partner_id:
                        depense.purchase_order_id = self.env['purchase.order'].sudo().create({
                            'partner_id': partner_id.id,
                            'recette_id': depense.recette_id.id,
                            'station_id': self.station_id.id,
                        })
                        # In the sales order I add some sales order lines. i choose event product
                        self.env['purchase.order.line'].sudo().create({
                            'product_id': depense.produit_id.id,
                            'recette_id': depense.recette_id.id,
                            'price_unit': depense.montant,
                            'product_uom': depense.produit_id.uom_id.id,
                            'product_qty': 1,
                            'order_id': depense.purchase_order_id.id,
                            'date_planned': fields.Datetime.now(),
                            'name': 'Purchases order line',
                        })
                        depense.purchase_order_id.button_confirm()
                        if depense.purchase_order_id.picking_ids:
                            picking = depense.purchase_order_id.picking_ids[0]
                            picking.action_confirm()
                            picking.action_assign()
                            move1 = picking.move_lines[0]
                            move1.move_line_ids.qty_done = 1
                            picking.action_done()
                        recette_payment_mode = self.env['account.payment.mode'].search(
                            [('name', '=', 'Automatic purchase')], limit=1)
                        if recette_payment_mode:
                            recette_payment_mode_id = recette_payment_mode.id
                        else:
                            recette_payment_mode_id = False

                        # Should be changed by automatic on_change later

                        invoice_account = self.env['account.account'].search(
                            [('user_type_id', '=', self.env.ref('account.data_account_type_receivable').id)], limit=1).id
                        invoice_line_account = self.env['account.account'].search(
                            [('user_type_id', '=', self.env.ref('account.data_account_type_expenses').id)], limit=1).id

                        invoice = self.env['account.invoice'].sudo().create({'partner_id': partner_id.id,
                                                                             'account_id': invoice_account,
                                                                             'type': 'in_invoice',
                                                                             'purchase_id': depense.purchase_order_id.id,
                                                                             'payment_mode_id': recette_payment_mode.id,
                                                                             'station_id': self.station_id.id,

                                                                             })

                        self.env['account.invoice.line'].sudo().create({'product_id': depense.produit_id.id,
                                                                        'quantity': 1.0,
                                                                        'price_unit': depense.montant,
                                                                        'invoice_id': invoice.id,
                                                                        'name': 'product that cost 100',
                                                                        'account_id': invoice_line_account,
                                                                        'invoice_line_tax_ids': False,
                                                                        'purchase_id': depense.purchase_order_id.id,
                                                                        })
                        invoice.action_invoice_open()

                        partner_type = invoice.type in ('out_invoice', 'out_refund') and \
                                       'customer' or 'supplier'
                        payment_mode = invoice.payment_mode_id

                        with savepoint(self.env.cr):
                            payment = self.env['account.payment'].sudo().create({
                                'invoice_ids': [(6, 0, invoice.ids)],
                                'amount': invoice.residual,
                                'payment_date': fields.Date.context_today(self),
                                'communication': invoice.reference or invoice.number,
                                'partner_id': invoice.partner_id.id,
                                'partner_type': partner_type,
                                'payment_type': payment_mode.payment_type,
                                'payment_method_id': payment_mode.payment_method_id.id,
                                'journal_id': payment_mode.fixed_journal_id.id,
                            })
                            payment.post()

            self.cloture = True

    def action_validate_recette_station(self):
        if self.valide == True:
            raise UserError("La recette est déjà validée!!!")
        total_bon_commande = 0
        for bncommande in self.boncommande_ids:  # Crédit client
            total_bon_commande = total_bon_commande + bncommande.montant
        total_paiement = 0
        
        for paiement in self.paiement_ids:  # Recette
            total_paiement = total_paiement + paiement.montant
        total_produit_vendu = 0
        for volumconteur in self.volumconteur_ids:  # VoluCompteur
            if volumconteur.compteur2 >= volumconteur.compteur1:
                total_produit_vendu = total_produit_vendu +  volumconteur.ca_sortie

        total_service_vendu = 0
        for vente in self.vente_service_ids:
            if str(vente.type_paiement_id.name) == 'Espèces':  # vente
                total_service_vendu = total_service_vendu + vente.montant
        total_depense = 0
        for depense in self.depense_ids:
            if str(depense.type_paiement_id.name) == 'Espèces':  # Depense
                total_depense = total_depense + depense.montant
        total_reg_credit = 0
        for reg_credit in self.reglement_credits_ids:  # Régelement credit
            total_reg_credit = total_reg_credit + reg_credit.montant
        diff = total_paiement - total_produit_vendu + total_bon_commande - total_service_vendu + total_depense
        print("diff", self.diff)
        if self.diff <= 10 and self.diff >= -10:
            for stock in self.stock_ids:
                if stock.stock_physique == 0:
                    raise UserError("vous devez saisir le stock physique!!!")

            for volumcompt in self.volumconteur_ids:
                if volumcompt.compteur2 == 0:
                    raise UserError("vous devez saisir le compteur final Volume compteur!!!")

            self.valide = True
            for volumconteur in self.volumconteur_ids:
                volumconteur.pompe_id.compteur = volumconteur.compteur2
            for stock in self.stock_ids:
                stock.reservoir_id.stock_initiale = stock.stock_physique
            for credit in self.boncommande_ids:
                credit.client_id.solde_client = credit.client_id.solde_client + credit.montant
            for reg_credit in self.reglement_credits_ids:
                reg_credit.client_id.solde_client = reg_credit.client_id.solde_client - reg_credit.montant
        else:
            document_has_attachement = self.sudo().env['ir.attachment'].search(
                [('res_model', '=', 'petrol.station.recette'), ('res_id', '=', self.id)])
            if not document_has_attachement or self.justifier_ecart == False:
                raise UserError("Vérifier votre recette ou justifier votre recette !!!")
            else:
                for stock in self.stock_ids:
                    if stock.stock_physique == 0:
                        raise UserError("vous devez saisir le stock physique!!!")
                for volumconteur in self.volumconteur_ids:
                    if volumconteur.compteur2 == 0:
                        raise UserError("vous devez Compteur Final des volume compteur!!!")
                self.valide = True
                for volumconteur in self.volumconteur_ids:
                    volumconteur.pompe_id.compteur = volumconteur.compteur2
                for stock in self.stock_ids:
                    stock.reservoir_id.stock_initiale = stock.stock_physique
                for credit in self.boncommande_ids:
                    credit.client_id.solde_client = credit.client_id.solde_client + credit.montant
                for reg_credit in self.reglement_credits_ids:
                    reg_credit.client_id.solde_client = reg_credit.client_id.solde_client - reg_credit.montant
        
        for k,v in check_plafond.items():
            check_plafond[k] = [0]

        for k,v in check_paiement.items():
            check_paiement[k] = [0]

    @api.model
    def default_get(self, fields):

        recette_non_valide = self.env['petrol.station.recette'].search([('valide', '=', False)])
        # if len(recette_non_valide)>0 and fields['is_central']:
        #    raise UserError("une recette est encours")
        res = super(petrol_station_recette, self).default_get(fields)
        return res

    #     @api.multi
    #     def write(self, vals):
    #         if self.cloture==True:
    #             raise UserError("Vous pouvez pas modifier une recette cloturée !!!!!!")
    #         res = super(petrol_station_recette , self).write(vals)
    #         return res
    @api.multi
    def write(self, vals):
        # if self.cloture==True and not vals.get('cloture_center_ok'):
        #    raise UserError("Vous pouvez pas modifier une recette cloturée !!!!!!")
        for rec in self:
            if rec.cloture == False and rec.valide == True:
                if not self.env.user.has_group('petrol_station_doosys.group_station_petrol_manager'):
                    raise UserError('Vous pouvez pas modifier une recette validée, vous devez contacter votre manager')
        res = super(petrol_station_recette, self).write(vals)
        
        return res


class petrol_station_velumcompteur(models.Model):
    _name = 'petrol.station.volumcomteur'
    name = fields.Char(string="name")
    pompe_id = fields.Many2one('petrol.station.pompe', string="Pompe", readonly=True)
    product_id = fields.Many2one('product.product', string="Produit", readonly=True)
    compteur1 = fields.Float(string="Compteur Initial", readonly=True)
    compteur2 = fields.Float(string="Compteur Final", required=True)
    hs = fields.Boolean(string="HS")
    recette_id = fields.Many2one('petrol.station.recette', string="Recette")
    valide = fields.Boolean("Valide" , compute="_valide", store=True)
    cloture = fields.Boolean(string="clotûre", compute="_valide", store=True)
    sortie = fields.Float(string="Sortie", compute="calcule_sorite")
    ca_sortie = fields.Float(string="CA", compute="calcule_sorite")
    prix_unitaire = fields.Float(string="Prix Unitaire")
    bloquage = fields.Boolean(String="Bloque")
    ca_sortie2 = fields.Float(string="CA")
    compteur2_bloquage = fields.Float(string="Compteur Final 2", required=True)



    @api.multi
    @api.depends("recette_id","recette_id.valide","recette_id.cloture")
    def  _valide(self):
        for rec in self:
            if rec.recette_id:
                rec.valide = rec.recette_id.valide
                rec.cloture = rec.recette_id.cloture



    @api.model
    def create(self, vals):
        vals['bloquage'] = self.env['petrol.station.pompe'].search([('id','=',vals['pompe_id'])])[0].bloquage
        print(self.compteur2_bloquage)
        print(vals)
        if self.hs == True:
            vals['compteur2'] = vals['compteur1']
        if self.bloquage == True:
            vals['compteur2'] = self.compteur2_bloquage

        return super(petrol_station_velumcompteur, self).create(vals)

    @api.multi
    def write(self, vals):
        print("vals usf", vals)
        
        if 'hs' in vals:
            if vals['hs'] == True:
                if 'compteur1' in vals:
                    vals['compteur2'] = vals['compteur1']
        # if self.bloquage == True:
        #     vals['compteur2'] = self.compteur2_bloquage

        return super(petrol_station_velumcompteur, self).write(vals)

    @api.onchange('pompe_id')
    def onchange_pompe_id(self):
        self.product_id = self.pompe_id.product_id.id
        self.compteur1 = self.pompe_id.compteur

    @api.onchange('hs')
    def onchange_hs(self):
        if self.hs == True:
            self.compteur2 = self.compteur1

    @api.onchange('ca_sortie')
    def onchange_ca(self):
        if self.bloquage == False:
            self.compteur2 = (self.ca_sortie / self.prix_unitaire) + self.compteur1
        else:
            
            sortie_tmp = (self.compteur2 - self.compteur1) * self.prix_unitaire

            print(sortie_tmp)
            print(self.ca_sortie)

            if(sortie_tmp <= self.ca_sortie):
                self.ca_sortie2 = self.ca_sortie
            else:
                print("kkk")
                raise UserError("Chiffre d'affaire doit être  supérieur ou égal")



    @api.onchange('compteur2')
    def onchange_compteur22(self):
        if self.bloquage == True:
            self.compteur2_bloquage = self.compteur2



    @api.multi
    @api.depends('compteur2', 'prix_unitaire')
    def calcule_sorite(self):
        for volume in self:
            sortie = volume.compteur2 - volume.compteur1

            if volume.compteur2 > 0:
                if sortie < 0:
                    raise UserError("Compteur final doit être  supérieur ou égal au compteur initial station" + str(
                        volume.recette_id.station_id.name) + ' pomp' + str(volume.pompe_id.name))
                else:
                    if(volume.bloquage == False):
                        volume.sortie = sortie
                        volume.ca_sortie = volume.sortie * volume.prix_unitaire
                    else:
                        volume.sortie = sortie
                        volume.ca_sortie = volume.ca_sortie2
                        volume.compteur2 = volume.compteur2_bloquage
                




class petrol_station_boncommande(models.Model):
    _name = 'petrol.station.boncommande'
    name = fields.Char(string="name")
    client_id = fields.Many2one('res.partner', string="Client", required=True,
                                domain="[('code_sap','!=',False),('customer','=',True),('type_paiement','=',False),('plafond','>',0.00),('reste','>',0.00)]")
    solde_client = fields.Float(string="Solde en cours", compute="_client_id"  )
    reste = fields.Float(string="Reliquat", compute="_client_id" )
    plafond = fields.Float(string="Plafond mensuel  ",compute="_client_id" )
    vehicule = fields.Char(string="Véhicule (option)")
    product_id = fields.Many2one('product.product', string="Produit", required=True,
                                 domain="[('sale_ok','=',True),('categ_id','ilike','Carburant')]")
    ref = fields.Char(string="Référence")
    montant = fields.Float(string="Montant", required=True)
    facture = fields.Boolean(string="facturé", default=False)
    recette_id = fields.Many2one('petrol.station.recette', string="Recette")
    valide = fields.Boolean("Valide" , compute="_valide", store=True)
    cloture = fields.Boolean(string="clotûre", compute="_valide", store=True)
    station_id = fields.Many2one(related="recette_id.station_id", string="Station")
    sale_order_id = fields.Many2one('sale.order', string="Sale order")
    qt = fields.Float(string="Quantité:")

    check_plafond = {}

    @api.multi
    def _recette_id(self):
        for rec in self:
            if rec.recette_id:
                rec.station_id = rec.recette_id.station_id    
    
    @api.multi
    @api.depends("client_id")
    def _client_id(self):
        for rec in self:
            if rec.client_id:
                count_solde = sum([v[0] for k,v in check_plafond.items() if '-'+str(rec.client_id.id) in k])
                if(rec.create_date):
                    rec.qt = 0
                    rec.solde_client = rec.client_id.solde_client + count_solde
                    rec.reste = rec.client_id.plafond - count_solde
                    rec.plafond = rec.client_id.plafond
                    rec.montant = 0
                    

                    for k,v in check_plafond.items():
                        if('-'+str(rec.create_date) in k):
                            check_plafond[k] = [0]

                    rec.create_date = False

                else:
                    rec.solde_client = rec.client_id.solde_client + count_solde
                    rec.reste = rec.client_id.plafond - rec.solde_client
                    rec.plafond = rec.client_id.plafond
                


    
    @api.multi
    @api.depends("recette_id","recette_id.valide","recette_id.cloture")
    def _valide(self):
        for rec in self:
            if rec.recette_id:
                rec.valide = rec.recette_id.valide
                rec.cloture = rec.recette_id.cloture


    @api.onchange('product_id', 'montant')
    def onchange_product_montant(self):
        if self.recette_id and self.product_id:
            products = self.env['product.pricelist.item'].search(
                [ ('date_start', '<=', self.recette_id.date_recette),
                 ('date_end','>=',self.recette_id.date_recette),
                 ('pricelist_id', '=', self.recette_id.pricelist_id.id)
                    , ('product_tmpl_id', '=', self.product_id.id)], limit=1, order="date_start desc, id desc")
            if products:
                prix_unitaire = products[0].fixed_price
            else:
                raise UserError(
                    "6vous devez vérifier votre listes de prix pour le produit %s %s %s" % (
                        self.product_id.name, self.recette_id.date_recette,
                        self.recette_id.station_id.name))
            if self.product_id and prix_unitaire != 0 and self.montant:
                self.qt = self.montant / prix_unitaire
    

    @api.multi
    @api.onchange('product_id', 'qt')
    def onchange_product_qt(self):
        if self.recette_id and self.product_id:
            products = self.env['product.pricelist.item'].search(
                [ ('date_start', '<=', self.recette_id.date_recette),
                  ('date_end','>=',self.recette_id.date_recette),
                 ('pricelist_id', '=', self.recette_id.pricelist_id.id)
                    , ('product_tmpl_id', '=', self.product_id.id)], limit=1, order="date_start desc, id desc")
            if products:
                prix_unitaire = products[0].fixed_price
            else:
                raise UserError(
                    "7vous devez vérifier votre listes de prix pour le produit %s %s %s" % (
                        self.product_id.name, self.recette_id.date_recette,
                        self.recette_id.station_id.name) )
            if self.product_id and prix_unitaire != 0 and self.qt and self.client_id:
                now = datetime.datetime.now()
                if(self.cloture == False):
                    if(self.create_date):
                        i = '-'+str(self.client_id.id) +'-'+ str(self.create_date)
                        count_solde = sum([v[0] for k,v in check_plafond.items() if '-'+str(self.client_id.id) in k]) - float(check_plafond[i][0])  + (self.qt * prix_unitaire)
                        if(count_solde + self.client_id.solde_client <= self.client_id.plafond):
                            self.montant = self.qt * prix_unitaire
                            self.solde_client = self.client_id.solde_client  + count_solde
                            self.reste = self.client_id.plafond - self.solde_client
                            check_plafond[i] = [self.qt * prix_unitaire]
                            # raise Warning("Le reliquat pour le client "+str(self.client_id.name)+" est "+str(self.reste))
                        else:
                            self.qt = 0
                            raise UserError("Vous avez depasser le solde")
                    else:
                        count_solde = sum([v[0] for k,v in check_plafond.items() if '-'+str(self.client_id.id) in k]) + self.qt * prix_unitaire
                        if(self.client_id.solde_client + count_solde <= self.client_id.plafond):
                            # raise Warning("Le reliquat pour le client "+str(self.client_id.name)+" est "+str(self.reste))

                            self.solde_client = self.client_id.solde_client + count_solde
                            self.reste = self.client_id.plafond - self.solde_client
                            self.montant = self.qt * prix_unitaire
                            self.create_date = now 
                            check_plafond['-'+str(self.client_id.id) +'-'+ str(now.replace(microsecond=0))] = [self.montant]
                        else:
                            self.qt = 0
                            raise UserError("Vous avez depasser le solde")


class petrol_station_paiement(models.Model):
    _name = 'petrol.station.paiement'
    name = fields.Char(string="name")
    type_paiement_id = fields.Many2one('type.paiement', string="Type de paiement", required=True)
    moyen_paiement_id = fields.Many2one('petrol.station.moyen.paiement', string="Moyen de paiement", required=True)
    refacture = fields.Boolean( string="facturé",compute='_type_paiement_id_related' , default=False, store=True)
    type_client = fields.Selection([
        ('banque', 'Banque'),
        ('confrere', 'Confrère'),
        ('espece', 'Espècce'),
    ], string='Type', compute='_type_paiement_id_related', readonly=True)
    client_id = fields.Many2one('res.partner', string="partenaire", required=True,
                                domain="[('customer','=',True),('type_paiement','=',type_client),('supplier','=',True)]")
    client_id1 = fields.Many2one('res.partner', string="Client",
                                 domain="[('code_sap','!=',False),('customer','=',True),('type_paiement','=',False)]")
    ref = fields.Char(string="Référence(option)")
    montant = fields.Float(string="Montant", required=True)
    solde_client = fields.Float(string="Solde à payer", compute="_solde_client")
    recette_id = fields.Many2one('petrol.station.recette', string="Recette paiement")


    valide = fields.Boolean("Valide", compute="_valide", store=True)
    cloture = fields.Boolean(string="clotûre", compute="_valide", store=True)
    station_id = fields.Many2one("petrol.station",string="Station", compute="_station_id")
    recette_reglement_credits_id = fields.Many2one('petrol.station.recette', string="Recette réglement crédit")
    date_recette = fields.Date(string='Date',
                               readonly=False, index=True,
                               help="Date de paiement", default=lambda self: date.today())
    product_id = fields.Many2one('product.product', string="Produit",
                                 domain="[('sale_ok','=',True),('categ_id','ilike','Carburant')]")
    km = fields.Float(string="kilométrage")
    qt = fields.Float(string="Quantité:")
    objet_regelement = fields.Text('objet du règlement')
    req_produit_rec = fields.Boolean( string="produit obligatoire recette  ", compute='_type_paiement_id_related',
                                     default=False)
    req_km_rec = fields.Boolean( string="kilométrage: obligatoire recette",compute='_type_paiement_id_related',
                                default=False)
    req_ref_rec = fields.Boolean( string="référence obligatoire recette",compute='_type_paiement_id_related',
                                 default=False)
    req_client_rec = fields.Boolean( string="Client obligatoire recette",compute='_type_paiement_id_related',
                                    default=False)
    sale_order_paiement_id = fields.Many2one('sale.order', 'Sale Order')
    # depense_id  = fields.Many2one("petrol.station.depense",string="Dépense" )
    commission = fields.Float(string="Commission", readonly=False)
    amount_net = fields.Float(string="Net", readonly=True,compute="changforcommission")
    qte_net = fields.Float(string="Net" ,compute="changforcommission")
    solde_client = fields.Float(string="Solde en cours", compute="_client_id")
    reste = fields.Float(string="Reliquat", compute="_client_id")
    plafond = fields.Float(string="Plafond mensuel ", compute="_client_id")
    check_paiement = {}

    _sql_constraints = [
        ('num_ref_type_paiement_uniq', 'CHECK(1=1)', 'Référence dois être unique par type de paiement'),
        ('num_ref_moyen_paiement_partenaire_uniq', 'CHECK(1=1)',
         'Référence dois être unique par rapport a un partenaire par mode de paiement'),
    ]

    @api.multi
    @api.depends("client_id")
    def _solde_client(self):
        for rec in self:
            if rec.client_id:
                rec.solde_client = rec.client_id.solde_client


    @api.multi
    @api.onchange("client_id1")
    def _client_id(self):
        for rec in self:
            if rec.client_id1:
                if rec.moyen_paiement_id.id == 20:
                    if(rec.create_date):
                        rec.montant = 0
                        rec.commission = 0
                        
                        for k,v in check_paiement.items():
                            if('-'+str(rec.create_date) in k):
                                check_paiement[k] = [0]
                        rec.create_date = False
                    else:
                        count_solde = sum([v[0] for k,v in check_paiement.items() if '-'+str(self.client_id1.id) in k]) + rec.montant
                        if(rec.client_id1.solde_client + count_solde <= rec.client_id1.plafond):
                            now = datetime.datetime.now()
                            rec.create_date = now 
                            check_paiement['-'+str(self.client_id1.id) +'-'+ str(now.replace(microsecond=0))] = [rec.montant]
                        else:
                            raise UserError("Solde insuffisant pour le client. \nLe client lui reste :" + str(rec.client_id1.plafond - sum([v[0] for k,v in check_paiement.items() if '-'+str(rec.client_id1.id) in k])))
               
                
                
    @api.multi
    @api.onchange("moyen_paiement_id")
    def _change_paiement(self):
        for rec in self:
            if rec.client_id1:
                if rec.moyen_paiement_id.id == 20:
                    now = datetime.datetime.now()
                    # if(rec.create_date):
                    #     now = datetime.datetime.now()
                    #     i = '-'+str(rec.client_id1.id) +'-'+ str(rec.create_date)
                    #     count_solde = sum([v[0] for k,v in check_paiement.items() if '-'+str(rec.client_id1.id) in k]) - float(check_paiement[i][0])  + rec.montant
                    #     if(rec.client_id1.solde_client + count_solde <= rec.client_id1.plafond):
                    #         rec.create_date = now 
                    #         check_paiement['-'+str(self.client_id1.id) +'-'+ str(now.replace(microsecond=0))] = [rec.montant]
                    #     else:
                    #         raise UserError("Solde insuffisant pour le client. \nLe solde actuel du client est :" + str(count_solde + rec.client_id1.solde_client))
                    # else:
                    count_solde = sum([v[0] for k,v in check_paiement.items() if '-'+str(rec.client_id1.id) in k]) + rec.montant
                    if(rec.client_id1.solde_client + count_solde <= rec.client_id1.plafond):
                        rec.create_date = now 
                        check_paiement['-'+str(self.client_id1.id) +'-'+ str(now.replace(microsecond=0))] = [rec.montant]
                    else:
                        raise UserError("Solde insuffisant pour le client. \nLe client lui reste :" + str(rec.client_id1.plafond - sum([v[0] for k,v in check_paiement.items() if '-'+str(rec.client_id1.id) in k])))
                else:
                    if(rec.create_date):
                        for k,v in check_paiement.items():
                            if('-'+str(rec.create_date) in k):
                                check_paiement[k] = [0]





    @api.multi
    @api.onchange("montant")
    def _change_montant(self):
        for rec in self:
            if rec.client_id1:
                if rec.moyen_paiement_id.id == 20:
                    now = datetime.datetime.now()
                    if(rec.create_date):
                        i = '-'+str(rec.client_id1.id) +'-'+ str(rec.create_date)
                        count_solde = sum([v[0] for k,v in check_paiement.items() if '-'+str(rec.client_id1.id) in k]) - float(check_paiement[i][0])  + rec.montant
                        if(rec.client_id1.solde_client + count_solde <= rec.client_id1.plafond):
                            rec.create_date = now 
                            check_paiement['-'+str(self.client_id1.id) +'-'+ str(now.replace(microsecond=0))] = [rec.montant]
                        else:
                            raise UserError("Solde insuffisant pour le client. \nLe client lui reste :" + str(rec.client_id1.plafond - sum([v[0] for k,v in check_paiement.items() if '-'+str(rec.client_id1.id) in k])))
                    else:
                        count_solde = sum([v[0] for k,v in check_paiement.items() if '-'+str(rec.client_id1.id) in k]) + rec.montant
                        if(rec.client_id1.solde_client + count_solde <= rec.client_id1.plafond):
                            rec.create_date = now 
                            check_paiement['-'+str(self.client_id1.id) +'-'+ str(now.replace(microsecond=0))] = [rec.montant]
                        else:
                            raise UserError("Solde insuffisant pour le client. \nLe client lui reste :" + str(rec.client_id1.plafond - sum([v[0] for k,v in check_paiement.items() if '-'+str(rec.client_id1.id) in k])))









    @api.multi
    @api.depends("recette_id","recette_reglement_credits_id")
    def _station_id(self):
        for rec in self:
            if rec.recette_id:
                rec.station_id = rec.recette_id.station_id
            elif rec.recette_reglement_credits_id :
                rec.station_id = rec.recette_reglement_credits_id.station_id


    @api.multi
    @api.depends("client_id")
    def _solde_client(self):
        for rec in self:
            if rec.client_id:
                rec.solde_client = rec.client_id.solde_client



    @api.multi
    @api.depends("type_paiement_id","type_paiement_id.refacture")
    def _type_paiement_id_related(self):
        for rec in self:
            if rec.type_paiement_id:
                rec.type_client  = rec.type_paiement_id.type
                rec.refacture  = rec.type_paiement_id.refacture
                rec.req_produit_rec = rec.type_paiement_id.req_produit_rec
                rec.req_km_rec = rec.type_paiement_id.req_km_rec
                rec.req_ref_rec = rec.type_paiement_id.req_ref_rec
                rec.req_client_rec = rec.type_paiement_id.req_client_rec



    @api.multi
    @api.depends("recette_id","recette_id.valide","recette_id.cloture","recette_reglement_credits_id","recette_reglement_credits_id.cloture")
    def _valide(self):
        print("_valide paiement")
        for rec in self:
            if rec.recette_id:
                rec.valide = rec.recette_id.valide
                rec.cloture = rec.recette_id.cloture
            elif rec.recette_reglement_credits_id:
                rec.valide = rec.recette_reglement_credits_id.valide
                rec.cloture = rec.recette_reglement_credits_id.cloture





    @api.multi
    def write(self, vals):
        print("write paiement")
        res = super(petrol_station_paiement, self).write(vals)

        if vals.get("commission"):
            if 1 == 1:
                # self.commission = self.client_id.commission / 100 * self.montant
                self.amount_net = self.montant - self.commission
                print("commission : ",self.amount_net,self.montant)

            else:
                self.amount_net = self.montant

        # self._depense_id()
        return res

    #@api.onchange("montant", "client_id", "commission")
    @api.multi
    @api.depends("montant","commission")
    def changforcommission(self):

        for rec in self:
            if rec.montant and rec.client_id:
                if rec.client_id.commission > 0 or rec.commission:
                    # self.commission = self.client_id.commission / 100 * self.montant
                    rec.amount_net = rec.montant - rec.commission

                else:
                    rec.amount_net = rec.montant
                rec.onchange_product_montant()

    @api.onchange('client_id')
    def change_client_id(self):

        if self.client_id:
            if self.client_id.commission:
                self.client_id1 = self.client_id
            if self.client_id.facturable:

                if self.station_id.bon_drh_client_id:
                    self.client_id1 = self.station_id.bon_drh_client_id
                else:
                    self.client_id1 = self.client_id

    def _depense_id(self):
        print("EEEE", self)

        if self.type_paiement_id and self.type_paiement_id.type == "confrere":
            value = {
                'produit_id': self.recette_id.station_id.comission_product_id and self.recette_id.station_id.comission_product_id.id or False,
                'montant': self.montant * self.client_id1.commission / 100,
                'qt': self.client_id1.commission / 100,
                'recette_id': self.recette_id.id,
                'type_paiement_id': self.type_paiement_id.id,
                'detail': "Commission : " + str(self.client_id1.name)
            }
            if not self.depense_id.id:
                print("333", self.depense_id.id, self.client_id1.name)
                self.depense_id = self.env['petrol.station.depense'].create(value)

            else:
                self.depense_id.write(value)
        else:

            obj = self.search([('id', '=', self.id)])
            if obj.depense_id.id:
                print("33334", obj.depense_id)
                obj.depense_id.unlink()
                print("5555", obj.depense_id)



    @api.onchange('moyen_paiement_id')
    def onchange_moyen_paiement_id(self):
        # if(self.moyen_paiement_id.id == 20):
        #     if(self.create_date):
        #         for rec in self:
                               
        #             rec.create_date = False
        #             rec.qt = 0
        #             rec.montant = 0
        #             rec.commission = 0
                
        #             for k,v in check_paiement.items():
        #                 if('-'+str(self.create_date) in k):
        #                     check_paiement[k] = [0]

        self.type_paiement_id = self.moyen_paiement_id.type_paiement_id.id
        self.client_id = self.moyen_paiement_id.client_id.id
                
                
                
       

    @api.onchange('product_id', 'montant')
    def onchange_product_montant(self):
        #print("onchange_product_montant paiement")
        if self.recette_id and self.product_id:
            products = self.env['product.pricelist.item'].search(
                [('date_start', '<=', self.recette_id.date_recette),
                 ('date_end','>=',self.recette_id.date_recette),
                 ('pricelist_id', '=', self.recette_id.pricelist_id.id)
                    , ('product_tmpl_id', '=', self.product_id.id)], limit=1, order="date_start desc, id desc")

            if products:
                prix_unitaire = products[0].fixed_price
            else:
                raise UserError(
                    "8vous devez vérifier votre listes de prix pour le produit %s %s %s" % (self.product_id.name,self.recette_id.date_recette, self.recette_id.station_id.name))
            if self.product_id and prix_unitaire != 0 and self.montant:
                self.qt = self.montant / prix_unitaire
                if self.amount_net and self.amount_net != self.montant :
                    self.qte_net = self.amount_net / prix_unitaire
                else:
                    self.qte_net = self.qt


    @api.onchange('product_id', 'qt')
    def onchange_product_qt(self):
        print("onchange_product_qt paiement")
        if self.recette_id and self.product_id:
            products = self.env['product.pricelist.item'].search(
                [ ('date_start', '<=', self.recette_id.date_recette),
               ('date_end','>=',self.recette_id.date_recette),
                 ('pricelist_id', '=', self.recette_id.pricelist_id.id)
                    , ('product_tmpl_id', '=', self.product_id.id)], limit=1, order="date_start desc, id desc")
            if products:
                prix_unitaire = products[0].fixed_price
            else:
                raise UserError("1vous devez vérifier votre listes de prix pour le produit %s %s %s" % (self.product_id.name,self.recette_id.date_recette, self.recette_id.station_id.name))
            if self.product_id and prix_unitaire != 0 and self.qt:
                self.montant = self.qt * prix_unitaire




class petrol_station_depense(models.Model):
    _name = 'petrol.station.depense'
    name = fields.Char(string="name")
    produit_id = fields.Many2one('product.product', string="Detail (produit)", required=True,
                                 domain="[('purchase_ok','=',True),('categ_id','ilike','Depense')]")
    montant = fields.Float(string="Montant", required=True)
    qt = fields.Float(string="Quantité:")
    recette_id = fields.Many2one('petrol.station.recette', string="Recette")
    valide = fields.Boolean("Valide" , compute="_valide", store=True)
    cloture = fields.Boolean(string="clotûre", compute="_valide", store=True)
    detail = fields.Text(string="Détail")
    type_paiement_id = fields.Many2one('type.paiement', string="Type de paiement", required=True)

    @api.multi
    @api.depends("recette_id","recette_id.valide")
    def _valide(self):
        for rec in self:
            if rec.recette_id:
                rec.valide = rec.recette_id.valide
                rec.cloture = rec.recette_id.cloture

    @api.onchange('produit_id', 'montant')
    def onchange_product_montant(self):
        if self.produit_id and self.produit_id.lst_price and self.montant:
            self.qt = self.montant / self.produit_id.lst_price

    @api.onchange('produit_id', 'qt')
    def onchange_product_qt(self):
        if self.produit_id and self.produit_id.lst_price and self.qt:
            self.montant = self.qt * self.produit_id.lst_price


class petrol_station_vente_service(models.Model):
    _name = 'petrol.station.vente.service'
    name = fields.Char(string="name")
    produit_id = fields.Many2one('product.product', string="Type", required=True,
                                 domain="[('sale_ok','=',True),('categ_id','ilike','Ventes et Sevices')]")
    montant = fields.Float(string="Total", required=True)
    qt = fields.Float(string="Quantité:")
    recette_id = fields.Many2one('petrol.station.recette', string="Recette")
    valide = fields.Boolean("Valide" , compute="_valide", store=True)
    cloture = fields.Boolean(string="clotûre", compute="_valide", store=True)
    sale_order_id = fields.Many2one('sale.order', 'Sale order')
    type_paiement_id = fields.Many2one('type.paiement', string="Type de paiement", required=True)

    @api.multi
    @api.depends("recette_id","recette_id.valide")
    def _valide(self):
        for rec in self:
            if rec.recette_id:
                rec.valide = rec.recette_id.valide
                rec.cloture = rec.recette_id.cloture

    @api.onchange('produit_id', 'montant')
    def onchange_product_montant(self):
        if self.produit_id and self.produit_id.lst_price and self.montant:
            self.qt = self.montant / self.produit_id.lst_price

    @api.onchange('produit_id', 'qt')
    def onchange_product_qt(self):

        if self.produit_id and self.produit_id.lst_price and self.qt:
            self.montant = self.qt * self.produit_id.lst_price


class petrol_station_reservoir(models.Model):
    _name = 'petrol.station.stock'
    name = fields.Char(string="name")
    reservoir_id = fields.Many2one('petrol.station.reservoir', string="Cuve", readonly=True)
    product_id = fields.Many2one('product.product', string="Produit", readonly=True)
    stock_initiale = fields.Float(string="Stock Initial", readonly=True)  # defaults
    sortie = fields.Float(string="Sortie")  # calculable
    sortie2 = fields.Float(string="Sortie", related='sortie', readonly=True)  # calculable
    entree = fields.Float(string="Entrées livraison")
    entree_remise = fields.Float(string="Entrées remise")
    n_bl = fields.Char(string="N°BL")
    stock_compatble = fields.Float(string="Stock Comptable", compute='calcule_comptable')
    stock_physique = fields.Float(string="Stock Physique  (jaugeage)")  # calculable
    prix_unitaire = fields.Float(string="Prix Unitaire")
    prix_cout = fields.Float( string="Prix Coût", compute="_prix_cout")
    cout_stock_compatble = fields.Float(compute="calcule_manquants_excedents", string="Coût Stock Comptable")
    cout_stock_physique = fields.Float(compute="calcule_manquants_excedents", string=" Coût Stock Physique")
    manquants_excedents = fields.Float(string="Manquants ou Excédents",
                                       compute="calcule_manquants_excedents")  # calculable
    cout_manquants_excedents = fields.Float(compute="calcule_manquants_excedents", string="Coût Manquants ou Excédents")

    recette_id = fields.Many2one('petrol.station.recette', string="Recette")
    valide = fields.Boolean("Valide" , compute="_valide", store=True)
    cloture = fields.Boolean(string="clotûre", compute="_valide", store=True)

    @api.multi
    @api.depends("product_id")
    def _prix_cout(self):
        for rec in self:
            if  rec.product_id:
                rec.prix_cout = rec.product_id.standard_price


    @api.multi
    @api.depends("recette_id","recette_id.valide","recette_id.cloture")
    def _valide(self):
        for rec in self:
            if rec.recette_id:
                rec.valide = rec.recette_id.valide
                rec.cloture = rec.recette_id.cloture

    @api.onchange("entree_remise")
    def change_recette(self):
        config = self.env.ref('petrol_station_doosys.petrol_station_confi_global')
        if self.entree_remise and self.entree_remise > config.entree_remise_max:
            raise UserError('le champ "Entrée remise" dépasse la quantité de '+str(config.entree_remise_max)+' L')

    @api.onchange('reservoir_id')
    def onchange_reservoir_id(self):
        self.product_id = self.reservoir_id.product_id.id
        self.stock_initiale = self.reservoir_id.stock_initiale

    @api.multi
    @api.depends('stock_initiale', 'sortie', 'entree', 'entree_remise')
    def calcule_comptable(self):
        for stock in self:
            stock.stock_compatble = stock.stock_initiale - stock.sortie + stock.entree + stock.entree_remise

    @api.multi
    @api.depends('stock_physique', 'stock_compatble')
    def calcule_manquants_excedents(self):
        for stock in self:
            stock.manquants_excedents = stock.stock_physique - stock.stock_compatble
            stock.cout_stock_compatble = stock.prix_cout * stock.stock_compatble
            stock.cout_stock_physique = stock.prix_cout * stock.stock_physique
            stock.cout_manquants_excedents = stock.prix_cout * stock.manquants_excedents


class station_config(models.Model):
    _name = 'petrol.station.config'

    name = fields.Char("configuration")
    entree_remise_max = fields.Float("Remise en cuve")
    date_limit_cloture = fields.Date("Date Limit de clotûre", default="2020-12-08")
    version =  fields.Float("Version")

    @api.model
    def before_import_partner_model(self):
        config = self.env.ref('petrol_station_doosys.petrol_station_confi_global')
        if not config.version or config.version < 13:
            config.version = 13
            partner_ids = self.env['res.partner'].search([])
            synchro_res_partner_id = self.env.ref("base_synchro.synchro_res_partner")
            synchro_res_partner_id.synchronize_date = False
            for partner_id in partner_ids:
                partner_id.station_ids = [(5, 0, 0)]

    @api.multi
    def before_import_partner(self):
        partner_ids = self.env['res.partner'].search([])
        synchro_res_partner_id = self.env.ref("base_synchro.synchro_res_partner")
        synchro_res_partner_id.synchronize_date= False
        for partner_id in partner_ids:
            partner_id.station_ids  = [(5, 0, 0)]

    @api.multi
    def update_clients(self):
        partner_ids = self.env['res.partner'].search([])
        for partner_id in partner_ids:
            partner_id.station_ids = [(6,0,[])]



class PeriodicCredit(models.Model):
    _name = 'periodic.credit'

    partner_id = fields.Many2one('res.partner',string="Client")
    date_begin = fields.Date(string='From')
    date_fin = fields.Date(string='To')
    total_credit = fields.Float(string="Total Crédit")


    def test(Self):
        print("")


    @api.model
    def calcul_total_credit(self):
        print("@@@@@@@########HELLO HELLO123456123")
        
        date = fields.date.today()
        first_date = date.replace(day=1)

        last_date = date.replace(day = calendar.monthrange(date.year,date.month)[1])

        path = os.path.dirname(os.path.realpath(__file__)) + "/test_plafond"

        # f = open(path, "w")
        # f.write("0")
        # f.close()


        f = open(path , "r")
        x = f.read()
        f.close()
        



        for partner in self.env['res.partner'].search([]):
            credit_ids = self.env['petrol.station.boncommande'].search([('client_id','=',partner.id),
                                                                        ('recette_id.date_recette','>=',first_date),
                                                                        ('recette_id.date_recette','<=',last_date)])
            total_credit = sum([line.montant for line in credit_ids])
            periodic_credit_id = self.env['periodic.credit'].search([('partner_id','=',partner.id),
                                                                     ('date_begin','=',first_date),
                                                                     ('date_fin','=',last_date)])


            if periodic_credit_id:
                periodic_credit_id.total_credit = total_credit
            else:
                periodic_credit_id = self.env['periodic.credit'].create({
                               'partner_id':partner.id,
                               'date_begin':first_date,
                               'date_fin': last_date,
                                'total_credit': total_credit,
                               'total_credit': 0,

                })
            if fields.date.today() == first_date or x =='0':
                partner.solde_client = 0
                partner.reste = 0
                partner.plafond = partner.plafond_sap

        f = open(path , "w")
        f.write("1")
        f.close()

        print("done")


    # @api.model
    # def calcul_total_credit(self):


    #     print("JJJJJJJJJJJ CREDIT CREIDT CREIDITIRMFOD< ########123")
    #     print(self.env['res.partner'].search([]))
    #     date = fields.date.today()
    #     first_date = date.replace(day=1)


    #     last_date = date.replace(month=date.month + 1, day=1) - timedelta(days=1)
    #     for partner in self.env['res.partner'].search([]):
    #         credit_ids = self.env['petrol.station.boncommande'].search([('client_id','=',partner.id),
    #                                                                     ('recette_id.date_recette','>=',first_date),
    #                                                                     ('recette_id.date_recette','<=',last_date)])
    #         total_credit = sum([line.montant for line in credit_ids])
    #         periodic_credit_id = self.env['periodic.credit'].search([('partner_id','=',partner.id),
    #                                                                  ('date_begin','=',first_date),
    #                                                                  ('date_fin','=',last_date)])


    #         print(periodic_credit_id) 


            # if periodic_credit_id:
            #     periodic_credit_id.total_credit = total_credit
            # else:
            #     periodic_credit_id = self.env['periodic.credit'].create({
            #                    'partner_id':partner.id,
            #                    'date_begin':first_date,
            #                    'date_fin': last_date,
            #                      'total_credit': total_credit,
            #                    'total_credit': 0,

            #     })
            # if fields.date.today() == test_date:

            #     partner.solde_client = 0
            #     partner.reste = 0
            #     partner.plafond = partner.plafond_sap