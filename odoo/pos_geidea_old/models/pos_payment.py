# -*- coding: utf-8 -*-

from odoo import fields, models, api
from datetime import datetime

class PosPayment(models.Model):
    _inherit = 'pos.payment'

  
    card_number = fields.Char(
        string='Card Number',
        help='The last 4 numbers of the card used to pay'
    )

    pos_entry_mode = fields.Char(
        string='POS Entry Mode',
        help='The entry mode of the card used to pay'
    )


    terminal_id = fields.Char(
        string='Terminal ID',
        help='Payment terminal ID'
    )
   

    transaction_type = fields.Char(
        string='Transaction Type',
        help='The type of transaction'
    )
    transaction_response = fields.Char(
        string='Transaction Response',
        help='The response of the transaction'
    )
    transaction_date = fields.Datetime(
        string='Transaction Date',
        help='The date of the transaction'
    )

class PosOrder(models.Model):
    _inherit = "pos.order"

    def _get_payment_data(self, payment, sync_record_data_id=False, payment_method_sync_db_id=False):
        data  = super()._get_payment_data(payment, sync_record_data_id, payment_method_sync_db_id)
        data.update({
            'card_number': payment.card_number,
            'pos_entry_mode': payment.pos_entry_mode,
            'terminal_id': payment.terminal_id,
            'transaction_type': payment.transaction_type,
            'transaction_response': payment.transaction_response,
            'transaction_date': payment.transaction_date,
        })
        return data

    @api.model
    def _payment_fields(self, order, ui_paymentline):
        fields = super()._payment_fields(order, ui_paymentline)
        
        def parse_transaction_date(date_str):
            # Expects '250503173311'
            if not date_str or len(date_str) != 12:
                return False
            try:
                return datetime.strptime(date_str, '%y%m%d%H%M%S')
            except Exception:
                return False

        fields.update({
            'card_number': ui_paymentline.get('card_number'),
            'pos_entry_mode': ui_paymentline.get('pos_entry_mode'),
            'terminal_id': ui_paymentline.get('terminal_id'),
            'transaction_type': ui_paymentline.get('transaction_type'),
            'name': ui_paymentline.get('rrn'),
            'transaction_response': ui_paymentline.get('transaction_response'),
            'transaction_date': parse_transaction_date(ui_paymentline.get('transaction_date')),
        })
       
        return fields