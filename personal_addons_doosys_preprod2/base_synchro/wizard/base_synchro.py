# See LICENSE file for full copyright and licensing details.

import logging
import time
import threading
from warnings import catch_warnings
from xmlrpc.client import ServerProxy
from odoo import http
from odoo import api, fields, models, _
from odoo.exceptions import Warning
import socket
from odoo.exceptions import AccessDenied
import requests
from uuid import getnode as get_mac

_logger = logging.getLogger(__name__)


class RPCProxyOne(object):

    def __init__(self, server, ressource):
        """Class to store one RPC proxy server."""
        self.server = server
        local_url = 'http://%s:%d/xmlrpc/common' % (server.server_url,
                                                    server.server_port)
        try:
            rpc = ServerProxy(local_url, allow_none=True)
            self.uid = rpc.login(server.server_db, server.login,
                                 server.password)
        except Exception as e:
            raise Warning(_(e))
        local_url = 'http://%s:%d/xmlrpc/object' % (server.server_url,
                                                    server.server_port)
        self.rpc = ServerProxy(local_url, allow_none=True)
        self.ressource = ressource

    def __getattr__(self, name):
        _logger.debug("__getattr__ usf %s)",
                      name)
        return lambda *args: self.rpc.execute(
            self.server.server_db, self.uid, self.server.password,
            self.ressource, name, *args)


class RPCProxy(object):

    def __init__(self, server):
        self.server = server

    def get(self, ressource):
        return RPCProxyOne(self.server, ressource)


class BaseSynchro(models.TransientModel):
    _name = 'base.synchro'
    _description = 'Base Synchronization'

    server_url = fields.Many2one('base.synchro.server', "Server URL",
                                 required=True)
    user_id = fields.Many2one('res.users', "Send Result To",
                              default=lambda self: self.env.user)
    message  = fields.Text('Message')


    #station_remote_id = fields.Integer(related="server_url.station_remote_id")

    report = []
    report_total = 0
    report_create = 0
    report_write = 0
    recette_add_ids = []
    recette_update_ids = []

    @api.model
    def synchronize(self, server, object):


        print("recette_add_ids 1",self.recette_add_ids)
        sync_ids = []
        pool1 = RPCProxy(server)
        pool2 = self
        dt = object.synchronize_date
        module = pool1.get('ir.module.module')
        model_obj = object.model_id.model
        avoid_field_list = [a.name for a in object.avoid_ids]
        station_remote_id = self.server_url.station_remote_id
        erreurs = []
        if module.search_count([("name", "ilike", "base_synchro"),
                                ('state', '=', 'installed')]) < 1:
            raise Warning(_('If your Synchronization direction is \
                          download and/or upload, please install \
                          "Multi-DB Synchronization" module in targeted \
                          server!'))
        if object.action in ('d', 'b'):


            sync_ids = pool1.get('base.synchro.obj').get_ids(
                model_obj, dt, eval(object.domain), {'action': 'd'})
        if object.action in ('u', 'b'):
            _logger.debug("Getting ids to synchronize [%s] (%s)",
                          object.synchronize_date, object.domain)

            sync_ids += pool2.env['base.synchro.obj'].get_ids(
                model_obj, dt, eval(object.domain), {'action': 'u'})
        print("get_ids : ",model_obj,object.domain,sync_ids)
        avoid_field_list += ['create_date', 'write_date']
        for dt, sync_id, action in sync_ids:
            print("sync_id usf",sync_id)
            destination_inverted = False
            if action == 'd':
                pool_src = pool1
                pool_dest = pool2
            else:
                pool_src = pool2
                pool_dest = pool1
                destination_inverted = True
            if not destination_inverted:
                try:
                    value = pool_src.get(object.model_id.model).search_read(
                        [('id', '=', sync_id)])[0]
                except Exception as e :
                        erreur = 'Erreur search : ' + str(e)
                        erreurs.append(erreur)
                        _logger.critical("Erreur search : " + str(e))
            else:
                pool = pool_src.env[object.model_id.model]
                value = pool.search_read([('id', '=', sync_id)])[0]


            field_vals = dict([(key, val[0] if isinstance(val, tuple)
                                else val) for key, val in filter(
                lambda i: i[0] not in avoid_field_list, value.items())])
            print("value usf 0 ", value)
            value = self.data_transform(
                pool_src, pool_dest, object.model_id.model, field_vals, action,
                destination_inverted, avoid_field_list)
            print("value usf 1abd ",value)
            id2 = self.get_id(object.id, sync_id, action)

            if id2:
                _logger.debug("Updating model %s [%d]", object.model_id.name,
                              id2)

                synchro_obj_line =  self.get_synchro(object.id, sync_id, action)
                if synchro_obj_line:
                    print(synchro_obj_line)
                    synchro_obj_line[0].update_date =  fields.Datetime.now()

                if not destination_inverted:
                    pool = pool_dest.env[object.model_id.model]
                    try:
                        pool.browse([id2]).sudo().update(value)
                    except Exception as e :
                        erreur = 'Erreur update : ' + str(e)
                        erreurs.append(erreur)
                        _logger.critical("Erreur update : " + str(e))

                else:
                    try:
                        if action == 'd':
                            pool_dest.get(object.model_id.model).sudo().write(id2,value)
                        else:
                            print("apdate",object.model_id.model,id2,value)
                            pool_dest.get(object.model_id.model).write(id2, value)
                    except Exception as e:
                        erreur = 'Erreur write : ' + str(e)
                        erreurs.append(erreur)
                        _logger.critical("Erreur write : " + str(e))
                print("object.model_id.mode usf",object.model_id.model)
                if object.model_id.model=="petrol.station.recette":
                    self.recette_update_ids.append(str(id2))
                self.report_total += 1
                self.report_write += 1
                _logger.debug("write : .model --> %s , report_write-->%s  sync_id--->%s id--->%s",object.model_id.name, self.report_write, str(sync_id),str(id2))
            else:
                _logger.debug("Creating model %s", object.model_id.name)
                new_id = 0
                if object.model_id.name == "petrol.station.boncommande":
                    print("usf log",value)

                try:
                    if not destination_inverted:
                        if action == 'd':
                            new_id = pool_dest.env[object.model_id.model
                                               ].sudo().create(value).id
                        else:
                            new_id = pool_dest.env[object.model_id.model
                            ].create(value).id
                    else:
                        if action == 'd':
                            new_id = pool_dest.get(
                                object.model_id.model).sudo().create(value)
                        else:
                            new_id = pool_dest.get(
                                object.model_id.model).create(value)


                except Exception as e:
                    erreur = 'Erreur create: '+str(e)
                    erreurs.append(erreur)
                    _logger.critical("Erreur create : " + str(e))

                    #raise Warning(_(e))
                if new_id :
                    self.env['base.synchro.obj.line'].sudo().create({
                        'name': fields.Datetime.now(),
                        'obj_id': object.id,
                        'local_id': (action == 'u') and sync_id or new_id,
                        'remote_id': (action == 'd') and sync_id or new_id
                    })
                    self._cr.commit()
                    self.report_total += 1
                    self.report_create += 1
                    if object.model_id.model == "petrol.station.recette":
                        self.recette_add_ids.append(str(new_id))
                    _logger.debug("create : model--->%s report_create-->%s sync_id--->%s new_id--->%s", object.model_id.model, self.report_create, str(sync_id), str(new_id))
                print("value", value)

            self._cr.commit()
            print("commit : ",dt,sync_id,action)
            _logger.debug("commit : %s", object.model_id.name)




            print("create : ", self.report_create)
            print("write : ", self.report_write)


        if len(erreurs) > 0 :
            return '\n'.join(erreurs)

        return False

    @api.model
    def get_synchro(self, object_id, id, action):
        try:
            synch_line_obj = self.env['base.synchro.obj.line']
            field_src = (action == 'u') and 'local_id' or 'remote_id'
            field_dest = (action == 'd') and 'local_id' or 'remote_id'
            synch_line_rec = synch_line_obj.search(
                [('obj_id', '=', object_id), (field_src, '=', id)], limit=1)


            return synch_line_rec
        except Exception as e:
            _logger.critical("Erreur  : " + str(e))
            return False


    @api.model
    def get_id(self, object_id, id, action):
        try :
            synch_line_obj = self.env['base.synchro.obj.line']
            field_src = (action == 'u') and 'local_id' or 'remote_id'
            field_dest = (action == 'd') and 'local_id' or 'remote_id'
            synch_line_rec = synch_line_obj.search_read(
                [('obj_id', '=', object_id), (field_src, '=', id)], [field_dest],limit=1, order="id desc")

            return synch_line_rec and synch_line_rec[0][field_dest] or False
        except Exception as e:
            _logger.critical("Erreur  : " + str(e))
            return False
                    # raise Warning(_(e)) 

    @api.model
    def relation_transform(self, pool_src, pool_dest, obj_model, res_id,
                           action, destination_inverted):
        is_product_product = False
        if obj_model == 'product.product' :

            is_product_product = True
            obj_model = 'product.template'
        if not res_id:
            return False
        _logger.debug("Relation transform")
        
        obj = False
        try :
            self._cr.execute('''select o.id from base_synchro_obj o left join
                            ir_model m on (o.model_id =m.id) where
                            m.model=%s ''', (obj_model,))

            obj = self._cr.fetchone()
            print(obj_model, res_id, action)
        except  Exception as  e:
            _logger.critical("Erreur : "+str(e))
        
        result = False
        if obj:
            result = self.get_id(obj[0], res_id, action)
            print("get id : ",obj_model, obj[0], res_id, result)
            #if is_product_product and result :
            #    self.env['']


            print(result)
            _logger.debug(
                "Relation object already synchronized. Getting id %s",
                result)
        else:
            _logger.debug('Relation object not synchronized. Searching \
             by name_get and name_search') #
            if not destination_inverted:
                try:
                    names = pool_src.get(obj_model).name_get([res_id])[0][1]
                    res = pool_dest.env[obj_model].name_search(
                        names, [], 'like', 1)
                    res = res and res[0][0] or False
                except Exception as e:
                    # raise Warning(_(e))
                    _logger.critical("Erreur : " + str(e))
                    res = False     
            else:
                pool = pool_src.env[obj_model]
                try:               
                    names = pool.browse([res_id]).name_get()[0][1]

                     
                    rec_name = pool_src.env[obj_model]._rec_name
                    res = pool_dest.get(obj_model).search(
                        [(rec_name, '=', names)], 1)
                    res = res and res[0] or False
                except Exception as e:
                    _logger.critical("Erreur : " + str(e))
                    res = False
                    #raise Warning(_(e))

            _logger.debug("name_get in src: %s", names)

            if res:
                result = res
            else:
                _logger.warning(
                    "Record '%s' on relation %s not found, set to null.",
                    names, obj_model)
                _logger.warning(
                    "You should consider synchronize this model '%s'",
                    obj_model)
                self.report.append(
                    'WARNING: Record "%s" on relation %s not found, set to\
                     null.' % (names, obj_model))
        return result

    @api.model
    def data_transform(self, pool_src, pool_dest, obj, data, action=None,
                       destination_inverted=False, avoid_fields=[]):

        if action is None:
            action = {}
        if not destination_inverted:
            fields = pool_src.get('ir.model.fields').search_read(
                [('model_id.model', '=', obj),
                 ('name', 'not in', avoid_fields),
                 ('store', '=', True)],
                ['name', 'ttype', 'relation'])
        else:
            fields = pool_src.env['ir.model.fields'].search_read(
                [('model_id.model', '=', obj),
                 ('name', 'not in', avoid_fields),
                 ('store', '=', True)],
                ['name', 'ttype', 'relation'])

        _logger.debug("Transforming data")
        d = {}
        for field in fields:
            ftype = field.get('ttype')
            fname = field.get('name')

            if fname in avoid_fields:
                del data[fname]
            if ftype in ('function', 'one2many', 'one2one'):
                _logger.debug("Field %s of type %s, discarded.", fname, ftype)
                del data[fname]
            elif ftype == 'many2one':
                _logger.debug("Field %s is many2one", fname)
                # a revoir usf
                if not data.get(fname, False) :
                    continue
                if   (isinstance(data[fname], list)) and data[fname]:
                    fdata = data[fname][0]
                else:
                    fdata = data[fname]
                df = self.relation_transform(pool_src, pool_dest,
                                             field.get('relation'), fdata,
                                             action, destination_inverted)
                data[fname] = df
                if not data[fname]:
                    del data[fname]
            elif ftype == 'many2many':
                if fname == "station_ids":
                    data[fname] = [self.server_url.station_remote_id]
                data[fname] = [(6, 0, [
                        rec for rec in
                        map(lambda res: self.relation_transform(
                            pool_src, pool_dest, field.get(
                                'relation'),
                            res, action, destination_inverted),
                            data[fname]) if rec])]

            if data.get(fname,False) or data.get(fname) == 0 :
                d[fname] = data[fname]


        del data['id']
        if d['id']:
            del d['id']

        return d

    def adressMacVerfier(self):
        server = self.server_url
        pool = RPCProxy(server)
        module = pool.get('petrol.station')
        # get adress mac de pc
        mac = get_mac()
        if self.server_url.station_remote_id:
            # verifer l'adress mac dans centrale
            station_remote_id = module.search_read([("id", "=", self.server_url.station_remote_id)])[0]
            print("station_remote_id",self.server_url.station_remote_id)

            if not station_remote_id.get('mac_adress',False) :

                # si vide créé une et synchroniser
                module.write(self.server_url.station_remote_id,{
                    'mac_adress' :  str(mac)
                })
                return True
            # si pas vide comparer avec adress mac de pc si ok synchrise
            elif station_remote_id.get('mac_adress') ==  str(mac) :
                return True
            else :
               station =  self.env['petrol.station'].search_read([],limit=1, order="id desc")[0]
               station_id = self.env['petrol.station'].browse(station.get('id'))

               if not station_id.forcer :
                   station_id.sudo().write({
                       'duplicate':True
                   })
                   self._cr.commit()
                   raise Warning(_('La station est configurer sur une autre machine , merci de contacter l\'adminstrateur' ))
               else:
                   module.write(self.server_url.station_remote_id, {
                       'mac_adress': str(mac)
                   })
                   station_id.duplicate = True
                   station_id.forcer = False
                   return True






    @api.multi
    def upload_download(self):
        self.ensure_one()
        self.report = []

        self.report_total = 0
        self.report_create = 0
        self.report_write = 0
        self.recette_add_ids = []
        self.recette_update_ids = []
        start_date = fields.Datetime.now()
        server = self.server_url
        pool = RPCProxy(server)
        self.adressMacVerfier()
        erreurs = []



        for obj_rec in server.obj_ids:
            _logger.debug("Start synchro of %s", obj_rec.name)
            erreur = self.synchronize(server, obj_rec)
            if erreur :
                erreurs.append(erreur)
            if obj_rec.action == 'b':
                time.sleep(1)
            if len(erreurs) == 0 :
                obj_rec.write({'synchronize_date': fields.Datetime.now()})
        end_date = fields.Datetime.now()

        # Creating res.request for summary results
        if self.user_id:
            res_request = self.env['res.request']
            erreur = '\n'.join(erreurs)
            if not self.report:
                self.report.append('No exception.')
            etat = 'no_erreur'
            if len(erreurs) > 0:
                etat = 'erreur'

                ## add station.synchro.report
            synchro_object = self.env['station.synchro.report']
            dbName = self._cr.dbname
            raport_recette = ""
            raport_recette +="""Here is the synchronization report:

Synchronization started: %s
Synchronization finished: %s

Synchronized records: %d
Records updated: %d
Records created: %d
            """% (start_date, end_date, self.report_total, self.report_write,
               self.report_create)

            print("recette_a=dd_ids 3", self.recette_add_ids)
            if len(self.recette_add_ids)>0:
                raport_recette +="recettes ajouter  : "
                raport_recette += ','.join(self.recette_add_ids)
            if len(self.recette_update_ids) > 0:
                raport_recette += "\n recettes modifier  : "
                raport_recette += ','.join(self.recette_update_ids)

            ip = ""
            print("recette_a=dd_ids 4")
            """try:
                req = requests.get("http://ip.jsontest.com/", verify=False)
                dat = req.json()
                if dat.get("ip", False):
                    ip = dat.get("ip")
            except Exception as e:
                pass"""
            #print("http.request.httprequest",str(http.request.httprequest))
            value_report = {
                'date' : fields.Datetime.now(),
                'db_name' : dbName,
                'address_ip' :socket.gethostbyname(socket.gethostname()),
                'address_ip_client': ip,
                'etat':etat,
                'erreur':erreur,
                'station_station_remote_id':self.server_url.station_remote_id,
                'user_name': self.user_id.name,
                'raport':raport_recette,
                #'url': http.request.httprequest and  str(http.request.httprequest) or 'cron'
            }
            print("recette_a=dd_ids 5")
            synchro_object.create(value_report)
            print("creat report usf",value_report)
            pool.get('station.synchro.report').create(value_report)

            summary = '''Here is the synchronization report:

Synchronization started: %s
Synchronization finished: %s

Synchronized records: %d
Records updated: %d
Records created: %d
Erreur : %s
Exceptions:
        ''' % (start_date, end_date, self.report_total, self.report_write,
               self.report_create,erreur)
            summary += '\n'.join(self.report)
            print("xreate ")
            res_request.create({
                'name': "Synchronization report",
                'act_from': self.user_id.id,
                'date': fields.Datetime.now(),
                'act_to': self.user_id.id,
                'body': summary,
            })
            return  erreurs

    @api.multi
    def upload_download_multi_thread(self):
        """threaded_synchronization = threading.Thread(
            target=self.upload_download())
        threaded_synchronization.run()"""
        erreurs =  self.upload_download()
        print('ttttt',erreurs)
        view_rec = self.env.ref('base_synchro.view_base_synchro_finish',
                                raise_if_not_found=False)
        action = self.env.ref(
            'base_synchro.action_view_base_synchro', raise_if_not_found=False
        ).read([])[0]
        action['views'] = [(view_rec and view_rec.id or False, 'form')]
        action['context'] = {
            'default_message': '/n'.join(erreurs)
        }
        return action
