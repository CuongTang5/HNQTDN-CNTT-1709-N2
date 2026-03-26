# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class HrWorkHistory(models.Model):
    _name = 'hr.work.history'
    _description = 'Quá Trình Công Tác'
    _order = 'date_start desc'

    nhan_vien_id = fields.Many2one('nhan_vien', string='Nhân Viên', required=True,
                                   ondelete='cascade', index=True)
    company_name = fields.Char(string='Tên Công Ty / Đơn Vị', required=True)
    position = fields.Char(string='Chức Vụ / Vị Trí', required=True)
    date_start = fields.Date(string='Ngày Bắt Đầu', required=True)
    date_end = fields.Date(string='Ngày Kết Thúc',
                           help='Để trống nếu đây là công việc hiện tại')
    mo_ta = fields.Char(string='Mô Tả')

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for rec in self:
            if rec.date_start and rec.date_start > fields.Date.today():
                raise ValidationError("Ngày bắt đầu không được lớn hơn ngày hiện tại!")
            if rec.date_start and rec.date_end and rec.date_end < rec.date_start:
                raise ValidationError("Ngày kết thúc không được nhỏ hơn ngày bắt đầu!")
