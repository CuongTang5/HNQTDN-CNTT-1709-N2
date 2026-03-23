# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date


class HrFamily(models.Model):
    _name = 'hr.family'
    _description = 'Thân Nhân Nhân Viên'
    _rec_name = 'name'
    _order = 'employee_id, relationship'

    employee_id = fields.Many2one('hr.employee', string='Nhân Viên', required=True, ondelete='cascade', index=True)
    name = fields.Char(string='Họ Và Tên', required=True)
    relationship = fields.Selection([
        ('vo', 'Vợ'),
        ('chong', 'Chồng'),
        ('con', 'Con'),
        ('cha', 'Cha'),
        ('me', 'Mẹ'),
        ('anh_chi_em', 'Anh/Chị/Em'),
        ('khac', 'Khác'),
    ], string='Quan Hệ', required=True)
    birth_date = fields.Date(string='Ngày Sinh')
    is_dependent = fields.Boolean(string='Người Phụ Thuộc', default=False,
                                  help='Được tính giảm trừ gia cảnh thuế TNCN')
    so_cccd = fields.Char(string='Số CCCD/CMND')
    ghi_chu = fields.Char(string='Ghi Chú')

    @api.constrains('birth_date')
    def _check_birth_date(self):
        for rec in self:
            if rec.birth_date and rec.birth_date > date.today():
                raise ValidationError("Ngày sinh không được lớn hơn ngày hiện tại!")
