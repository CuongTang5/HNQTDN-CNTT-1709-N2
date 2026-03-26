# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from datetime import datetime


class DiemDanh(models.Model):
    _name = 'diem_danh'
    _description = 'Điểm Danh'
    _rec_name = 'display_name'
    _order = 'ngay_lam_viec desc, nhan_vien_id'

    # ─── Thông tin cơ bản ───────────────────────────────────────────────────
    nhan_vien_id = fields.Many2one('nhan_vien', string="Nhân Viên", required=True, index=True)
    phong_ban_id = fields.Many2one(
        'phong_ban', string="Phòng Ban",
        related='nhan_vien_id.phong_ban_id', store=True, readonly=True
    )
    ngay_lam_viec = fields.Date(string="Ngày Làm Việc", required=True, default=fields.Date.today)
    display_name = fields.Char(compute='_compute_display_name', store=True)

    # ─── Lịch & Ca ──────────────────────────────────────────────────────────
    lich_lam_viec_id = fields.Many2one(
        'lich_lam_viec', string="Lịch Làm Việc",
        domain="[('nhan_vien_id', '=', nhan_vien_id), ('trang_thai', '=', 'da_duyet')]"
    )
    ca_lam_viec = fields.Selection(
        related='lich_lam_viec_id.ca_lam_viec', string="Ca Làm Việc", store=True
    )

    # ─── Check-in / Check-out ────────────────────────────────────────────────
    gio_check_in = fields.Datetime(string="Giờ Check-In", readonly=True)
    gio_check_out = fields.Datetime(string="Giờ Check-Out", readonly=True)
    so_gio_lam = fields.Float(
        string="Số Giờ Làm", compute='_compute_so_gio_lam', store=True
    )

    # ─── Trạng thái ─────────────────────────────────────────────────────────
    trang_thai_diem_danh = fields.Selection([
        ('chua_diem_danh', 'Chưa Hoàn Thành'),
        ('dang_lam', 'Đang Làm Việc'),
        ('som', 'Đến Sớm'),
        ('dung_gio', 'Đúng Giờ'),
        ('muon', 'Đi Muộn'),
        ('hoan_thanh', 'Hoàn Thành'),
    ], string="Trạng Thái", default='chua_diem_danh', readonly=True)

    # Field tính toán để hiển thị màu
    co_dung_gio = fields.Boolean(
        string="Check-in Đúng Giờ", compute='_compute_co_dung_gio', store=True
    )

    ghi_chu = fields.Text(string="Ghi Chú")

    # ════════════════════════════════════════════════════════════════════════
    # COMPUTE
    # ════════════════════════════════════════════════════════════════════════

    @api.depends('gio_check_in', 'ca_lam_viec', 'ngay_lam_viec')
    def _compute_co_dung_gio(self):
        from datetime import datetime
        ca_map = {'sang': (8, 12), 'chieu': (13, 17), 'toi': (18, 22)}
        for r in self:
            if not r.gio_check_in or not r.ca_lam_viec or not r.ngay_lam_viec:
                r.co_dung_gio = True
                continue
            ca = ca_map.get(r.ca_lam_viec)
            if not ca:
                r.co_dung_gio = True
                continue
            ngay = r.ngay_lam_viec
            gio_bat_dau = datetime(ngay.year, ngay.month, ngay.day, ca[0], 0, 0)
            gio_ket_thuc = datetime(ngay.year, ngay.month, ngay.day, ca[1], 0, 0)
            # check-in trong phạm vi ca (cho phép trễ 15 phút)
            check_in_local = r.gio_check_in
            r.co_dung_gio = (gio_bat_dau <= check_in_local <= gio_ket_thuc)

    @api.depends('nhan_vien_id', 'ngay_lam_viec')
    def _compute_display_name(self):
        for r in self:
            nv = r.nhan_vien_id.ho_va_ten or ''
            ngay = str(r.ngay_lam_viec) if r.ngay_lam_viec else ''
            r.display_name = f"{nv} - {ngay}" if nv else 'Điểm Danh Mới'

    @api.depends('gio_check_in', 'gio_check_out')
    def _compute_so_gio_lam(self):
        for r in self:
            if r.gio_check_in and r.gio_check_out:
                delta = r.gio_check_out - r.gio_check_in
                r.so_gio_lam = round(delta.total_seconds() / 3600, 2)
            else:
                r.so_gio_lam = 0.0

    # ════════════════════════════════════════════════════════════════════════
    # ONCHANGE
    # ════════════════════════════════════════════════════════════════════════

    @api.onchange('lich_lam_viec_id')
    def _onchange_lich_lam_viec(self):
        if self.lich_lam_viec_id:
            self.ngay_lam_viec = self.lich_lam_viec_id.ngay_lam_viec

    # ════════════════════════════════════════════════════════════════════════
    # CONSTRAINTS
    # ════════════════════════════════════════════════════════════════════════

    @api.constrains('nhan_vien_id', 'ngay_lam_viec')
    def _check_trung_ngay(self):
        for r in self:
            trung = self.search([
                ('nhan_vien_id', '=', r.nhan_vien_id.id),
                ('ngay_lam_viec', '=', r.ngay_lam_viec),
                ('id', '!=', r.id),
            ])
            if trung:
                raise ValidationError(
                    f"Nhân viên '{r.nhan_vien_id.ho_va_ten}' đã có bản ghi điểm danh ngày {r.ngay_lam_viec}!"
                )

    # ════════════════════════════════════════════════════════════════════════
    # ACTIONS
    # ════════════════════════════════════════════════════════════════════════

    def _get_ca_start_time(self):
        """Trả về giờ bắt đầu ca (datetime) hoặc None."""
        ca_map = {'sang': 8, 'chieu': 13, 'toi': 18}
        if self.ca_lam_viec and self.ngay_lam_viec:
            h = ca_map.get(self.ca_lam_viec)
            if h:
                ngay = self.ngay_lam_viec
                return datetime(ngay.year, ngay.month, ngay.day, h, 0, 0)
        return None

    def _get_or_create_bang_luong(self, rec):
        """Lấy hoặc tự động tạo bảng lương cho nhân viên trong tháng."""
        thang = str(rec.ngay_lam_viec.month)
        nam = rec.ngay_lam_viec.year
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

    def _trigger_bang_luong_recompute(self, records):
        """Tự tạo bảng lương nếu chưa có, rồi recompute."""
        for rec in records:
            if not rec.nhan_vien_id or not rec.ngay_lam_viec:
                continue
            bang_luong = self._get_or_create_bang_luong(rec)
            if bang_luong:
                bang_luong._compute_cong()
                bang_luong._compute_luong()

    @api.model
    def create(self, vals):
        rec = super().create(vals)
        self._trigger_bang_luong_recompute(rec)
        return rec

    def write(self, vals):
        res = super().write(vals)
        if any(f in vals for f in ('gio_check_in', 'gio_check_out', 'trang_thai_diem_danh', 'ngay_lam_viec')):
            self._trigger_bang_luong_recompute(self)
        return res

    def check_in_out(self):
        for rec in self:
            now = fields.Datetime.now()

            if not rec.gio_check_in:
                # Xác định trạng thái check-in
                start = rec._get_ca_start_time()
                if start:
                    diff_minutes = (now_local - start).total_seconds() / 60
                    if diff_minutes < -5:
                        trang_thai = 'som'
                    elif diff_minutes <= 15:
                        trang_thai = 'dung_gio'
                    else:
                        trang_thai = 'muon'
                else:
                    trang_thai = 'dung_gio'

                rec.gio_check_in = now
                rec.trang_thai_diem_danh = 'dang_lam' if trang_thai == 'dung_gio' else trang_thai

            elif not rec.gio_check_out:
                rec.gio_check_out = now
                rec.trang_thai_diem_danh = 'hoan_thanh'

            else:
                raise UserError("Nhân viên đã hoàn thành điểm danh hôm nay!")

        return {'type': 'ir.actions.client', 'tag': 'reload'}
