# -*- coding: utf-8 -*-
##############################################################################
# Author: Mastercore Sinapsys Global®
# Copyright: 2019-Present.
# License OPL-1 (Odoo Proprietary License v1.0) 
# See https://www.odoo.com/documentation/master/legal/licenses.html
#
###############################################################################
from odoo import fields, models, _
import requests
import urllib3
from bs4 import BeautifulSoup
import logging

urllib3.disable_warnings()
_logger = logging.getLogger(__name__)


class resCurrency(models.Model):
    _inherit = 'res.currency'

    def scrapper(self, currency):
        url = 'http://www.bcv.org.ve/'
        try:
            page = self._open_url(url)

            # Parse the html using beautiful soup and store in variable `soup`
            soup = BeautifulSoup(page, 'html.parser')

            # Take out the <div> of name and get its value
            content = ''
            if currency.name == 'USD':
                content = soup.find('div', {"id": "dolar"})
            elif currency.name == 'EUR':
                content = soup.find('div', {"id": "euro"})
            else:
                rate = 0
                return rate

            article = ''
            rate = 0
            for i in content.findAll('strong'):
                rate = float(i.text.replace(' ', '').replace(",", "."))
                article = article + '' + i.text
            _logger.info("::: TIPO DE CAMBIO BCV :::")
            _logger.info("* %s *" % (article))
            return rate
        except Exception as e:
            _logger.error("(scrapper): %s" % (e))

    def _open_url(self, url):
        try:
            return requests.get(url, verify=False).content
        except (ValueError, requests.exceptions.ConnectionError, requests.exceptions.Timeout, requests.exceptions.HTTPError) as e:
            _logger.error("(_open_url) Connection BCV error: %s" % (e))

    def cron_create_currency_rate(self, round_rate=0):
        company_ids = self.env['res.company'].search([])
        for company in company_ids:
            if company.currency_rate_bcv:
                for currency in company.currency_available_ids:
                    rate_bcv = 0
                    date = fields.Date.today()
                    scrapper = False
                    if company.block_days_bcv and company.days_bcv_ids:
                        list_days_block = []
                        for days in company.days_bcv_ids:
                            list_days_block.append(int(days.code) - 1)
                        if int(date.weekday()) in list_days_block:
                            rate_bcv = self._old_rate(currency, company)
                        else:
                            scrapper = True
                    else:
                        scrapper = True
                    bank_holidays = self.env['bank.holidays.bcv'].sudo().search([])
                    if bank_holidays and scrapper:
                        today = fields.Date.context_today(self)
                        holidays = False
                        for day in bank_holidays:
                            if day.date == today:
                                holidays = True
                                break
                        if holidays:
                            rate_bcv = self._old_rate(currency, company)
                            scrapper = False
                    if scrapper:
                        if (company.force_rate_all_currencys and company.force_currency_id):
                            rate_bcv = self.scrapper(company.force_currency_id)
                        else:
                            rate_bcv = self.scrapper(currency)
                    if round_rate > 0:
                        round_rate = round_rate + 1
                        rate_bcv = str(rate_bcv)
                        rate_bcv = rate_bcv[:rate_bcv.index('.')+round_rate]
                    rate = format(1 / float(rate_bcv), '.16f')
                    values = {
                        'rate': rate,
                        'currency_id': currency.id,
                        'company_id': company.id,
                        'name': date,
                    }
                    if currency.id == company.currency_id.id:
                        rate = format(1 * float(rate_bcv), '.16f')
                        values['rate'] = rate
                        values['currency_id'] = self.env['res.currency'].search([('name','in', ['VES'])]).id
                    rec = self.env['res.currency.rate'].search([
                        ('currency_id', '=', (currency.id if (currency.id != company.currency_id.id) else values['currency_id'])),
                        ('name', '=', date),
                        ('company_id', '=', company.id)
                    ])
                    if rec:
                        rec.write(values)
                    else:
                        self.env['res.currency.rate'].create(values)

    def _old_rate(self, currency, company):
        return (1 / self.env['res.currency.rate'].search([
            ('currency_id', '=', currency.id),
            ('company_id', '=', company.id)
        ],limit=1).rate)
