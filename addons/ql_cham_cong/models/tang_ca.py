# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date


class TangCa(models.Model):
    _name = 'tang_ca'
    _description = 'Quản Lý Tăng Ca (OT)'
    _rec_name = 'display_name'
    _order = 'ngay_tang_ca desc'

    nhan_vien_id = fields.Many2one('nhan_vien', string='Nhân Viên', required=True, index=True)
    phong_ban_id = fields.Many2one('phong_ban', related='nhan_vien_id.phong_ban_id', store=True, readonly=True)
    ngay_tang_ca = fields.Date(string='Ngày Tăng Ca', required=True, default=fields.Date.today)
    loai_ngay = fields.Selection([
        ('thuong', 'Ngày Thường'),
        ('cuoi_tuan', 'Cuối Tuần'),
        ('le', 'Ngày Lễ'),
    ], string='Loại Ngày', required=True, default='thuong')
    gio_bat_dau = fields.Float(string='Giờ Bắt Đầu OT', required=True)
    gio_ket_thuc = fields.Float(string='Giờ Kết Thúc OT', required=True)
    so_gio_ot = fields.Float(string='Số Giờ OT', compute='_compute_so_gio_ot', store=True)
    he_so_ot = fields.Float(string='Hệ Số OT', compute='_compute_he_so', store=True,
                            help='Ngày thường: 1.5x | Cuối tuần: 2.0x | Lễ: 3.0x')
    trang_thai = fields.Selection([
        ('cho_duyet', 'Chờ Duyệt'),
        ('da_duyet', 'Đã Duyệt'),
        ('tu_choi', 'Từ Chối'),
    ], string='Trạng Thái', default='cho_duyet')
    ghi_chu = fields.Text(string='Ghi Chú')
    display_name = fields.Char(compute='_compute_display_name', store=True)

    @api.depends('nhan_vien_id', 'ngay_tang_ca')
    def _compute_display_name(self):
        for r in self:
            nv = r.nhan_vien_id.ho_va_ten or ''
            r.display_name = f"OT {nv} - {r.ngay_tang_ca}" if nv else 'Tăng Ca Mới'

    @api.depends('gio_bat_dau', 'gio_ket_thuc')
    def _compute_so_gio_ot(self):
        for r in self:
            if r.gio_ket_thuc > r.gio_bat_dau:
                r.so_gio_ot = round(r.gio_ket_thuc - r.gio_bat_dau, 2)
            else:
                r.so_gio_ot = 0.0

    @api.depends('loai_ngay')
    def _compute_he_so(self):
        he_so_map = {'thuong': 1.5, 'cuoi_tuan': 2.0, 'le': 3.0}
        for r in self:
            r.he_so_ot = he_so_map.get(r.loai_ngay, 1.5)

    @api.constrains('gio_bat_dau', 'gio_ket_thuc')
    def _check_gio(self):
        for r in self:
            if r.gio_ket_thuc <= r.gio_bat_dau:
                raise ValidationError("Giờ kết thúc phải sau giờ bắt đầu!")
            if r.so_gio_ot > 4:
                raise ValidationError("Số giờ OT không được vượt quá 4 giờ/ngày!")

    def _get_or_create_bang_luong(self, rec):
        """Lấy hoặc tự động tạo bảng lương cho nhân viên trong tháng."""
        thang = str(rec.ngay_tang_ca.month)
        nam = rec.ngay_tang_ca.year
        bang_luong = self.env['bang_luong'].search([
            ('nhan_vien_id', '=', rec.nhan_vien_id.id),
            ('thang', '=', thang),
            ('nam', '=', nam),
        ], limit=1)
        if not bang_luong:
            hd = self.env['hop_dong'].search([
                ('nhan_vien_id', '=', rec.nhan_vien_id.id),
                ('trang_thai', '=', 'active'),
            ], limit=1, order='ngay_bat_dau desc')
            if hd:
                bang_luong = self.env['bang_luong'].create({
                    'nhan_vien_id': rec.nhan_vien_id.id,
                    'thang': thang,
                    'nam': nam,
                    'hop_dong_id': hd.id,
                    'luong_co_ban': hd.luong_co_ban,
                    'so_ngay_cong_chuan': hd.so_ngay_cong_chuan,
                })
        return bang_luong

    def _trigger_bang_luong_recompute(self):
        """Trigger recompute bảng lương khi tăng ca thay đổi trạng thái."""
        for rec in self:
            if not rec.nhan_vien_id or not rec.ngay_tang_ca:
                continue
            bang_luong = self._get_or_create_bang_luong(rec)
            if bang_luong:
                bang_luong._compute_ot()
                bang_luong._compute_luong()

    def action_duyet(self):
        self.trang_thai = 'da_duyet'
        self._trigger_bang_luong_recompute()

    def action_tu_choi(self):
        self.trang_thai = 'tu_choi'
        self._trigger_bang_luong_recompute()
