# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HrEmployeeInherit(models.Model):
    _inherit = 'hr.employee'

    que_quan = fields.Char(string='Quê Quán')
    so_cccd = fields.Char(string='Số CCCD')
    ngay_cap = fields.Date(string='Ngày Cấp CCCD')
    noi_cap = fields.Char(string='Nơi Cấp CCCD')

    family_ids = fields.One2many('hr.family', 'employee_id', string='Danh Sách Thân Nhân')
    so_nguoi_phu_thuoc = fields.Integer(
        string='Số Người Phụ Thuộc',
        compute='_compute_so_nguoi_phu_thuoc', store=True
    )

    @api.depends('family_ids', 'family_ids.is_dependent')
    def _compute_so_nguoi_phu_thuoc(self):
        for rec in self:
            rec.so_nguoi_phu_thuoc = len(rec.family_ids.filtered('is_dependent'))

    @api.constrains('birthday')
    def _check_birthday(self):
        for rec in self:
            if rec.birthday and rec.birthday > fields.Date.today():
                raise ValidationError("Ngày sinh không được lớn hơn ngày hiện tại!")
            if rec.birthday:
                from datetime import date
                today = date.today()
                tuoi = today.year - rec.birthday.year - (
                    (today.month, today.day) < (rec.birthday.month, rec.birthday.day)
                )
                if tuoi < 18:
                    raise ValidationError("Nhân viên phải đủ 18 tuổi!")
