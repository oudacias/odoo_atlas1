import datetime
import json
import logging

from requests import HTTPError

from odoo import api, fields, models, _

import time
from odoo.exceptions import UserError, ValidationError
import requests

_logger = logging.getLogger(__name__)


class SapServer(models.Model):
    _name = "sap.server"

    base_url = fields.Char("Base url")
    companyDB = fields.Char("companyDB")
    password = fields.Char("Password")
    userName = fields.Char("userName")


class SapObjects(models.Model):
    _name = "sap.objects"
    _order = 'sequence'

    name = fields.Char(string="Titre")
    link_sap = fields.Char(string="lien sap")
    model_id = fields.Many2one('ir.model')
    type = fields.Selection([
        ('d', 'Télécharger'),
        ('u', 'Upload')
    ])
    line_ids = fields.One2many("sap.objects.line", "sap_object_id")
    date_last_synchro = fields.Datetime(string="Last Synchronisation")
    domain = fields.Char(string="domain", default="[]")
    active_field = fields.Boolean("Active Synchro", default=True)
    active = fields.Boolean(string="Active", default=True)
    is_ligne_price_list = fields.Boolean("is price list")
    filtre = fields.Char(string="Filtre")
    sequence = fields.Integer("sequence")

    @api.model
    def schedule_synchro(self):
        recs = self.search([('active_field', "=", True)])
        recs.sycnhro()

    def synchronisationAdd(self, url, headers, erreur, primare, line_ulti_ids, synchro_obj, obj, rec, base_url):
        error = ""
        try:

            url.replace('&&', '&')
            print(url)
            _logger.debug("url sap : %s ", url)
            req = requests.get(url, headers=headers, verify=False)
            # req.raise_for_status()
            constent = req.json()
            print("req", req.json())
        except Exception as err:
            add_data = req.json()
            print(add_data)
            error = ('Erreur : Login SAP'
                     )

        if constent.get("error"):
            error = ('Erreur :  %s'
                     % constent.get('error').get('message').get('value'))
        if error != "":
            erreur.append(error)
        print("erreurs : ", erreur)

        if constent.get('value'):
            _logger.debug("url sap value  : %s ", constent["value"])
            for value in constent["value"]:

                data = {}
                id_remote = value.get(primare)

                for line_id in line_ulti_ids:
                    if len(line_id.relation_id) > 0:
                        synchro_line_ids = synchro_obj.search(
                            [('remote', '=', value.get(primare)), ('sap_objet_id', '=', line_id.relation_id.id)])

                        if synchro_line_ids and synchro_line_ids[0]:
                            data.update({
                                line_id.field_name: synchro_line_ids[0].local
                            })
                        else:
                            erreur.append(_(
                                'id  %s  de champs  %s ce trouve pas.') % (
                                              value.get(primare), line_id.field_name))

                    elif line_id.default_value != False:
                        data.update({
                            line_id.field_name: line_id.default_value
                        })
                    else:
                        if value.get(line_id.field_name_sap) == 'tNO':
                            v = False
                        elif value.get(line_id.field_name_sap) == 'tYES':
                            v = True
                        else:
                            v = value.get(line_id.field_name_sap)
                        data.update({
                            line_id.field_name: v
                        })

                if rec.link_sap == "b1s/v1/BusinessPartners":
                    BPLID = [v['BPLID'] for v in value.get('BPBranchAssignment')]
                    station_ids = self.env['petrol.station'].search([('magasin_code', 'in', BPLID)])
                    data['station_ids'] = [(6, 0, station_ids.ids)]
                    print("station_ids", data)
                    # exit()
                synchro_ids = synchro_obj.search([('remote', '=', id_remote), ('sap_objet_id', '=', rec.id)])

                if synchro_ids and synchro_ids[0]:

                    local_id = synchro_ids[0].local
                    obj_id = obj.browse(local_id)

                    print("write1", data)

                    obj_id.write(data)
                else:

                    if rec.model_id.model == 'res.partner':

                        res = obj.name_search(
                            data['name'], [('code_sap', '=', id_remote)], 'like', 1)

                    else:

                        res = obj.name_search(
                            data['name'], [], 'like', 1)
                    res = res and res[0][0] or False

                    if res:
                        obj_id = obj.browse(res)
                        obj_id.write(data)
                        print("write2", data)
                    else:
                        print("create2", data)
                        obj_id = obj.create(
                            data
                        )

                    synchro_obj.create({
                        'date': time.strftime("%Y-%m-%d %H:%M:%S"),
                        'sap_objet_id': rec.id,
                        'local': obj_id.id,
                        'remote': id_remote
                    })

                if rec.is_ligne_price_list:
                    ItemPrices = value.get("ItemPrices")
                    for ItemPrice in ItemPrices:
                        data_price = {}
                        # get object synch pricelist
                        pricelist_syn_id = self.env["sap.objects"].search([('name', '=', 'List de prix')], limit=1)
                        # id price list local
                        synchro_list_id = synchro_obj.search(
                            [('remote', '=', ItemPrice.get('PriceList')),
                             ('sap_objet_id', '=', pricelist_syn_id.id)], limit=1)
                        print("synchro_list_id", synchro_list_id)
                        if not synchro_list_id:
                            continue

                        # id produit local
                        id_product = obj_id.id
                        # price local
                        pricelist_item_id = self.env['product.pricelist.item'].search(
                            [('pricelist_id', '=', synchro_list_id.local),
                             ('product_tmpl_id', '=', id_product)], order="id desc", limit=1)

                        # compare

                        if (not pricelist_item_id or pricelist_item_id.fixed_price != ItemPrice.get(
                                'Price')) and ItemPrice.get('Price'):
                            data.update({
                                'date_start': fields.Date().today(),

                                'pricelist_id': synchro_list_id.local,
                                'fixed_price': ItemPrice.get('Price'),
                                'product_id': id_product,
                                'product_tmpl_id': id_product,
                                'applied_on': '1_product',
                                'compute_price': 'fixed'
                            })
                            pricelist_item = self.env['product.pricelist.item'].create(
                                data
                            )

                        # add
                self._cr.commit()
            if constent.get('odata.nextLink'):
                self.synchronisationAdd(base_url + '' + constent.get('odata.nextLink'), headers, erreur, primare,
                                        line_ulti_ids, synchro_obj, obj, rec, base_url)
            rec.date_last_synchro = fields.Datetime().now()

        return erreur

    @api.multi
    def sycnhro(self):
        synchro_report_id = self.env['sap.synchro.report'].create({
            'report': ''
        })
        # test sans sap
        self.env['petrol.station.recette'].action_cloturer_recette_station_center()
        self.env['automatic.workflow.job'].run()
        
        server_id = self.env["sap.server"].search([], limit=1)

        base_url = server_id.base_url  # "https://37.187.134.37:50000"
        url_login = base_url + "/b1s/v1/Login"
        synchro_obj = self.env['sap.synchro.line']
        erreur = []
        # test sans sap
        try:
            data = {
                "CompanyDB": server_id.companyDB,  # "TEST_ESCAPADE",
                "Password": server_id.password,  # "skatys",
                "UserName": server_id.userName,  # "manager"
            }
            req = requests.post(url_login, data=json.dumps(data), verify=False)
            req.raise_for_status()
            login_data = req.json()




        except Exception as err:
            add_data = req.json()

            print(add_data)

            raise UserError('Erreur :  %s'

                            % add_data.get('error').get('message').get('value'))

        rec_downloads = self.env['sap.objects'].search([('type', '=', 'd'), ('active_field', '=', True)])
        for rec in rec_downloads:
            erreur_rec = []
            obj = self.env[rec.model_id.model]
            link_sap = rec.link_sap
            line_ids = rec.line_ids.filtered(lambda l: (l.field_name_sap != False))
            champs_lid = line_ids.mapped('field_name_sap')
            field_names = rec.line_ids.mapped('field_name')
            champs = ",".join(champs_lid)
            line_ulti_ids = rec.line_ids.filtered(lambda l: (l.primar == False))
            primare_list = rec.line_ids.filtered(lambda l: (l.primar == True))
            if primare_list:
                primare = primare_list[0].field_name_sap

            # test sans sap
            headers = {"Cookie": "B1SESSION=" + login_data['SessionId'] + "; ROUTEID=.node0"}
            if rec.type == "d":
                error = ""
                filtre = "$filter="
                if rec.date_last_synchro and rec.link_sap != "b1s/v1/PriceLists" and not rec.is_ligne_price_list:
                    # a ajouter updatedate
                    filtre += "(CreateDate ge '" + rec.date_last_synchro + "' or UpdateDate ge '" + rec.date_last_synchro + "')"
                if rec.filtre:
                    filtre += ' and ' + rec.filtre
                if filtre == "$filter=":
                    filtre = ''

                select = champs
                if rec.is_ligne_price_list:
                    select += ",ItemPrices"
                url = base_url + '/' + rec.link_sap + "?$select=" + select + "&" + filtre
                ##
                # test sans sap
                self.synchronisationAdd(url, headers, erreur, primare, line_ulti_ids, synchro_obj, obj, rec, base_url)

        rec_uploads = self.env['sap.objects'].search([('type', '=', 'u'), ('active_field', '=', True)])
        # Identification de recette à synchroniser: condition:
        # clôturée
        # non synchronisée
        # Date min ????
        config = self.env.ref('petrol_station_doosys.petrol_station_confi_global')
        recette_ids = self.env['petrol.station.recette'].search(
            [('cloture_center', '=', True), ('synchronisee', '=', False), ('station_recette_id2', '!=', 0),('volumconteur_ids','!=',False),('date_recette','>',config.date_synchonisation_sap),('date_recette', '<',config.date_end_synchonisation_sap),('station_id','in',config.station_ids.ids)], order='date_recette asc')

        _logger.debug("recettes a synchoniser %s  ", recette_ids.ids)


        # recette_ids  = self.env['petrol.station.recette'].search([('cloture_center','=',True),('station_recette_id2','!=',0),('id','=',2448)],order='date_recette asc')

        report_obj = self.env['recette.report']
        for recette_id in recette_ids:
            recette_non_cloture = self.env['petrol.station.recette'].search_count(
                [('station_id', '=', recette_id.id), ('date_recette', '<', recette_id.date_recette),
                 ('cloture_center', '=', False)])
            if recette_non_cloture:
                continue
            _logger.debug("recette a synchoniser %s  ", recette_id)
            report_id = report_obj.create({
                'recette_id': recette_id.id,
                'station_id': recette_id.station_id.id,
                'synchro_report_id': synchro_report_id.id
            })
            report = ""
            erreur = ""
            for rec in rec_uploads:
                _logger.debug("model a synchoniser %s  ", rec.model_id.model)
                erreur_rec = []
                report_rec = []
                obj = self.env[rec.model_id.model]
                link_sap = rec.link_sap
                line_ids = rec.line_ids.filtered(lambda l: (l.field_name_sap != False))
                champs_lid = line_ids.mapped('field_name_sap')
                field_names = rec.line_ids.mapped('field_name')
                champs = ",".join(champs_lid)
                line_ulti_ids = rec.line_ids.filtered(lambda l: (l.primar == False))
                primare_list = rec.line_ids.filtered(lambda l: (l.primar == True))
                if primare_list:
                    primare = primare_list[0].field_name_sap

                # test sans sap
                headers = {"Cookie": "B1SESSION=" + login_data['SessionId'] + "; ROUTEID=.node0"}
                dt = rec.date_last_synchro

                if 1==1:
                    if rec.model_id.model == 'petrol.station.recette':
                        domain = eval(rec.domain) + [('id', '=', recette_id.id)]
                    else:
                        domain = eval(rec.domain) + [('recette_id', '=', recette_id.id)]

                else:
                    domain = eval(rec.domain)
                obj_ids = obj.search(domain)
                print("obj_ids", domain, obj_ids)
                report_upload = '\nObject : ' + rec.name + ' --> '

                for obj_id in obj_ids:
                    error = ""
                    value = {}
                    synchro_ids = synchro_obj.search([('local', '=', obj_id.id), ('sap_objet_id', '=', rec.id)])
                    if synchro_ids and synchro_ids[0]:
                        print('upate')
                    else:
                        for line_id in line_ulti_ids:
                            # if y a des ligne de l'objec comme ligne factures
                            if len(line_id.one2many) > 0:
                                one2many_value = []
                                for obj_one_id in obj_id[line_id.field_name]:
                                    if rec.link_sap == "b1s/v1/InventoryGenEntries":
                                        print("obj_id : ", obj_one_id)
                                        obj_one_id['manquants_excedents']  = float("{:.2f}".format(obj_one_id['manquants_excedents'] )) 
                                        if obj_one_id['manquants_excedents'] <= 0:
                                            continue
                                          
                                    if rec.link_sap == "b1s/v1/InventoryGenExits":
                                        obj_one_id['manquants_excedents']  = float("{:.2f}".format(obj_one_id['manquants_excedents'] )) 
                                        if obj_one_id['manquants_excedents'] >= 0:
                                            continue
                                        else:
                                            obj_one_id['manquants_excedents'] = abs(obj_one_id['manquants_excedents'])
                                           
                                    
                                    one2many_item = {}
                                    print(obj_one_id)
                                    for line_one_id in line_id.one2many.line_ids:
                                        if len(line_one_id.relation_id) > 0:
                                            synchro__id = synchro_obj.search(
                                                [('local', '=', obj_one_id[line_one_id.field_name].id),
                                                 (
                                                     'sap_objet_id', '=', line_one_id.relation_id.id)],
                                                limit=1)
                                            if synchro__id.remote:
                                                one2many_item.update({
                                                    line_one_id.field_name_sap: synchro__id.remote
                                                })




                                        elif line_id.default_value:
                                            one2many_item.update({
                                                line_one_id.field_name_sap: line_one_id.default_value
                                            })
                                        else:
                                            one2many_item.update({
                                                line_one_id.field_name_sap: obj_one_id[line_one_id.field_name]
                                            })

                                    one2many_value.append(one2many_item)
                                # if Recette stock
                                if rec.link_sap == "b1s/v1/InventoryPostings":
                                    InventoryPostings = {}
                                    for one2many in one2many_value:
                                        if not InventoryPostings.get(one2many["ItemCode"]):
                                            InventoryPostings[one2many["ItemCode"]] = one2many
                                        else:
                                            InventoryPostings[one2many["ItemCode"]]['CountedQuantity'] += one2many[
                                                'CountedQuantity']
                                    one2many_value = []
                                    for key, value_one2man in InventoryPostings.items():
                                        one2many_value.append(value_one2man)

                                # if y  pas des lignes elements
                                if len(one2many_value) == 0:
                                    continue
                                    continue

                                value.update({
                                    line_id.field_name_sap: one2many_value
                                })

                            # if il est lier à u autre object
                            elif len(line_id.relation_id) > 0:
                                try:
                                    synchro__id = synchro_obj.search([('local', '=', obj_id[line_id.field_name].id),
                                                                      ('sap_objet_id', '=', line_id.relation_id.id)],
                                                                     limit=1)
                                except Exception as err:
                                    _logger.debug("synchro_obj.search :  %s   %s ", obj_id ,line_id.field_name, line_id.relation_id)
                                    raise UserError('Erreur :  %s' % erreur)
                                if synchro__id.remote:
                                    value.update({
                                        line_id.field_name_sap: synchro__id.remote
                                    })

                                else:
                                    """ value.update({
                                         line_id.field_name_sap: synchro__id.remote
                                     })
                                     value.append(str(0))"""
                            # if il a une valeur pre défini
                            elif line_id.default_value:
                                value.update({
                                    line_id.field_name_sap: line_id.default_value
                                })

                            else:
                                if (
                                        line_id.field_type == "char" or line_id.field_type == "date" or line_id.field_type == "datetime") and \
                                        obj_id[line_id.field_name]:
                                    value.update({
                                        line_id.field_name_sap: obj_id[line_id.field_name]
                                    })

                                else:
                                    value.update({
                                        line_id.field_name_sap: obj_id[line_id.field_name]
                                    })

                        if (
                                rec.link_sap == "b1s/v1/InventoryGenEntries" or rec.link_sap == "b1s/v1/InventoryGenExits") and len(
                                one2many_value) == 0:
                            continue
                        # if PAIEMENT
                        if rec.link_sap == "b1s/v1/IncomingPayments":

                            if not obj_id.amount or not obj_id.type_payement:
                                continue

                            compte_caisse = False
                            if obj_id.partner_id and obj_id.partner_id.commission:
                                compte_caisse = obj_id.station_id.compte_commission
                            if value.get("DocEntry"):
                                compte_caisse = obj_id.station_id.compte_caisse
                                PaymentInvoices = [{
                                    "InvoiceType": "it_Invoice",
                                    "DocEntry": value.get("DocEntry"),
                                    "SumApplied": obj_id.amount_rec
                                }]
                                if value.get("DocEntry"):
                                    del value["DocEntry"]
                                value.update({
                                    'PaymentInvoices': PaymentInvoices
                                })

                            if not compte_caisse:
                                continue

                            if obj_id.type_payement == "CARTE CMI" and obj_id.amount:
                                dat_now = datetime.datetime.now()
                                PaymentCreditCards = [{
                                    'CardValidUntil': str(dat_now.strftime("%Y-%m-%d")),
                                    'CreditCard': obj_id.station_id.cart_id,
                                    #'CreditCardNumber': 1,
                                    #'PaymentMethodCode': 1,
                                    'VoucherNum': 1,
                                    'CreditSum': obj_id.amount_rec,
                                }]
                                value.update({
                                    'PaymentCreditCards': PaymentCreditCards,
                                    'CashAccount': obj_id.station_id.compte_carte_credite,  # '51112000'
                                })
                            elif obj_id.type_payement == "Chèque" and obj_id.amount:
                                PaymentChecks = [{
                                    "CheckSum": obj_id.amount_rec,
                                }]
                                value.update({
                                    'PaymentChecks': PaymentChecks,
                                    'CashAccount': obj_id.station_id.compte_cheque  # '51112000'
                                })
                            elif obj_id.type_payement == "Espèces" and obj_id.amount:
                                value.update({
                                    'CashSum': obj_id.amount_rec,
                                    'CashAccount': compte_caisse  # '51611000'
                                })
                            print("PAIEMENT usf", obj_ids, obj_id.type_payement, value)
                        # commission
                        if rec.link_sap == "b1s/v1/CreditNotes":
                            AccountCode = "61473400"
                            if obj_id.client_id.name ==  "CLIENT TOTAL":
                                AccountCode = "61473300"
                            DocumentLines = [{
                                "ItemDescription": "Avoir financier du "+obj_id.recette_id.date_recette,
                                 "AccountCode": AccountCode,
                                 "LineTotal": obj_id.commission
                            }]
                            value.update({
                                'DocumentLines': DocumentLines
                            })
                        # if RECEPTION
                        if rec.link_sap == "b1s/v1/PurchaseDeliveryNotes":
                            DocumentLines = [{
                                'ItemCode': value.get('ItemCode'),
                                "Quantity": obj_id.entree
                            }]
                            if value.get('ItemCode'):
                                del value["ItemCode"]
                            value.update({
                                'DocumentLines': DocumentLines
                            })
                        # if Ecart
                        if rec.link_sap == "b1s/v1/JournalEntries":
                            JournalEntryLines = [
                                {
                                    "AccountCode": "61870000",
                                    "Credit": obj_id.amount_diff,
                                    "Debit": 0,
                                    "BPLID": obj_id.station_id.magasin_code
                                },
                                {
                                    "ShortName": obj_id.station_id.client_comptant_id.code_sap,
                                    "AccountCode": obj_id.station_id.compte_client_comptant,
                                    "Credit": 0,
                                    "Debit": obj_id.amount_diff,
                                    "BPLID": obj_id.station_id.magasin_code
                                }
                            ]
                            value.update({
                                'JournalEntryLines': JournalEntryLines
                            })

                        if len(value) > 0:
                            print(value)
                            # test sans sap
                            try:
                                url = base_url + '/' + rec.link_sap
                                print("usr usf", url, value)
                                # send data to SAP
                                req = requests.post(url, data=json.dumps(value), headers=headers, verify=False)
                                _logger.debug("req usf %s data : %s ", req, value)
                                print(req)
                                req.raise_for_status()
                                add_data = req.json()

                                id_remote = add_data.get(primare)
                                synchro_obj.create({
                                    'date': time.strftime("%Y-%m-%d %H:%M:%S"),
                                    'sap_objet_id': rec.id,
                                    'local': obj_id.id,
                                    'remote': id_remote
                                })

                                # if 'error' in add_data:
                                #    _logger.debug("data usf %s ", add_data)
                                #    error = ('Erreur : %s , %s' % (add_data.error.message.value,obj_id.name))





                            # except HTTPError as http_err:

                            #    print(f'HTTP error occurred: {http_err}')  # Python 3.6
                            # test sans sap
                            except Exception as err:

                                add_data = req.json()
                                _logger.debug("data usf %s ", add_data, rec, obj_id)

                                print(add_data)
                                error = ""
                                if (add_data.get('error')):
                                    error = ('Erreur ::  %s ==> %s  %s id : %s \n %s \n %s'
                                             % (
                                             add_data.get('error').get('message').get('value'), str(rec), str(obj_id),
                                             str(obj_id.id), str(rec.link_sap), str(value)))
                                    report_id.erreur = error         
                                report_id.state = 'erreur'
                                
                                report_id.report = report
                                self._cr.commit()

                                raise UserError('Erreur :  %s' % error)

                                # else :
                                #    error = 'Erreur '
                    self._cr.commit()
                    report_upload += str(obj_id.id) + ','

                    if error != "":
                        erreur_rec.append(error)

                if len(erreur_rec) == 0:
                    rec.date_last_synchro = fields.Datetime().now()
                    report += report_upload
                else:
                    erreur_rec.append('\n '.join(erreur_rec))
                    print("erreur_rec", erreur_rec)
                    erreur += '\n '.join(erreur_rec)
            report_id.report = report
            report_id.erreur = erreur
            if erreur != '':
                report_id.state = 'erreur'
                self._cr.commit()
                raise UserError('Erreur :  %s' % erreur)
            else:
                report_id.state = 'passe'
                recette_id.synchronisee = True

            self._cr.commit()

        print("erreur", erreur)
        str_erreur = erreur
        synchro_report_id.report = 'La synchronisation avec SAP est terminer \n ' + str(str_erreur)

        return erreur


class SapObjectsLine(models.Model):
    _name = "sap.objects.line"
    _order = "sequance"

    sap_object_id = fields.Many2one('sap.objects', string="Sap object")
    field_id = fields.Many2one('ir.model.fields', string="Field")
    field_name = fields.Char(related="field_id.name")
    field_type = fields.Selection(related="field_id.ttype")
    field_name_sap = fields.Char("Column name sap")
    relation_id = fields.Many2one("sap.objects", "Relation")
    default_value = fields.Char("Default value")
    sequance = fields.Integer("seaqunce")
    primar = fields.Boolean("primare")
    one2many = fields.Many2one("sap.objects", string="One2many")


class SapSynchroLine(models.Model):
    _name = "sap.synchro.line"

    date = fields.Datetime(string="date")
    sap_objet_id = fields.Many2one('sap.objects', string="Sap object")
    local = fields.Integer("local")
    remote = fields.Char("Remote")


class SapSynchroRport(models.Model):
    _name = "sap.synchro.report"

    date = fields.Datetime(string="Date", default=lambda self: fields.Datetime().now())
    report = fields.Text("Rapport")

