# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date
import calendar


class BangLuong(models.Model):
    _name = 'bang_luong'
    _description = 'Bảng Lương Nhân Viên'
    _rec_name = 'display_name'
    _order = 'nam desc, thang desc, nhan_vien_id'

    # ─── Thông tin cơ bản ───────────────────────────────────────────────────
    nhan_vien_id = fields.Many2one('nhan_vien', string='Nhân Viên', required=True, ondelete='restrict', index=True)
    employee_id = fields.Many2one('hr.employee', string='Nhân Viên HR', ondelete='set null', index=True)
    phong_ban_id = fields.Many2one('phong_ban', related='nhan_vien_id.phong_ban_id', store=True, readonly=True, string='Phòng Ban')
    chuc_vu_id = fields.Many2one('chuc_vu', related='nhan_vien_id.chuc_vu_id', store=True, readonly=True, string='Chức Vụ')
    thang = fields.Selection([(str(i), f'Tháng {i}') for i in range(1, 13)], string='Tháng', required=True)
    nam = fields.Integer(string='Năm', required=True, default=lambda self: date.today().year)
    display_name = fields.Char(compute='_compute_display_name', store=True)

    # ─── Hợp đồng ───────────────────────────────────────────────────────────
    hop_dong_id = fields.Many2one('hop_dong', string='Hợp Đồng', readonly=True)
    luong_co_ban = fields.Float(string='Lương Cơ Bản (VNĐ)', readonly=True)
    so_ngay_cong_chuan = fields.Integer(string='Ngày Công Chuẩn', readonly=True, default=26)

    # ─── Chấm công ──────────────────────────────────────────────────────────
    tong_ngay_cong = fields.Float(string='Ngày Công Thực Tế', compute='_compute_cong', store=True)
    ngay_nghi_phep_co_luong = fields.Float(string='Ngày Nghỉ Phép Có Lương', compute='_compute_cong', store=True)
    tong_ngay_tinh_luong = fields.Float(string='Tổng Ngày Tính Lương', compute='_compute_cong', store=True)

    # Chấm công từ hr.attendance (Odoo HR)
    tong_ngay_cong_hr = fields.Float(string='Ngày Công (HR Attendance)', compute='_compute_cong_hr', store=True)

    # ─── Tăng ca OT ─────────────────────────────────────────────────────────
    tong_gio_ot_thuong = fields.Float(string='Giờ OT Ngày Thường', compute='_compute_ot', store=True)
    tong_gio_ot_cuoi_tuan = fields.Float(string='Giờ OT Cuối Tuần', compute='_compute_ot', store=True)
    tong_gio_ot_le = fields.Float(string='Giờ OT Ngày Lễ', compute='_compute_ot', store=True)
    luong_ot = fields.Float(string='Lương Tăng Ca (VNĐ)', compute='_compute_ot', store=True)

    # ─── Thưởng / Phạt ──────────────────────────────────────────────────────
    tong_thuong = fields.Float(string='Tổng Thưởng (VNĐ)', compute='_compute_thuong_phat', store=True)
    tong_phat = fields.Float(string='Tổng Phạt (VNĐ)', compute='_compute_thuong_phat', store=True)

    # ─── Phụ cấp nhập tay ───────────────────────────────────────────────────
    phu_cap = fields.Float(string='Phụ Cấp Khác (VNĐ)', default=0.0)

    # ─── Tính lương ─────────────────────────────────────────────────────────
    luong_theo_cong = fields.Float(string='Lương Theo Công', compute='_compute_luong', store=True)
    bao_hiem_nhan_vien = fields.Float(string='BHXH/BHYT/BHTN NV (10.5%)', compute='_compute_luong', store=True)
    bao_hiem_doanh_nghiep = fields.Float(string='BHXH/BHYT/BHTN DN (21.5%)', compute='_compute_luong', store=True)
    luong_gross = fields.Float(string='Lương Gross (Trước Khấu Trừ)', compute='_compute_luong', store=True)
    thue_tncn = fields.Float(string='Thuế TNCN (VNĐ)', compute='_compute_luong', store=True)
    luong_thuc_lanh = fields.Float(string='Lương Thực Lãnh (VNĐ)', compute='_compute_luong', store=True)

    # ─── Trạng thái & xác nhận ──────────────────────────────────────────────
    trang_thai = fields.Selection([
        ('nhap', 'Nháp'),
        ('xac_nhan', 'Đã Xác Nhận'),
        ('da_tra', 'Đã Trả Lương'),
        ('nhan_vien_xac_nhan', 'NV Đã Xác Nhận'),
    ], string='Trạng Thái', default='nhap', required=True)
    ngay_tra_luong = fields.Date(string='Ngày Trả Lương')
    da_ky_xac_nhan = fields.Boolean(string='Nhân Viên Đã Xác Nhận Nhận Lương', default=False)
    ngay_ky_xac_nhan = fields.Datetime(string='Ngày Xác Nhận', readonly=True)
    ghi_chu = fields.Text(string='Ghi Chú')

    _sql_constraints = [
        ('unique_nv_thang_nam', 'UNIQUE(nhan_vien_id, thang, nam)',
         'Nhân viên này đã có bảng lương trong tháng/năm này!'),
        ('unique_employee_thang_nam', 'UNIQUE(employee_id, thang, nam)',
         'Nhân viên HR này đã có bảng lương trong tháng/năm này!'),
    ]

    # ════════════════════════════════════════════════════════════════════════
    # COMPUTE
    # ════════════════════════════════════════════════════════════════════════

    @api.depends('nhan_vien_id', 'thang', 'nam')
    def _compute_display_name(self):
        for rec in self:
            nv = rec.nhan_vien_id.ho_va_ten or ''
            rec.display_name = f"Lương {nv} - T{rec.thang}/{rec.nam}" if nv else 'Bảng Lương Mới'

    @api.depends('nhan_vien_id', 'thang', 'nam')
    def _compute_cong(self):
        for rec in self:
            if not (rec.nhan_vien_id and rec.thang and rec.nam):
                rec.tong_ngay_cong = rec.ngay_nghi_phep_co_luong = rec.tong_ngay_tinh_luong = 0.0
                continue
            thang_int = int(rec.thang)
            ngay_dau = date(rec.nam, thang_int, 1)
            ngay_cuoi = date(rec.nam, thang_int, calendar.monthrange(rec.nam, thang_int)[1])

            dd = self.env['diem_danh'].search([
                ('nhan_vien_id', '=', rec.nhan_vien_id.id),
                ('ngay_lam_viec', '>=', ngay_dau),
                ('ngay_lam_viec', '<=', ngay_cuoi),
                ('gio_check_in', '!=', False),
            ])
            ngay_cong = float(len(set(dd.mapped('ngay_lam_viec'))))

            np_records = self.env['yeu_cau_nghi_phep'].search([
                ('nhan_vien_id', '=', rec.nhan_vien_id.id),
                ('trang_thai', '=', 'da_duyet'),
                ('loai_nghi_phep', 'in', ['nghi_phep', 'nghi_co_luong']),
                ('ngay_bat_dau', '<=', ngay_cuoi),
                ('ngay_ket_thuc', '>=', ngay_dau),
            ])
            tong_nghi = 0.0
            for np in np_records:
                tong_nghi += (min(np.ngay_ket_thuc, ngay_cuoi) - max(np.ngay_bat_dau, ngay_dau)).days + 1

            rec.tong_ngay_cong = ngay_cong
            rec.ngay_nghi_phep_co_luong = tong_nghi
            rec.tong_ngay_tinh_luong = ngay_cong + tong_nghi

    @api.depends('employee_id', 'thang', 'nam')
    def _compute_cong_hr(self):
        for rec in self:
            if not (rec.employee_id and rec.thang and rec.nam):
                rec.tong_ngay_cong_hr = 0.0
                continue
            thang_int = int(rec.thang)
            ngay_dau_thang = date(rec.nam, thang_int, 1)
            ngay_cuoi_thang = date(rec.nam, thang_int, calendar.monthrange(rec.nam, thang_int)[1])
            # Đếm số ngày có check_in trong tháng (mỗi ngày tính 1 lần)
            attendances = self.env['hr.attendance'].search([
                ('employee_id', '=', rec.employee_id.id),
                ('check_in', '>=', str(ngay_dau_thang)),
                ('check_in', '<=', str(ngay_cuoi_thang) + ' 23:59:59'),
            ])
            ngay_lam = set(a.check_in.date() for a in attendances if a.check_in)
            rec.tong_ngay_cong_hr = float(len(ngay_lam))

    @api.depends('nhan_vien_id', 'thang', 'nam', 'luong_co_ban')
    def _compute_ot(self):
        for rec in self:
            if not (rec.nhan_vien_id and rec.thang and rec.nam):
                rec.tong_gio_ot_thuong = rec.tong_gio_ot_cuoi_tuan = rec.tong_gio_ot_le = rec.luong_ot = 0.0
                continue
            thang_int = int(rec.thang)
            ngay_dau = date(rec.nam, thang_int, 1)
            ngay_cuoi = date(rec.nam, thang_int, calendar.monthrange(rec.nam, thang_int)[1])

            ot_records = self.env['tang_ca'].search([
                ('nhan_vien_id', '=', rec.nhan_vien_id.id),
                ('trang_thai', '=', 'da_duyet'),
                ('ngay_tang_ca', '>=', ngay_dau),
                ('ngay_tang_ca', '<=', ngay_cuoi),
            ])
            gio_thuong = sum(r.so_gio_ot for r in ot_records if r.loai_ngay == 'thuong')
            gio_cuoi_tuan = sum(r.so_gio_ot for r in ot_records if r.loai_ngay == 'cuoi_tuan')
            gio_le = sum(r.so_gio_ot for r in ot_records if r.loai_ngay == 'le')

            # Lương giờ = luong_co_ban / (so_ngay_cong_chuan * 8)
            chuan = rec.so_ngay_cong_chuan or 26
            luong_gio = rec.luong_co_ban / (chuan * 8) if chuan else 0.0
            luong_ot = (gio_thuong * 1.5 + gio_cuoi_tuan * 2.0 + gio_le * 3.0) * luong_gio

            rec.tong_gio_ot_thuong = gio_thuong
            rec.tong_gio_ot_cuoi_tuan = gio_cuoi_tuan
            rec.tong_gio_ot_le = gio_le
            rec.luong_ot = round(luong_ot, 2)

    @api.depends('nhan_vien_id', 'thang', 'nam')
    def _compute_thuong_phat(self):
        for rec in self:
            if not (rec.nhan_vien_id and rec.thang and rec.nam):
                rec.tong_thuong = rec.tong_phat = 0.0
                continue
            domain_base = [
                ('nhan_vien_id', '=', rec.nhan_vien_id.id),
                ('trang_thai', '=', 'da_duyet'),
                ('thang', '=', rec.thang),
                ('nam', '=', rec.nam),
            ]
            rec.tong_thuong = sum(self.env['thuong_phat'].search(domain_base + [('loai', '=', 'thuong')]).mapped('so_tien'))
            rec.tong_phat = sum(self.env['thuong_phat'].search(domain_base + [('loai', '=', 'phat')]).mapped('so_tien'))

    @api.depends('luong_co_ban', 'so_ngay_cong_chuan', 'tong_ngay_tinh_luong',
                 'luong_ot', 'tong_thuong', 'tong_phat', 'phu_cap')
    def _compute_luong(self):
        for rec in self:
            lcb = rec.luong_co_ban
            chuan = rec.so_ngay_cong_chuan or 26
            luong_theo_cong = (lcb / chuan) * rec.tong_ngay_tinh_luong if chuan else 0.0
            bh_nv = lcb * 0.105
            bh_dn = lcb * 0.215
            luong_gross = luong_theo_cong + rec.luong_ot + rec.tong_thuong + rec.phu_cap - rec.tong_phat
            # Lương thực lãnh = Gross - BHXH nhân viên (10.5%)
            luong_thuc_lanh = luong_gross - bh_nv

            rec.luong_theo_cong = round(luong_theo_cong, 2)
            rec.bao_hiem_nhan_vien = round(bh_nv, 2)
            rec.bao_hiem_doanh_nghiep = round(bh_dn, 2)
            rec.luong_gross = round(max(0.0, luong_gross), 2)
            rec.thue_tncn = 0.0
            rec.luong_thuc_lanh = round(max(0.0, luong_thuc_lanh), 2)

    @api.model
    def _tinh_thue_luy_tien(self, tntt):
        return 0.0

    # ════════════════════════════════════════════════════════════════════════
    # ONCHANGE + CREATE
    # ════════════════════════════════════════════════════════════════════════

    @api.onchange('nhan_vien_id')
    def _onchange_nhan_vien(self):
        self._load_hop_dong()

    def _load_hop_dong(self):
        for rec in self:
            if rec.nhan_vien_id:
                hd = self.env['hop_dong'].search([
                    ('nhan_vien_id', '=', rec.nhan_vien_id.id),
                    ('trang_thai', '=', 'active'),
                ], limit=1, order='ngay_bat_dau desc')
                rec.hop_dong_id = hd.id if hd else False
                rec.luong_co_ban = hd.luong_co_ban if hd else 0.0
                rec.so_ngay_cong_chuan = hd.so_ngay_cong_chuan if hd else 26
            else:
                rec.hop_dong_id = False
                rec.luong_co_ban = 0.0
                rec.so_ngay_cong_chuan = 26

    @api.model
    def create(self, vals):
        rec = super().create(vals)
        if rec.nhan_vien_id and not rec.luong_co_ban:
            rec._load_hop_dong()
        return rec

    # ════════════════════════════════════════════════════════════════════════
    # CONSTRAINTS
    # ════════════════════════════════════════════════════════════════════════

    @api.constrains('nam')
    def _check_nam(self):
        for rec in self:
            if rec.nam < 2000 or rec.nam > 2100:
                raise ValidationError("Năm không hợp lệ (2000–2100)!")

    # ════════════════════════════════════════════════════════════════════════
    # WORKFLOW
    # ════════════════════════════════════════════════════════════════════════

    def action_xac_nhan(self):
        for rec in self:
            if rec.trang_thai != 'nhap':
                raise ValidationError("Chỉ xác nhận được bảng lương ở trạng thái Nháp!")
            hd = self.env['hop_dong'].search([
                ('nhan_vien_id', '=', rec.nhan_vien_id.id),
                ('trang_thai', '=', 'active'),
            ], limit=1)
            if not hd:
                raise ValidationError(f"Nhân viên '{rec.nhan_vien_id.ho_va_ten}' chưa có hợp đồng đang hiệu lực!")
            rec.trang_thai = 'xac_nhan'

    def action_da_tra(self):
        for rec in self:
            if rec.trang_thai != 'xac_nhan':
                raise ValidationError("Chỉ đánh dấu đã trả khi bảng lương đã xác nhận!")
            rec.trang_thai = 'da_tra'
            rec.ngay_tra_luong = date.today()

    def action_nhan_vien_xac_nhan(self):
        """Nhân viên ký xác nhận đã nhận lương."""
        for rec in self:
            if rec.trang_thai != 'da_tra':
                raise ValidationError("Chỉ xác nhận khi lương đã được trả!")
            rec.da_ky_xac_nhan = True
            rec.ngay_ky_xac_nhan = fields.Datetime.now()
            rec.trang_thai = 'nhan_vien_xac_nhan'

    def action_ve_nhap(self):
        for rec in self:
            if rec.trang_thai in ('da_tra', 'nhan_vien_xac_nhan'):
                raise ValidationError("Không thể đưa về nháp khi đã trả lương!")
            rec.trang_thai = 'nhap'

    def action_in_phieu_luong(self):
        return self.env.ref('ql_tinh_luong.action_report_phieu_luong').report_action(self)
