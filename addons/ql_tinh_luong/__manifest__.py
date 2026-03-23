# -*- coding: utf-8 -*-
{
    'name': "Tính Lương",
    'summary': "Tự động tính lương từ chấm công, OT, thưởng/phạt và hồ sơ nhân sự",
    'author': "My Company",
    'category': 'Human Resources',
    'version': '0.2',
    'depends': ['base', 'ql_nhan_su', 'ql_cham_cong', 'hr'],
    'data': [
        'security/ir.model.access.csv',
        'report/phieu_luong_template.xml',
        'views/tao_bang_luong_wizard.xml',
        'views/bang_luong.xml',
        'views/menu.xml',
    ],
    'demo': [],
}
