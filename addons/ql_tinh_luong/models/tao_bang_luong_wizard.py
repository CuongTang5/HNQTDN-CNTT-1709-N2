# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import date


class TaoBangLuongWizard(models.TransientModel):
    _name = 'tao.bang.luong.wizard'
    _description = 'Wizard Tạo Bảng Lương Hàng Loạt'

    thang = fields.Selection(
        [(str(i), f'Tháng {i}') for i in range(1, 13)],
        string='Tháng', required=True,
        default=lambda self: str(date.today().month)
    )
    nam = fields.Integer(string='Năm', required=True, default=lambda self: date.today().year)
    phong_ban_id = fields.Many2one('phong_ban', string='Phòng Ban (để trống = tất cả)')
    chi_nhan_vien_dang_lam = fields.Boolean(string='Chỉ NV Đang Làm Việc', default=True)

    def action_tao(self):
        self.ensure_one()
        domain = [('trang_thai', '=', 'dang_lam')] if self.chi_nhan_vien_dang_lam else []
        if self.phong_ban_id:
            domain.append(('phong_ban_id', '=', self.phong_ban_id.id))

        nhan_viens = self.env['nhan_vien'].search(domain)
        if not nhan_viens:
            raise UserError("Không tìm thấy nhân viên phù hợp!")

        da_tao = 0
        bo_qua = 0
        for nv in nhan_viens:
            # Kiểm tra đã có bảng lương chưa
            existing = self.env['bang_luong'].search([
                ('nhan_vien_id', '=', nv.id),
                ('thang', '=', self.thang),
                ('nam', '=', self.nam),
            ], limit=1)
            if existing:
                bo_qua += 1
                continue

            # Kiểm tra có hợp đồng active không
            hd = self.env['hop_dong'].search([
                ('nhan_vien_id', '=', nv.id),
                ('trang_thai', '=', 'active'),
            ], limit=1, order='ngay_bat_dau desc')
            if not hd:
                bo_qua += 1
                continue

            self.env['bang_luong'].create({
                'nhan_vien_id': nv.id,
                'thang': self.thang,
                'nam': self.nam,
                'hop_dong_id': hd.id,
                'luong_co_ban': hd.luong_co_ban,
                'so_ngay_cong_chuan': hd.so_ngay_cong_chuan,
            })
            da_tao += 1

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Tạo Bảng Lương Hoàn Tất',
                'message': f'Đã tạo {da_tao} bảng lương. Bỏ qua {bo_qua} (đã tồn tại hoặc thiếu hợp đồng).',
                'type': 'success',
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }
