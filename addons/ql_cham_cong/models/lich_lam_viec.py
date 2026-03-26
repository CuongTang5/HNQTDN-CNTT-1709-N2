from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import timedelta

class LichLamViec(models.Model):
    _name = 'lich_lam_viec'
    _description = 'Quản lý lịch làm việc của nhân viên'

    ca_lam_viec = fields.Selection([
        ('sang', 'Ca Sáng (08:00 - 12:00)'),
        ('chieu', 'Ca Chiều (13:00 - 17:00)'),
        ('toi', 'Ca Tối (18:00 - 22:00)')
    ], string="Ca Làm Việc", required=True)
    
    trang_thai = fields.Selection([
        ('cho_duyet', 'Chờ Duyệt'),
        ('da_duyet', 'Đã Duyệt'),
        ('tu_choi', 'Từ Chối')
    ], string="Trạng Thái", default="cho_duyet")

    loai_cong_viec = fields.Selection([
    ('van_phong', 'Làm việc tại văn phòng'),
    ('tu_xa', 'Làm việc từ xa'),
    ('hop', 'Họp'),
    ('dao_tao', 'Đào tạo'),
    ('khac', 'Khác'),
    ], string="Loại công việc", default="van_phong")

    lap_lai = fields.Selection([
    ('khong', 'Không lặp lại'),
    ('hang_tuan', 'Hàng tuần'),
    ('hang_thang', 'Hàng tháng'),
    ], string="Lặp lại", default="khong")
    
    muc_do_uu_tien = fields.Selection([
    ('cao', 'Cao'),
    ('trung_binh', 'Trung bình'),
    ('thap', 'Thấp'),
    ], string="Mức độ ưu tiên", default="trung_binh")
    
    ngay_ket_thuc_lap_lai = fields.Date(string="Ngày kết thúc lặp lại")
    ngay_lam_viec = fields.Date(string="Ngày làm việc", default=fields.Date.today(), required=True)
    gio_bat_dau = fields.Float("Giờ Bắt Đầu" )
    gio_ket_thuc = fields.Float("Giờ Kết Thúc")
    ma_dinh_danh = fields.Char(related='nhan_vien_id.ma_dinh_danh', string="Mã Định Danh", readonly=True)
    so_dien_thoai = fields.Char(related='nhan_vien_id.so_dien_thoai', string="Số Điện Thoại", readonly=True)
    tong_gio = fields.Float('Tổng Giờ Làm', compute='_compute_tong_gio', store=True)
    nhan_vien_id = fields.Many2one('nhan_vien', string="Nhân viên")
    phong_ban_id = fields.Many2one('phong_ban', string="Phòng ban", compute='_compute_phong_ban_va_chuc_vu', store=True)
    chuc_vu_id = fields.Many2one('chuc_vu', string="Chức vụ", compute='_compute_phong_ban_va_chuc_vu', store=True)
    lich_su_dang_ky_ids = fields.One2many('lich_su_dang_ky', 'lich_lam_viec_id', string="Lịch Sử Đăng Ký")
    luu_file_id = fields.One2many('luu_file', 'lich_lam_viec_id', string="Up file cần khi mức độ ưu tiên cao")
    luu_file = fields.Binary("Tệp", attachment=True)
    luu_file_name = fields.Char("Tên Tệp")
    mo_ta = fields.Text(string="Mô tả")


    @api.depends('gio_bat_dau', 'gio_ket_thuc')
    def _compute_tong_gio(self):
        for record in self:
            if record.gio_bat_dau and record.gio_ket_thuc:
                if record.gio_ket_thuc >= record.gio_bat_dau:
                    record.tong_gio = record.gio_ket_thuc - record.gio_bat_dau
                else:
                    record.tong_gio = (24 - record.gio_bat_dau) + record.gio_ket_thuc
            else:
                record.tong_gio = 0.00

    @api.constrains('ngay_lam_viec')
    def _check_ngay_lam_viec(self):
        for record in self:
            if record.ngay_lam_viec < fields.Date.today():
                raise ValidationError("Không thể đăng ký làm việc vào ngày trong quá khứ!")
            
    @api.onchange('ca_lam_viec')
    def _onchange_ca_lam_viec(self):
        if self.ca_lam_viec == 'sang':
            self.gio_bat_dau = 8.00
            self.gio_ket_thuc = 12.00
        elif self.ca_lam_viec == 'chieu':
            self.gio_bat_dau = 13.00
            self.gio_ket_thuc = 17.00
        elif self.ca_lam_viec == 'toi':
            self.gio_bat_dau = 18.00
            self.gio_ket_thuc = 22.00
    

    @api.depends('nhan_vien_id')
    def _compute_phong_ban_va_chuc_vu(self):
        for record in self:
            if record.nhan_vien_id:
                record.phong_ban_id = record.nhan_vien_id.phong_ban_id
                record.chuc_vu_id = record.nhan_vien_id.chuc_vu_id
            else:
                record.phong_ban_id = False
                record.chuc_vu_id = False
    


    @api.model
    def create(self, vals):
        record = super(LichLamViec, self).create(vals)
        # Ghi lại lịch sử đăng ký
        self.env['lich_su_dang_ky'].create({
            'lich_lam_viec_id': record.id,
            'ghi_chu': "Đăng ký ca làm việc mới.",
        })
        return record

    def action_duyet(self):
        for rec in self:
            rec.trang_thai = 'da_duyet'
            if not rec.nhan_vien_id or not rec.ngay_lam_viec:
                continue
            # Kiểm tra đã có bản ghi điểm danh chưa
            existing = self.env['diem_danh'].search([
                ('nhan_vien_id', '=', rec.nhan_vien_id.id),
                ('ngay_lam_viec', '=', rec.ngay_lam_viec),
            ], limit=1)
            if not existing:
                self.env['diem_danh'].create({
                    'nhan_vien_id': rec.nhan_vien_id.id,
                    'ngay_lam_viec': rec.ngay_lam_viec,
                    'lich_lam_viec_id': rec.id,
                    'trang_thai_diem_danh': 'chua_diem_danh',
                })

    def action_xem_diem_danh(self):
        self.ensure_one()
        dd = self.env['diem_danh'].search([
            ('lich_lam_viec_id', '=', self.id),
        ], limit=1)
        if dd:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Điểm Danh',
                'res_model': 'diem_danh',
                'view_mode': 'form',
                'res_id': dd.id,
            }
        return {
            'type': 'ir.actions.act_window',
            'name': 'Điểm Danh',
            'res_model': 'diem_danh',
            'view_mode': 'tree,form',
            'domain': [('nhan_vien_id', '=', self.nhan_vien_id.id),
                       ('ngay_lam_viec', '=', self.ngay_lam_viec)],
        }

    def action_tu_choi(self):
        self.trang_thai = 'tu_choi'

    def action_cho_duyet(self):
        self.trang_thai = 'cho_duyet'