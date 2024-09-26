# -*- coding: utf-8 -*-

from odoo import api, models
    
class LedgerReport(models.AbstractModel):
    _name = 'report.custom_partner_ledger.filtered_partner_ledger'
    _description = 'Report Filtered Aging Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        return {
            'doc_ids': docids,
            'data':data,
        }
