# -*- coding: utf-8 -*-

from odoo import fields, models, api, _

class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    def _get_payment_terminal_selection(self):
        return super()._get_payment_terminal_selection() + [('geidea', 'Geidea')]

    geidea_connection_mode = fields.Selection(
        [
            ("COM", "Serial"),
            ("TCP", "Network"),
        ],
        default="COM", 
        string="Geidea Connection Mode"
    )
    geidea_com_name = fields.Char(string="COM Port")
    geidea_baud_rate = fields.Char(default="38400", string="Baud Rate")
    geidea_data_bits = fields.Char(default="8", string="Data Bits")
    geidea_parity = fields.Char(default="none", string="Parity")
    geidea_ip_address = fields.Char(string="IP Address")
    geidea_port = fields.Integer(string="Port")
    geidea_print_settings = fields.Selection(
        [("1", "Yes"), ("0", "No")], 
        default="1", 
        string="Print Settings"
    )
    geidea_app_id = fields.Char(default="11", string="App ID")