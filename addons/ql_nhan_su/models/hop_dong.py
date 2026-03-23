# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date


class HopDong(models.Model):
    _name = 'hop_dong'
    _description = 'Hợp Đồng Lao Động'
    _rec_name = 'name'
    _order = 'ngay_bat_dau desc'

    # ─── Thông tin cơ bản ───────────────────────────────────────────────────
    name = fields.Char(string='Số Hợp Đồng', required=True, copy=False)
    nhan_vien_id = fields.Many2one('nhan_vien', string='Nhân Viên', required=True, ondelete='restrict')
    loai_hop_dong = fields.Selection([
        ('chinh_thuc', 'Chính Thức'),
        ('thu_viec', 'Thử Việc'),
        ('thoi_vu', 'Thời Vụ'),
        ('part_time', 'Bán Thời Gian'),
    ], string='Loại Hợp Đồng', default='chinh_thuc', required=True)
    ngay_bat_dau = fields.Date(string='Ngày Bắt Đầu', required=True)
    ngay_ket_thuc = fields.Date(string='Ngày Kết Thúc', required=True)
    thoi_han_con_lai = fields.Integer(
        string='Ngày Còn Lại', compute='_compute_thoi_han', store=False
    )
    trang_thai = fields.Selection([
        ('active', 'Đang Hiệu Lực'),
        ('expired', 'Hết Hạn'),
        ('terminated', 'Đã Chấm Dứt'),
    ], string='Trạng Thái', default='active', required=True)

    # ─── Lương & Ngày công ──────────────────────────────────────────────────
    luong_co_ban = fields.Float(string='Lương Cơ Bản (VNĐ)', required=True, default=0.0)
    so_ngay_cong_chuan = fields.Integer(string='Ngày Công Chuẩn/Tháng', default=26)

    # ─── Chế độ nghỉ phép ───────────────────────────────────────────────────
    ngay_nghi_phep_toi_da = fields.Integer(string='Nghỉ Phép Năm (ngày)', default=12)
    so_ngay_nghi_om = fields.Integer(string='Nghỉ Ốm (ngày)', default=10)
    nghi_phep_dac_biet = fields.Integer(string='Nghỉ Đặc Biệt (ngày)', default=3)
    ngay_nghi_co_luong = fields.Integer(string='Nghỉ Có Lương (ngày)', default=5)
    tu_dong_duyet = fields.Boolean(string='Tự Động Duyệt Nghỉ Phép', default=False)

    ghi_chu = fields.Text(string='Ghi Chú')

    # ════════════════════════════════════════════════════════════════════════
    # COMPUTE
    # ════════════════════════════════════════════════════════════════════════

    @api.depends('ngay_ket_thuc')
    def _compute_thoi_han(self):
        today = date.today()
        for r in self:
            if r.ngay_ket_thuc:
                r.thoi_han_con_lai = (r.ngay_ket_thuc - today).days
            else:
                r.thoi_han_con_lai = 0

    # ════════════════════════════════════════════════════════════════════════
    # CONSTRAINTS
    # ════════════════════════════════════════════════════════════════════════

    @api.constrains('ngay_bat_dau', 'ngay_ket_thuc')
    def _check_ngay(self):
        for r in self:
            if r.ngay_ket_thuc <= r.ngay_bat_dau:
                raise ValidationError("Ngày kết thúc phải sau ngày bắt đầu!")

    @api.constrains('luong_co_ban')
    def _check_luong(self):
        for r in self:
            if r.luong_co_ban < 0:
                raise ValidationError("Lương cơ bản không được âm!")
