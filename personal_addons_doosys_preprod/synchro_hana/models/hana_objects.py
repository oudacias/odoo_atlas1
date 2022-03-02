# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models,  _
from hdbcli import dbapi
import time
from odoo.exceptions import UserError, ValidationError

class HanaObjects(models.Model):
    _name = "hana.objects"

    name = fields.Char(string="Titre")
    table_name = fields.Char(string="Table hana")
    model_id = fields.Many2one('ir.model')
    type = fields.Selection([
        ('d','Télécharger'),
        ('u','Upload')
    ])
    line_ids = fields.One2many("hana.objects.line","hana_object_id")
    date_last_synchro = fields.Datetime(string="Last Synchronisation")
    domain = fields.Char(string="domain",default="[]")
    active_field = fields.Boolean("Active champ", default= True)
    active = fields.Boolean(string="Active", default=True)

    @api.model
    def schedule_synchro(self):
        conf_ids = self.search([])



    @api.multi
    def sycnhro(self):
        """connection = dbapi.connect(
            address="hxehost",
            port="39041",
            user="SYSTEM",
            password="SAPhxe123",
        )"""
        connection = dbapi.connect(
            address="37.187.134.37",
            port="30015",
            user="SYSTEM",
            password="Skatys2020",
        )
        cursor = connection.cursor()
        print('cursor',cursor)

        synchro_obj = self.env['hana.synchro.line']
        for rec in self:
                seq = "ARTICLE_SEQ"
                #seq = str(rec.name)+"_id_SEQ"
                obj = self.env[rec.model_id.model]
                table = '"TEST_ESCAPADE"."'+rec.table_name+'"'
                line_ids =rec.line_ids.filtered(lambda l: (l.field_name_hana != False))

                champs_lid = line_ids.mapped('field_name_hana')
                print('champs_lid', champs_lid)
                field_names = rec.line_ids.mapped('field_name')
                champs = ",".join('"{0}"'.format(w) for w in champs_lid)
                line_ulti_ids = rec.line_ids.filtered(lambda l: (l.primar == False))
                print('line_ids', line_ids)
                if rec.type == "d":
                    if rec.date_last_synchro:
                        sql = "SELECT "+champs+"  FROM "+table+" WHERE (\"UpdateDate\" >= '"+str(rec.date_last_synchro)+"' OR  \"CreateDate\" >= '"+str(rec.date_last_synchro)+"') AND 	'ValidFor'='ValidFor'"
                    else :
                        sql = "SELECT "+champs+"  FROM "+table+" WHERE 	'ValidFor'='ValidFor'"

                    print(sql)

                    cursor.execute(sql)
                    for row in cursor:
                        row = list(row)
                        print(row)


                        id_remote =  row[0]
                        row.pop(0)
                        i = 0
                        data ={}
                       # print("row",row)

                        for  line_id  in line_ulti_ids:

                            if len(line_id.relation_id)>0:
                                # get id local
                                print("EEEE",row,line_id.relation_id,line_id.relation_id.name)
                                synchro_line_ids = synchro_obj.search([('remote','=',row[i]),('hana_objet_id','=',line_id.relation_id.id)])
                                print(synchro_line_ids)
                                if synchro_line_ids and synchro_line_ids[0]:
                                    data.update({
                                        line_id.field_name:synchro_line_ids[0].local
                                    })
                                else:
                                    raise UserError(_(
                                        'id  %s  de champs  %s ce trouve pas.') % (
                                                    row[i], line_id.field_name))

                            elif line_id.default_value != False:

                                data.update({
                                    line_id.field_name : line_id.default_value
                                })
                            else:
                                print( "ddd",line_id.field_name,row,'i:',i)
                                data.update({
                                    line_id.field_name:  row[i]
                                })

                            i+=1
                        #data = {field_name: row[i] for i, field_name in enumerate(field_names)}
                        print("dist", data)
                        # find if is synchro
                        synchro_ids = synchro_obj.search([('remote','=',id_remote),('hana_objet_id','=',rec.id)])
                        if rec.table_name == "ITM1":
                            pricelist_ids = self.env['product.pricelist.item'].search(
                                ['&',('pricelist_id', '=', data['pricelist_id']),
                                 ('product_tmpl_id', '=', data['product_tmpl_id'])], order="id desc")
                            print("pricelist_ids",pricelist_ids[0].fixed_price,data['fixed_price'])

                            data.update({
                                'date_start': fields.Date().today()
                            })
                            print("data : ", data)
                            if pricelist_ids[0].fixed_price != data['fixed_price']:
                                obj_id = obj.create(
                                    data
                                )

                        elif synchro_ids and synchro_ids[0]:
                            local_id = synchro_ids[0].local
                            obj_id = obj.browse(local_id)
                            print("write",local_id,data)
                            obj_id.write(data)
                        else:
                            obj_id = obj.create(
                                  data
                            )
                            synchro_obj.create({
                                'date':time.strftime("%Y-%m-%d %H:%M:%S"),
                                'hana_objet_id': rec.id,
                                'local': obj_id.id,
                                'remote':id_remote
                            })
                    rec.date_last_synchro = fields.Datetime().now()
                else:
                    dt = rec.date_last_synchro
                    domain =eval(rec.domain) + ['|', ('write_date', '>=', dt),
                                   ('create_date', '>=', dt)]

                    obj_ids = obj.search(domain)
                    print("obj_ids : ",obj_ids)
                    for obj_id in obj_ids:
                        print('obj_id',obj_id)
                        value = []
                        synchro_ids = synchro_obj.search([('local','=',obj_id.id),('hana_objet_id','=',rec.id)])
                        if synchro_ids and synchro_ids[0] and 1!=1:
                            remote_id = synchro_ids[0].remote
                            for line_id in line_ulti_ids:
                                if len(line_id.relation_id) > 0:

                                    synchro__id = synchro_obj.search([('local', '=',obj_id[line_id.field_name].id),
                                                                     ('hana_objet_id', '=', line_id.relation_id.id)], limit=1)

                                    value.append(str(line_id.field_name_hana)+'='+str(synchro__id.remote))
                                else:
                                    if (line_id.field_type == "char" or line_id.field_type == "date" or line_id.field_type == "datetime")  and obj_id[line_id.field_name]:
                                        value.append(line_id.field_name_hana+"="+"'"+str(obj_id[line_id.field_name])+"'")
                                    else:
                                        value.append(line_id.field_name_hana+'='+ str(obj_id[line_id.field_name]) )

                            if len(value) > 0 :
                                #print("value update",value)
                                value_string = ",".join(value)
                                sql = "UPDATE "+ table +" set "+value_string+" WHERE ID="+str(remote_id)
                                print(sql)
                                cursor.execute(sql)
                        else:
                            for line_id in line_ulti_ids:
                                print("line_id",line_id.field_name_hana)
                                if len(line_id.relation_id) > 0:
                                    print("333",line_id.relation_id.name)
                                    synchro__id = synchro_obj.search([('local','=',obj_id[line_id.field_name].id),('hana_objet_id','=',line_id.relation_id.id)], limit= 1)
                                    print("synchro__id : ",synchro__id.remote,synchro__id  ,obj_id[line_id.field_name].id,line_id.relation_id)
                                    if synchro__id.remote:
                                        value.append(str(synchro__id.remote))
                                    else:
                                        value.append(str(0))

                                elif line_id.default_value:
                                    value.append("'"+str(line_id.default_value)+"'")
                                else:
                                    if (line_id.field_type == "char" or line_id.field_type == "date" or line_id.field_type == "datetime" ) and obj_id[line_id.field_name]:
                                        value.append("'"+str(obj_id[line_id.field_name])+"'")
                                    else:
                                        value.append( str(obj_id[line_id.field_name]) )
                                        print("444",  str(obj_id[line_id.field_name]))

                            if len(value) > 0:
                                value_string = ",".join(value)
                               # cursor.execute("SELECT ARTICLE_SEQ.CURRVAL FROM DUMMY;")
                               # row = cursor.fetchone()
                               # print(row)

                                print('SELECT MAX(U_ID) FROM ' + table + ' WHERE 1=1')
                                cursor.execute('SELECT MAX(U_ID) FROM ' + table + ' WHERE 1=1')
                                row = cursor.fetchone()
                                print("row[0",row[0])
                                if not row[0] and row[0]!=0:
                                    id_remote = 0
                                else:
                                    id_remote = int(row[0])+1
                                sql = 'INSERT INTO ' + table + '  ("Code","Name","U_ID",'+ champs +')  VALUES ('+str(id_remote)+','+str(id_remote)+','+str(id_remote)+','+ value_string +') ;'
                                print(sql)
                                cursor.execute(sql)

                                if 'remote_id' in obj_id._fields:
                                    obj_id.remote_id = id_remote

                                #print(cursor,cursor.get_resultset_holdability())
                                synchro_obj.create({
                                    'date': time.strftime("%Y-%m-%d %H:%M:%S"),
                                    'hana_objet_id': rec.id,
                                    'local': obj_id.id,
                                    'remote': id_remote
                                })
                    rec.date_last_synchro = fields.Datetime().now()






               # product_id = product_obj.create(
               #  data
               #  )




class HanaObjectsLine(models.Model):
    _name = "hana.objects.line"
    _order = "sequance"

    hana_object_id = fields.Many2one('hana.objects',string="Hana object")
    field_id = fields.Many2one('ir.model.fields',string="Field")
    field_name = fields.Char(related="field_id.name")
    field_type = fields.Selection(related="field_id.ttype")
    field_name_hana =  fields.Char("Column name hana")
    relation_id  = fields.Many2one("hana.objects","Relation")
    default_value = fields.Char("Default value")
    sequance = fields.Integer("seaqunce")
    primar = fields.Boolean("primare")

class HanaSynchroLine(models.Model):
    _name = "hana.synchro.line"

    date = fields.Datetime(string="date")
    hana_objet_id =  fields.Many2one('hana.objects',string="Hana object")
    local = fields.Integer("local")
    remote = fields.Char("Remote")

