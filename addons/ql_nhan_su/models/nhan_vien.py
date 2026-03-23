# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date


class NhanVien(models.Model):
    _name = 'nhan_vien'
    _description = 'Nhân Viên'
    _rec_name = 'ho_va_ten'
    _order = 'ho_va_ten'

    # ─── Ảnh & Định danh ────────────────────────────────────────────────────
    anh_dai_dien = fields.Image(string="Ảnh Đại Diện", max_width=256, max_height=256)
    ma_dinh_danh = fields.Char("Mã Nhân Viên", required=True, copy=False)
    ho_ten_dem = fields.Char("Họ Tên Đệm", required=True)
    ten = fields.Char("Tên", required=True)
    ho_va_ten = fields.Char("Họ Và Tên", compute="_compute_ho_va_ten", store=True)

    # ─── Thông tin cá nhân ──────────────────────────────────────────────────
    gioi_tinh = fields.Selection([
        ('Nam', 'Nam'), ('Nu', 'Nữ'), ('Khac', 'Khác'),
    ], string="Giới Tính", default='Nam')
    ngay_sinh = fields.Date(string="Ngày Sinh")
    tuoi = fields.Integer(string="Tuổi", compute="_compute_tuoi", store=False)
    que_quan = fields.Char("Quê Quán")
    so_cccd = fields.Char("Số CCCD/CMND")
    ngay_cap_cccd = fields.Date("Ngày Cấp")
    noi_cap_cccd = fields.Char("Nơi Cấp")
    email = fields.Char("Email")
    so_dien_thoai = fields.Char("Số Điện Thoại")
    dia_chi = fields.Text("Địa Chỉ")

    # ─── Công việc ──────────────────────────────────────────────────────────
    chuc_vu_id = fields.Many2one('chuc_vu', string="Chức Vụ")
    phong_ban_id = fields.Many2one('phong_ban', string="Phòng Ban")
    ngay_vao_lam = fields.Date(string="Ngày Vào Làm")
    trang_thai = fields.Selection([
        ('dang_lam', 'Đang Làm Việc'),
        ('nghi_viec', 'Đã Nghỉ Việc'),
        ('thu_viec', 'Thử Việc'),
    ], string="Trạng Thái", default='dang_lam')

    # ─── Hợp đồng ───────────────────────────────────────────────────────────
    hop_dong_ids = fields.One2many('hop_dong', 'nhan_vien_id', string="Danh Sách Hợp Đồng")
    hop_dong_id = fields.Many2one(
        'hop_dong', string="Hợp Đồng Hiện Tại",
        compute="_compute_hop_dong", store=False
    )

    # ─── Smart button counts ─────────────────────────────────────────────────
    so_hop_dong = fields.Integer(string="Số Hợp Đồng", compute="_compute_counts")
    so_diem_danh = fields.Integer(string="Số Ngày Công", compute="_compute_counts")
    so_nghi_phep = fields.Integer(string="Số Đơn Nghỉ Phép", compute="_compute_counts")
    so_bang_luong = fields.Integer(string="Số Bảng Lương", compute="_compute_counts")

    # ════════════════════════════════════════════════════════════════════════
    # COMPUTE
    # ════════════════════════════════════════════════════════════════════════

    @api.depends("ho_ten_dem", "ten")
    def _compute_ho_va_ten(self):
        for r in self:
            r.ho_va_ten = f"{r.ho_ten_dem or ''} {r.ten or ''}".strip()

    @api.depends("ngay_sinh")
    def _compute_tuoi(self):
        today = date.today()
        for r in self:
            if r.ngay_sinh:
                r.tuoi = today.year - r.ngay_sinh.year - (
                    (today.month, today.day) < (r.ngay_sinh.month, r.ngay_sinh.day)
                )
            else:
                r.tuoi = 0

    @api.depends('hop_dong_ids', 'hop_dong_ids.trang_thai', 'hop_dong_ids.ngay_bat_dau')
    def _compute_hop_dong(self):
        for r in self:
            hd = r.hop_dong_ids.filtered(lambda h: h.trang_thai == 'active')
            r.hop_dong_id = hd.sorted('ngay_bat_dau', reverse=True)[:1].id if hd else False

    def _compute_counts(self):
        for r in self:
            r.so_hop_dong = self.env['hop_dong'].search_count([('nhan_vien_id', '=', r.id)])
            # diem_danh và yeu_cau_nghi_phep ở module ql_cham_cong
            if 'diem_danh' in self.env:
                r.so_diem_danh = self.env['diem_danh'].search_count([
                    ('nhan_vien_id', '=', r.id), ('gio_check_in', '!=', False)
                ])
            else:
                r.so_diem_danh = 0
            if 'yeu_cau_nghi_phep' in self.env:
                r.so_nghi_phep = self.env['yeu_cau_nghi_phep'].search_count([('nhan_vien_id', '=', r.id)])
            else:
                r.so_nghi_phep = 0
            if 'bang_luong' in self.env:
                r.so_bang_luong = self.env['bang_luong'].search_count([('nhan_vien_id', '=', r.id)])
            else:
                r.so_bang_luong = 0

    # ════════════════════════════════════════════════════════════════════════
    # ONCHANGE
    # ════════════════════════════════════════════════════════════════════════

    @api.onchange("ten", "ho_ten_dem")
    def _onchange_ten(self):
        for r in self:
            if r.ho_ten_dem and r.ten:
                chu_cai = ''.join([w[0] for w in r.ho_ten_dem.lower().split()])
                r.ma_dinh_danh = r.ten.lower() + chu_cai

    # ════════════════════════════════════════════════════════════════════════
    # CONSTRAINTS
    # ════════════════════════════════════════════════════════════════════════

    @api.constrains('ngay_sinh')
    def _check_ngay_sinh(self):
        for r in self:
            if r.ngay_sinh and r.ngay_sinh > date.today():
                raise ValidationError("Ngày sinh không được lớn hơn ngày hiện tại!")
            if r.ngay_sinh and r.tuoi < 18:
                raise ValidationError("Nhân viên phải đủ 18 tuổi!")

    _sql_constraints = [
        ('ma_dinh_danh_unique', 'unique(ma_dinh_danh)', 'Mã nhân viên phải là duy nhất!')
    ]

    # ════════════════════════════════════════════════════════════════════════
    # SMART BUTTON ACTIONS
    # ════════════════════════════════════════════════════════════════════════

    def action_xem_hop_dong(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Hợp Đồng',
            'res_model': 'hop_dong',
            'view_mode': 'tree,form',
            'domain': [('nhan_vien_id', '=', self.id)],
            'context': {'default_nhan_vien_id': self.id},
        }

    def action_xem_diem_danh(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Điểm Danh',
            'res_model': 'diem_danh',
            'view_mode': 'tree,form',
            'domain': [('nhan_vien_id', '=', self.id)],
            'context': {'default_nhan_vien_id': self.id},
        }

    def action_xem_nghi_phep(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Đơn Nghỉ Phép',
            'res_model': 'yeu_cau_nghi_phep',
            'view_mode': 'tree,form',
            'domain': [('nhan_vien_id', '=', self.id)],
            'context': {'default_nhan_vien_id': self.id},
        }

    def action_xem_bang_luong(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Bảng Lương',
            'res_model': 'bang_luong',
            'view_mode': 'tree,form',
            'domain': [('nhan_vien_id', '=', self.id)],
            'context': {'default_nhan_vien_id': self.id},
        }
