# -*- coding: utf-8 -*-
{
    'name': "Chấm Công",
    'summary': "Quản lý điểm danh, lịch làm việc, tăng ca, nghỉ phép và thưởng/phạt nhân viên",
    'author': "My Company",
    'website': "http://www.yourcompany.com",
    'category': 'Human Resources',
    'version': '0.1',
    'depends': ['base', 'ql_nhan_su'],
    'data': [
        'security/ir.model.access.csv',
        'views/lich_lam_viec.xml',
        'views/diem_danh.xml',
        'views/yeu_cau_nghi_phep.xml',
        'views/tang_ca.xml',
        'views/thuong_phat.xml',
        'views/menu.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
}
