# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class BangLuongLine(models.Model):
    _name = 'bang_luong.line'
    _description = 'Chi Tiết Phiếu Lương'
    _order = 'type desc, name'

    bang_luong_id = fields.Many2one('bang_luong', string='Bảng Lương',
                                    required=True, ondelete='cascade', index=True)
    name = fields.Char(string='Nội Dung', required=True,
                       help='Ví dụ: Lương cứng, Thưởng KPI, Phạt đi muộn...')
    amount = fields.Float(string='Số Tiền (VNĐ)', required=True, default=0.0)
    type = fields.Selection([
        ('cong', 'Cộng'),
        ('tru', 'Trừ'),
    ], string='Loại', required=True, default='cong')

    @api.constrains('amount')
    def _check_amount(self):
        for rec in self:
            if rec.amount < 0:
                raise ValidationError("Số tiền không được âm!")
