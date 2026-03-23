from odoo import models, fields

class LuuFile(models.Model):
    _name = 'luu_file'
    _description = 'Lưu file'

    # Dùng ondelete='set null' thay vì 'cascade' để tránh xung đột xóa đồng thời
    # giữa record luu_file và ir_attachment (serialization conflict)
    yeu_cau_nghi_phep_id = fields.Many2one(
        'yeu_cau_nghi_phep', string="Yêu Cầu Nghỉ Phép", ondelete="set null"
    )
    lich_lam_viec_id = fields.Many2one(
        'lich_lam_viec', string="Lịch Làm Việc", ondelete="set null"
    )
    # Không dùng attachment=True để tránh Odoo tự quản lý ir_attachment song song
    luu_file = fields.Binary("Tệp", attachment=False)
    luu_file_name = fields.Char("Tên Tệp")

    def unlink(self):
        """Xóa tuần tự, không để PostgreSQL trigger xóa attachment đồng thời."""
        return super().unlink()