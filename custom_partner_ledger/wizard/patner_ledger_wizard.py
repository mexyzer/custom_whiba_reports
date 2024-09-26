# -*- coding: utf-8 -*-


from odoo import models, fields
import calendar
from dateutil.relativedelta import relativedelta


class PartnerLedger(models.TransientModel):
    _name = "partner.ledger"
    _description = "Partner Ledger"

    def _default_date_from(self):
        date = fields.Date.today().replace(day=1) - relativedelta(months=1)
        return date

    def _default_date_to(self):
        date = fields.Date.today().replace(day=1) - relativedelta(months=1)
        max_day_in_month = calendar.monthrange(date.year, date.month)[1]
        date = date.replace(day=max_day_in_month)
        return date

    date_from = fields.Date("From Date", required=True, default=_default_date_from)
    date_to = fields.Date("To Date", required=True, default=_default_date_to)
    partner_type = fields.Selection([('receivables', 'Receivables'), ('payables', 'Payables'), ('both', 'Both')],
                                    default="both", required=True)
    include_unposted_entries = fields.Boolean('Include Unposted Entries')

    type = fields.Selection([('balances', 'Balances'), ('detailed', 'Detailed')], required=True, string="Type",
                            default="balances")
    ignore_limit = fields.Float("Ignore Limit")
    note = fields.Text("Note")

    def export_pdf(self):
        acc_partner_ledger = self.env.ref('account_reports.partner_ledger_report')
        date = acc_partner_ledger.sudo()._get_dates_period(self.date_from, self.date_to, 'range', 'custom')
        options = self.with_context(target_date=date).sudo().export_data()
        options['unfold_all'] = True
        options.update({
            'include_initial_balance': True,  # Ensure initial balance is included
        })
        lines = acc_partner_ledger.sudo()._get_lines(options)
        partner_ids = self.env["res.partner"].browse(self._context.get('active_ids'))

        all_lines = []
        total_line = {}

        move_line = self.env["account.move.line"].sudo()

        def extract_number_from_string(input_string):
            parts = input_string.split('~account.move.line~')
            if len(parts) >= 2:
                second_part = parts[-1]
                if '|' in second_part:
                    return int(second_part.split('|')[0])
                else:
                    return int(second_part)
            elif len(parts) == 1:
                return int(parts[0])
            else:
                return int(parts[-1])

        # TODO : handle the types of the account

        initial_balance_lines = self.env['account.move.line'].search([
            ('partner_id', '=', partner_ids[0].id),
            ('account_id.account_type', 'in', ['asset_receivable', 'liability_payable']),
            ('date', '<', date['date_from'])])

        initial_balance_debit = sum(initial_balance_lines.mapped('debit'))
        initial_balance_credit = sum(initial_balance_lines.mapped('credit'))
        initial_balance = initial_balance_debit - initial_balance_credit

        cumulative_debit = 0
        cumulative_credit = 0
        cumulative_balance = 0

        if initial_balance:
            all_lines.append({
                'date': False,
                'doc_number': 000,
                'debit': 0,
                'credit': 0,
                'balance': initial_balance,
                'description': f' الرصيد قبل تاريخ {date["date_from"]} ',
            })

            cumulative_balance = initial_balance
            cumulative_debit = initial_balance_debit
            cumulative_credit = initial_balance_credit

        for line in lines:
            if 'account.move.line' in line.get('id'):
                line_id = move_line.browse(extract_number_from_string(line.get('id')))

                cumulative_balance += line_id.debit - line_id.credit
                cumulative_debit += line_id.debit
                cumulative_credit += line_id.credit

                all_lines.append({
                    'date': line_id.date,
                    'doc_number': line_id.move_id.name,
                    'debit': line_id.debit,
                    'credit': line_id.credit,
                    'balance': cumulative_balance,
                    'description': line_id.ref,
                })

        if initial_balance:
            total_line.update({
                'debit': cumulative_debit,
                'credit': cumulative_credit,
                'balance': cumulative_balance
            })

        print(110000, options['date'])
        data = {
            "partner_name": partner_ids[0].name,
            "date": options['date'],
            "lines": all_lines,
            "total_line": total_line,
        }
        return self.env.ref('custom_partner_ledger.action_report_ledger').report_action(self, data=data)

    def export_xlsx(self):
        partner_ledger = self.env.ref('account_reports.partner_ledger_report')
        options = self.export_data()
        return partner_ledger.export_file(options, 'export_to_xlsx')

    def export_data(self):
        partner_ledger = self.env.ref('account_reports.partner_ledger_report')
        # dont_include_details = True if self.type == "balances" else False
        options = partner_ledger.get_options()
        if self.type == 'detailed':
            options.update({'unfold_all': True})
        options.update({
            # 'dont_include_details': dont_include_details,
            'selected_partner_ids': self._context.get('active_ids'),
            'partner_ids': self._context.get('active_ids'),
            'all_entries': True if self.include_unposted_entries else False,
        })
        for account_type in options.get('account_type'):
            if self.partner_type == 'receivables' and account_type.get('id') in ['trade_payable', 'non_trade_payable']:
                options['account_type'].remove(account_type)
            elif self.partner_type == 'payables' and account_type.get('id') in ['trade_receivable',
                                                                                'non_trade_receivable']:
                options['account_type'].remove(account_type)
        date = partner_ledger._get_dates_period(self.date_from, self.date_to, 'range', 'custom')
        options['date'] = date
        options["summary"] = self.note
        options["ignore_limit"] = self.ignore_limit
        options["filtered_partner_ledger"] = True

        return options


class AccountReport(models.AbstractModel):
    _inherit = "account.report"

    def _init_options_column_headers(self, options, previous_options=None):
        if self._context.get('target_date'):
            options['date'] = self._context.get('target_date')
        return super(AccountReport, self)._init_options_column_headers(options, previous_options)
