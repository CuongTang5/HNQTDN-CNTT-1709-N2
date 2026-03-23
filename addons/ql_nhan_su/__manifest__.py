# -*- coding: utf-8 -*-
{
    'name': "ql_nhan_su",
    'summary': "Quản lý nhân sự",
    'author': "My Company",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base', 'hr'],
    'data': [
        'security/ir.model.access.csv',
        'views/nhan_vien.xml',
        'views/chuc_vu.xml',
        'views/phong_ban.xml',
        'views/hop_dong.xml',
        'views/hr_employee_inherit.xml',
        'views/menu.xml',
    ],
    'demo': [],
}
