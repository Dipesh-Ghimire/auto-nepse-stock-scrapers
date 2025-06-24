import argparse
from .api import MeroShareAPI
import csv
from .issue import Issue
import urllib3
from datetime import date
from dateutil.relativedelta import relativedelta
from ..models import MeroShareAccount
from ..capital import get_capital_id_from_code

import logging
logger = logging.getLogger("meroshare")


class MeroShareClient:
    def __init__(self, meroshareAccount:MeroShareAccount):
        self.meroshareAccount = meroshareAccount
        self.capital_id = get_capital_id_from_code(meroshareAccount.dp)
        self.api = MeroShareAPI(self.capital_id, meroshareAccount.username, meroshareAccount.password)
        self.bank_info = self.api.get_bank_info()
        self.branch_info = self.api.get_branch_info(self.bank_info['id'])
        self.demat = '130'+self.meroshareAccount.dp + self.meroshareAccount.username

    def logout(self):
        self.api.logout()
        
    def get_issues(self):
        return [Issue(data) for data in self.api.get_open_issues()]

    def get_filtered_issues(self):
        """
        Get issues filtered to return only Ordinary Share IPOs for GPs.
        """
        return [issue for issue in self.get_issues() if issue.is_ipo and issue.is_ordinary_shares and issue.is_for_gp]
     
    def get_filtered_issues_foreign(self):
        """
        Get issues filtered to return only Ordinary Share IPOs for Foreign Employment.
        """
        return [issue for issue in self.get_issues() if issue.is_reserved and issue.is_ordinary_shares and issue.is_reserved]
    
    def apply(self, company_share_id, number_of_shares=10):
        if not self.api.check_applicability(company_share_id, self.demat):
            print(f"Cannot apply: {company_share_id}")
            return
        payload = {
            "appliedKitta": int(number_of_shares),
            "companyShareId": str(company_share_id),
            "customerId": self.branch_info['id'],
            "boid": self.meroshareAccount.username,
            "crnNumber": self.meroshareAccount.crn,
            "bankId": self.branch_info['bankId'],
            "accountNumber": self.branch_info['accountNumber'],
            "demat": self.demat,
            "accountBranchId": self.branch_info['accountBranchId'],
            "transactionPIN": self.meroshareAccount.pin,
            "accountTypeId": self.branch_info['accountTypeId']
        }

        if self.api.apply_to_issue(payload):
            print(f"Successfully applied to: {company_share_id}")
        else:
            print(f"Failed to apply to: {company_share_id}")
            
    def reapply(self, company_share_id, number_of_shares=10):
        applicant_form_id = self.api.fetch_applicantFormId(company_share_id)
        print(f"Reapplying to applicant form id : {applicant_form_id}")
        payload = {
            "appliedKitta": int(number_of_shares),
            "companyShareId": str(company_share_id),
            "customerId": self.branch_info['id'],
            "boid": self.meroshareAccount.username,
            "crnNumber": self.meroshareAccount.crn,
            "bankId": self.branch_info['bankId'],
            "accountNumber": self.branch_info['accountNumber'],
            "demat": self.demat,
            "accountBranchId": self.branch_info['accountBranchId'],
            "transactionPIN": self.meroshareAccount.pin,
            "accountTypeId": self.branch_info['accountTypeId']
        }

        if self.api.reapply_to_issue(applicant_form_id, payload):
            print(f"Successfully re-applied to: {applicant_form_id}")
        else:
            print(f"Failed to re-apply to: {applicant_form_id}")

    def report(self):
        today = date.today()
        two_months_ago = today - relativedelta(months=2)
        reports = self.api.fetch_application_reports(two_months_ago, today)
        for item in reports:
            status = self.api.get_allotment_status(item['applicantFormId'])
            print(f"{item['companyName']} - {status}")
    
    def apply_bulk(self, number_of_shares):
        results = []
        for issue in self.get_filtered_issues():
            result = self.apply(issue.company_share_id, number_of_shares)
            result["company_name"] = issue.company_name
            results.append(result)
        return results

