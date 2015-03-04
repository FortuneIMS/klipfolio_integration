# -*- encoding: utf-8 -*-

from openerp.osv import osv, fields
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
import werkzeug
from openerp import SUPERUSER_ID
import urllib2
from werkzeug import url_encode
from requests.auth import HTTPBasicAuth
import requests
import json
import time
from openerp import SUPERUSER_ID


class res_company(osv.Model):
    _inherit = "res.company"
    _columns = {
        'klip_host': fields.char('Klipfolio host url', translate=True, help="klipfolio url for get post data"),
        'klip_user': fields.char('Klipfolio username', translate=True, help="klipfolio user name"),
        'klip_pass': fields.char('Klipfolio password', translate=True, help="klipfolio password"),
    }
    
class klipfolio_data(osv.Model):
    _name = "kilpfolio.data"
    INTERVAL_TYPE = [('minutes', 'Minutes'),
            ('hours', 'Hours'), ('work_days','Work Days'), ('days', 'Days'),('weeks', 'Weeks'), 
            ('months', 'Months')]
    _columns = {
        'name': fields.char('Name', required=True, help="Dashboard name"),
        'datasource_key': fields.char('Datasource', help="klipfolio datasource id", required=True),
        'query': fields.text('Query'),
        'cron_id': fields.many2one('ir.cron', 'Scheduler',ondelete='cascade'),
        'interval_type': fields.related('cron_id','interval_type',selection=INTERVAL_TYPE, 
                                        type='selection', string='Interval Unit', store=True),
        'trigger_on': fields.related('cron_id','nextcall',type="datetime",store=True,string='Trigger On'),
        'active': fields.related('cron_id','active',type="boolean",string='Active',store=True),
        'interval_number': fields.related('cron_id','interval_number',type="integer",string='Interval Number',store=True),
    }

    _defaults = {
         'active': True,
         'trigger_on': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
         'interval_type': 'days',
    }

    def create(self, cr, uid, vals, context=None):
        if context is None: context = {}
        cron_pool = self.pool.get('ir.cron')
        cron_id = cron_pool.create(cr, uid, {
            'name': 'Klipfolio Sync - %s'%(vals.get('name')),
            'active': True,
            'user_id': SUPERUSER_ID,
            'interval_number': 1,
            'interval_type': vals.get('interval_type'),
            'numbercall': -1,
            'doall': False,
            'model': 'kilpfolio.data',
            'function': 'klipfolio_scheduler',
            'args': '()'
        }, context)
        vals.update({'cron_id': cron_id})
        return super(klipfolio_data, self).create(cr, uid, vals, context=context)

#     def _get_klipfolio_cron_id(self,cr, uid, context=None):
#         if context is None: context={}
#         cron_pool = self.pool.get('ir.cron')
#         cron_ids = cron_pool.search(cr, uid, [('function','=','klipfolio_scheduler'),
#                                               ('active','=',True)])
#         print "cron_ids............",cron_ids
#         if not cron_ids:
#             return False
#         return cron_ids[0]
# 
#     _defaults = {
#         'cron_id': _get_klipfolio_cron_id,
#      }

    def test_query(self, cr, uid, ids, context=None):
        if context is None: context = {}
        for obj in self.browse(cr, uid, ids, context):
            try:
                cr.execute(obj.query)
                result = cr.fetchall()
            except Exception,e:
                raise osv.except_osv(_('Error!'), _(str(e)))
        return True

    def klipfolio_scheduler(self, cr, uid, ids, context=None):
        return True

    def contract_query(self,cr, uid, ids, context=None):
        result = []
        for obj in self.browse(cr, uid, ids, context):
#             query = '''
# select 
#     so.name,
#     p.first_name,
#     p.last_name,
#     p.is_company,
#     prod.default_code,
#     so.move_in,
#     so.date,
#     sol.actual_price,
#     sol.discount_price,
#     sol.price_unit,
#     prod.surface_m2
# FROM
#     sale_order_line as sol
# INNER JOIN sale_order as so on so.id=sol.order_id
# INNER JOIN res_partner as p on p.id=so.partner_id
# INNER JOIN product_product as prod on prod.id=sol.product_id
# INNER JOIN product_template as pt on pt.id=prod.product_tmpl_id
# where 
#     so.contract_order=True AND
#     prod.rent_categ=True AND 
#     prod.is_cubix=False
# GROUP BY
#     prod.default_code,
#     prod.surface_m2,
#     so.move_in,
#     so.date,
#     so.name,
#     p.first_name,
#     p.last_name,
#     p.is_company,
#     sol.actual_price,
#     sol.discount_price,
#     sol.price_unit
# ORDER BY
#     so.move_in,
#     so.date,
#     so.name
#             '''
            cr.execute(obj.query)
            result = cr.fetchall()
            print "result..............",result
            self.export_data(cr, uid, ids, result, context)
        return result

    def export_data(self, cr, uid, ids, result, context=None):
        """ @paramas: res list of dictionary """
        single_line_data = """"""
        for res in result:
#             print "res.............",res
            inner_data = ''
            for ele in res:
#                 print "ele..........",ele,type(ele)
                if not ele:
                    inner_data += 'False,'
                elif isinstance(ele, float):
                    inner_data += str(ele) + ','
                elif isinstance(ele, int):
                    inner_data += str(ele) + ','
                else:
                    inner_data += str(ele.encode('ascii', 'xmlcharrefreplace')) + ','
#             print "inner_data.............",inner_data
            single_line_data += inner_data + '\n'

        print "\n\n\nsingle_line_data............................\n",single_line_data
        obj = self.browse(cr, uid, ids[0], context)
        user = self.pool['res.users'].browse(cr, uid, uid, context=context)
        print "..........................", user
        headers = { "Content-Type": "application/json"}
        url = user.company_id.klip_host + '/datasources/%s'%(obj.datasource_key)
        print "url....................",url
    #     {"meta":{"success":true,"status":200},"data":{"clients":[]}} 
    #     ['__attrs__', '__bool__', '__class__', '__delattr__', '__dict__', '__doc__', '__format__', '__getattribute__', '__getstate__', '__hash__', '__init__', '__iter__', '__module__', '__new__', '__nonzero__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__setstate__', '__sizeof__', '__str__', '__subclasshook__', '__weakref__', '_content', 
    #      '_content_consumed', 'apparent_encoding', 'close', 'connection', 'content', 'cookies', 'elapsed', 'encoding', 'headers', 'history', 'iter_content', 'iter_lines', 'json', 'links', 'ok', 'raise_for_status', 'raw', 'reason', 'request', 'status_code', 'text', 'url']
    #     requests.post("https://app.klipfolio.com/api/1/post/clients", data=res)
    #     var = requests.get('https://app.klipfolio.com/api/1/clients', auth=HTTPBasicAuth('sanjay@fortuneims.com', 'please'), params=res)
        var = requests.put(url + '/data',
                           auth=HTTPBasicAuth(user.company_id.klip_user, user.company_id.klip_pass),
                           data=single_line_data, headers=headers)
#         refrsh = requests.post(url + '/@/refresh', auth=HTTPBasicAuth(user.company_id.klip_user, user.company_id.klip_pass))
#         print "refrsh.............",refrsh
#         print ">>aaaa..............", refrsh.text


    #     validate_url = "https://app.klipfolio.com/api/1.0/datasource/524700bcb0cb8b7e8f6d912dc69cc30c/data?" + url_encode(res)
    #     print ".......validate_urlvalidate_urlvalidate_urlvalidate_url", validate_url
    #     urequest = urllib2.Request(validate_url)
    #     uopen = urllib2.urlopen(urequest)
    #     resp = uopen.read()
    #     print ">.....................................", resp
        return True
     
