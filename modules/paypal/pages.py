# -*- coding: utf-8 -*-

# Copyright(C) 2013      Laurent Bachelier
#
# This file is part of weboob.
#
# weboob is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# weboob is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with weboob. If not, see <http://www.gnu.org/licenses/>.

from decimal import Decimal
import re
import datetime

from weboob.tools.browser import BasePage, BrokenPageError
from weboob.tools.parsers.csvparser import CsvParser
from weboob.tools.misc import to_unicode
from weboob.capabilities.bank import Account, Transaction
from weboob.tools.capabilities.bank.transactions import FrenchTransaction

__all__ = ['LoginPage', 'AccountPage']


def clean_amount(text):
    """
    >>> clean_amount('42')
    Decimal('42')
    >>> clean_amount('42,12')
    Decimal('42.12')
    >>> clean_amount('42.12')
    Decimal('42.12')
    >>> clean_amount('$42.12 USD')
    Decimal('42.12')
    >>> clean_amount('$12.442,12 USD')
    Decimal('12442.12')
    >>> clean_amount('$12,442.12 USD')
    Decimal('12442.12')
    """
    # Convert "American" UUU.CC format to "French" UUU,CC format
    if re.search(r'\d\.\d\d(?: [A-Z]+)?$', text):
        text = text.replace(',', ' ').replace('.', ',')
    return Decimal(FrenchTransaction.clean_amount(text))


class LoginPage(BasePage):
    def login(self, login, password):
        self.browser.select_form(name='login_form')
        self.browser['login_email'] = login
        self.browser['login_password'] = password
        self.browser.submit(nologin=True)


class AccountPage(BasePage):
    def get_account(self, _id):
        return self.get_accounts().get(_id)

    def get_accounts(self):
        accounts = {}
        content = self.document.xpath('//div[@id="main"]//div[@class="col first"]')[0]

        # Total currency balance.
        # If there are multiple currencies, this balance is all currencies
        # converted to the main currency.
        balance = content.xpath('.//h3/span[@class="balance"]')
        if not balance:
            balance = content.xpath('.//li[@class="balance"]//span/strong')
        balance = balance[0].text_content().strip()

        # Primary currency account
        primary_account = Account()
        primary_account.type = Account.TYPE_CHECKING
        primary_account.balance = clean_amount(balance)
        primary_account.currency = Account.get_currency(balance)
        primary_account.id = unicode(primary_account.currency)
        primary_account.label = u'%s %s*' % (self.browser.username, balance.split()[-1])
        accounts[primary_account.id] = primary_account

        # The following code will only work if the user enabled multiple currencies.
        balance = content.xpath('.//div[@class="body"]//ul/li[@class="balance"]/span')
        table = content.xpath('.//table[@id="balanceDetails"]//tbody//tr')

        # sanity check
        if bool(balance) is not bool(table):
            raise BrokenPageError('Unable to find all required multiple currency entries')

        # Primary currency balance.
        # If the user enabled multiple currencies, we get this one instead.
        # An Account object has only one currency; secondary currencies should be other accounts.
        if balance:
            balance = balance[0].text_content().strip()
            primary_account.balance = clean_amount(balance)
            # The primary currency of the "head balance" is the same; ensure we got the right one
            assert primary_account.currency == primary_account.get_currency(balance)

        for row in table:
            balance = row.xpath('.//td')[-1].text_content().strip()
            account = Account()
            account.type = Account.TYPE_CHECKING
            account.balance = clean_amount(balance)
            account.currency = Account.get_currency(balance)
            account.id = unicode(account.currency)
            account.label = u'%s %s' % (self.browser.username, balance.split()[-1])
            if account.id == primary_account.id:
                assert account.balance == primary_account.balance
                assert account.currency == primary_account.currency
            elif account.currency:
                accounts[account.id] = account

        return accounts


class DownloadHistoryPage(BasePage):
    def download(self):
        today = datetime.date.today()
        self.browser.select_form(name='form1')
        # download an entire year
        self.browser['to_c'] = str(today.year)
        self.browser['to_a'] = str(today.month)
        self.browser['to_b'] = str(today.day)
        self.browser['from_c'] = str(today.year - 1)
        self.browser['from_a'] = str(today.month)
        self.browser['from_b'] = str(today.day)

        self.browser['custom_file_type'] = ['comma_balaffecting']
        self.browser['latest_completed_file_type'] = ['']

        self.browser.submit()


class SubmitPage(BasePage):
    """
    Any result of form submission
    """
    def iter_transactions(self, account):
        DATE = 0
        TIME = 1
        NAME = 3
        TYPE = 4
        CURRENCY = 6
        GROSS = 7
        FEE = 8
        NET = 9
        FROM = 10
        TO = 11
        TRANS_ID = 12
        ITEM = 15
        SITE = 24
        csv = self.document
        for row in csv.rows:
            # we filter accounts by currency
            if account.get_currency(row[CURRENCY]) != account.currency:
                continue

            trans = Transaction(row[TRANS_ID])

            # silly American locale
            if re.search(r'\d\.\d\d$', row[NET]):
                date = datetime.datetime.strptime(row[DATE] + ' ' + row[TIME], "%m/%d/%Y %I:%M:%S %p")
            else:
                date = datetime.datetime.strptime(row[DATE] + ' ' + row[TIME], "%d/%m/%Y %H:%M:%S")
            trans.date = date
            trans.rdate = date

            line = row[NAME]
            if row[ITEM]:
                line += u' ' + row[ITEM]
            if row[SITE]:
                line += u"(" + row[SITE] + u")"
            trans.raw = line
            trans.label = row[NAME]

            if row[TYPE].endswith(u'Credit Card') or row[TYPE].endswith(u'carte bancaire'):
                trans.type = Transaction.TYPE_CARD
            elif row[TYPE].endswith(u'Payment Sent') or row[TYPE].startswith(u'Paiement'):
                trans.type = Transaction.TYPE_ORDER
            elif row[TYPE] in (u'Currency Conversion', u'Conversion de devise'):
                trans.type = Transaction.TYPE_BANK
            else:
                trans.type = Transaction.TYPE_UNKNOWN

            # Net is what happens after the fee (0 for most users), so what is the most "real"
            trans.amount = clean_amount(row[NET])
            trans._gross = clean_amount(row[GROSS])
            trans._fees = clean_amount(row[FEE])

            trans._to = row[TO] or None
            trans._from = row[FROM] or None

            yield trans


class HistoryParser(CsvParser):
    HEADER = True
    FMTPARAMS = {'skipinitialspace': True}

    def decode_row(self, row, encoding):
        """
        PayPal returns different encodings (latin-1 and utf-8 are know ones)
        """
        return [to_unicode(cell) for cell in row]


class UselessPage(BasePage):
    pass
