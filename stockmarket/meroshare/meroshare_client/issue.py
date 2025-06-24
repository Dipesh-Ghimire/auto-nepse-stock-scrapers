import os
from functools import cached_property


class Issue:
    def __init__(self, json_data):
        self._json_data = json_data

    def __str__(self):
        return (
            "******   COMPANY SHARE ID: {company_share_id}    ******{sep}{share_type} ({share_group}) - {subgroup}"
            " ({symbol}) - {name}{sep}{open_date} - {close_date}{sep}{status}{sep}"
            .format(
                sep=os.linesep,
                company_share_id=self.company_share_id,
                name=self.company_name,
                subgroup=self.subgroup,
                symbol=self.scrip,
                open_date=self.issue_open_date,
                close_date=self.issue_close_date,
                share_type=self.share_type_name,
                share_group=self.share_group_name,
                status=self.status.capitalize())
        )

    @property
    def is_unapplied_ordinary_share(self):
        return self.is_ordinary_shares and not self.is_applied

    @property
    def is_ipo(self):
        return True if self.share_type_name == 'IPO' else False

    @property
    def is_fpo(self):
        return True if self.share_type_name == 'FPO' else False

    @property
    def is_reserved(self):
        return True if self.share_type_name == 'RESERVED' else False
    
    @property
    def is_ordinary_shares(self):
        return True if self.share_group_name == 'Ordinary Shares' else False

    @property
    def status(self):
        return "applied" if self.is_applied else "not applied"

    @property
    def is_applied(self):
        return True if self.action == "edit" else False

    @cached_property
    def is_for_gp(self):
        return True if self._json_data.get("subGroup") == "For General Public" else False
    
    @cached_property
    def company_share_id(self):
        return self._json_data.get("companyShareId")

    @cached_property
    def subgroup(self):
        return self._json_data.get("subGroup")

    @cached_property
    def scrip(self):
        return self._json_data.get("scrip")

    @cached_property
    def company_name(self):
        return self._json_data.get("companyName")

    @cached_property
    def share_type_name(self):
        return self._json_data.get("shareTypeName")

    @cached_property
    def share_group_name(self):
        return self._json_data.get("shareGroupName")

    @cached_property
    def status_name(self):
        return self._json_data.get("statusName")

    @cached_property
    def action(self):
        return self._json_data.get("action")

    @cached_property
    def issue_open_date(self):
        return self._json_data.get("issueOpenDate")

    @cached_property
    def issue_close_date(self):
        return self._json_data.get("issueCloseDate")
    
    @cached_property
    def is_foreign(self):
        return True if self._json_data.get("reservationTypeName") == "FOREIGN EMPLOYMENT" and self._json_data.get("prospectusRemarks") == "IPO for Foreign Employment" else False
    
    @cached_property
    def is_reapply(self):
        return True if self._json_data.get("action") == "reapply" else False