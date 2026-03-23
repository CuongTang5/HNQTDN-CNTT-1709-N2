# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ThuongPhat(models.Model):
    _name = 'thuong_phat'
    _description = 'Thưởng / Phạt Nhân Viên'
    _rec_name = 'display_name'
    _order = 'ngay_ap_dung desc'

    nhan_vien_id = fields.Many2one('nhan_vien', string='Nhân Viên', required=True, index=True)
    phong_ban_id = fields.Many2one('phong_ban', related='nhan_vien_id.phong_ban_id', store=True, readonly=True)
    loai = fields.Selection([
        ('thuong', 'Thưởng'),
        ('phat', 'Phạt'),
    ], string='Loại', required=True, default='thuong')
    ly_do = fields.Char(string='Lý Do', required=True)
    so_tien = fields.Float(string='Số Tiền (VNĐ)', required=True)
    ngay_ap_dung = fields.Date(string='Ngày Áp Dụng', required=True, default=fields.Date.today)
    thang = fields.Selection(
        [(str(i), f'Tháng {i}') for i in range(1, 13)],
        string='Tháng Tính Lương', required=True
    )
    nam = fields.Integer(string='Năm', required=True)
    trang_thai = fields.Selection([
        ('cho_duyet', 'Chờ Duyệt'),
        ('da_duyet', 'Đã Duyệt'),
        ('tu_choi', 'Từ Chối'),
    ], string='Trạng Thái', default='cho_duyet')
    ghi_chu = fields.Text(string='Ghi Chú')
    display_name = fields.Char(compute='_compute_display_name', store=True)

    @api.depends('nhan_vien_id', 'loai', 'ly_do')
    def _compute_display_name(self):
        for r in self:
            nv = r.nhan_vien_id.ho_va_ten or ''
            loai = 'Thưởng' if r.loai == 'thuong' else 'Phạt'
            r.display_name = f"{loai} - {nv}: {r.ly_do}" if nv else 'Thưởng/Phạt Mới'

    @api.constrains('so_tien')
    def _check_so_tien(self):
        for r in self:
            if r.so_tien <= 0:
                raise ValidationError("Số tiền phải lớn hơn 0!")

    def _trigger_bang_luong_recompute(self):
        for rec in self:
            if not rec.nhan_vien_id or not rec.thang or not rec.nam:
                continue
            bang_luong = self.env['bang_luong'].search([
                ('nhan_vien_id', '=', rec.nhan_vien_id.id),
                ('thang', '=', rec.thang),
                ('nam', '=', rec.nam),
            ], limit=1)
            if not bang_luong:
                hd = self.env['hop_dong'].search([
                    ('nhan_vien_id', '=', rec.nhan_vien_id.id),
                    ('trang_thai', '=', 'active'),
                ], limit=1, order='ngay_bat_dau desc')
                if hd:
                    bang_luong = self.env['bang_luong'].create({
                        'nhan_vien_id': rec.nhan_vien_id.id,
                        'thang': rec.thang,
                        'nam': rec.nam,
                        'hop_dong_id': hd.id,
                        'luong_co_ban': hd.luong_co_ban,
                        'so_ngay_cong_chuan': hd.so_ngay_cong_chuan,
                    })
            if bang_luong:
                bang_luong._compute_thuong_phat()
                bang_luong._compute_luong()

    def action_duyet(self):
        self.trang_thai = 'da_duyet'
        self._trigger_bang_luong_recompute()

    def action_tu_choi(self):
        self.trang_thai = 'tu_choi'
        self._trigger_bang_luong_recompute()
