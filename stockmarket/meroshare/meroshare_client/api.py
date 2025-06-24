import requests
import logging

logger = logging.getLogger("meroshare")
class MeroShareAPI:
    BASE_URL = 'https://webbackend.cdsc.com.np/api/meroShare'

    def __init__(self, capital_id, username, password):
        self.capital_id = capital_id
        self.username = username
        self.password = password
        self.authorization = self.authenticate()

    def authenticate(self):
        logger.info(f'Authenticating {self.username} with capital ID {self.capital_id}')
        r = requests.post(f'{self.BASE_URL}/auth/',
                          json={'clientId': self.capital_id, 'username': self.username, 'password': self.password},
                          verify='stockmarket/meroshare/meroshare_client/DigiCertGlobalRootG2.crt.pem')
        if r.ok:
            return r.headers['Authorization']
        raise ValueError('Unable to authenticate')

    @property
    def headers(self):
        return {'Authorization': self.authorization}

    def get_bank_info(self):
        r = requests.get(f'{self.BASE_URL}/bank/', headers=self.headers, verify='stockmarket/meroshare/meroshare_client/DigiCertGlobalRootG2.crt.pem')
        logger.info(f"Fetching bank info for {self.username}")
        logger.info(f'Response: {r.status_code} - {r.text} - {r.headers}')
        if r.ok and r.json():
            logger.info(f'Bank info for {self.username}: {r.json()[0]}')
            return r.json()[0]
        raise ValueError('Unable to fetch bank info')

    def get_branch_info(self, bank_id):
        r = requests.get(f'{self.BASE_URL}/bank/{bank_id}', headers=self.headers, verify='stockmarket/meroshare/meroshare_client/DigiCertGlobalRootG2.crt.pem')
        if r.ok:
            info = r.json()[0]
            info['bankId'] = bank_id
            logger.info(f'Branch info for bank {bank_id}: {info}')
            return info
        raise ValueError('Unable to fetch branch info')

    def get_open_issues(self):
        payload = {
            "filterFieldParams": [
                {"key": "companyIssue.companyISIN.script", "alias": "Scrip"},
                {"key": "companyIssue.companyISIN.company.name", "alias": "Company Name"},
                {"key": "companyIssue.assignedToClient.name", "value": "", "alias": "Issue Manager"}
            ],
            "filterDateParams": [
                {"key": "minIssueOpenDate", "condition": "", "alias": "", "value": ""},
                {"key": "maxIssueCloseDate", "condition": "", "alias": "", "value": ""}
            ],
            "page": 1,
            "size": 20,
            "searchRoleViewConstants": "VIEW_APPLICABLE_SHARE"
        }
        r = requests.post(f'{self.BASE_URL}/companyShare/applicableIssue/', json=payload, headers=self.headers, verify='stockmarket/meroshare/meroshare_client/DigiCertGlobalRootG2.crt.pem')
        if r.ok:
            return r.json()['object']
        raise ValueError('Unable to fetch open issues')

    def check_applicability(self, company_share_id, demat):
        r = requests.get(f'{self.BASE_URL}/applicantForm/customerType/{company_share_id}/{demat}',
                         headers=self.headers, verify='stockmarket/meroshare/meroshare_client/DigiCertGlobalRootG2.crt.pem')
        logger.info(f'Checking applicability for {demat} on issue {company_share_id}')
        logger.info(f'Response: {r.status_code} - {r.text}')
        return r.ok and r.json().get('message') == "Customer can apply."

    def apply_to_issue(self, payload):
        logger.info(f'Applying to issue with payload: {payload}')
        r = requests.post(f'{self.BASE_URL}/applicantForm/share/apply', json=payload, headers=self.headers, verify='stockmarket/meroshare/meroshare_client/DigiCertGlobalRootG2.crt.pem')
        return r.ok

    def reapply_to_issue(self, applicant_form_id, payload):
        logger.info(f'Reapplying to issue {applicant_form_id} with payload: {payload}')
        r = requests.post(f'{self.BASE_URL}/applicantForm/share/reapply/{applicant_form_id}', json=payload, headers=self.headers, verify='stockmarket/meroshare/meroshare_client/DigiCertGlobalRootG2.crt.pem')
        return r.ok
    
    def fetch_application_reports(self, from_date, to_date):
        payload = {
            "filterFieldParams": [
                {"key": "companyShare.companyIssue.companyISIN.script", "alias": "Scrip"},
                {"key": "companyShare.companyIssue.companyISIN.company.name", "alias": "Company Name"}
            ],
            "page": 1,
            "size": 20,
            "searchRoleViewConstants": "VIEW_APPLICANT_FORM_COMPLETE",
            "filterDateParams": [
                {"key": "appliedDate", "condition": "", "alias": "", "value": f"BETWEEN '{from_date}' AND '{to_date}'"}
            ]
        }
        r = requests.post(f'{self.BASE_URL}/applicantForm/active/search/', json=payload, headers=self.headers)
        if r.ok:
            return r.json()['object']
        raise ValueError('Error while fetching reports')

    def get_allotment_status(self, application_id):
        r = requests.get(f'{self.BASE_URL}/applicantForm/report/detail/{application_id}', headers=self.headers, verify='stockmarket/meroshare/meroshare_client/DigiCertGlobalRootG2.crt.pem')
        if r.ok:
            return r.json().get('statusName')
        return 'N/A'
    
    def fetch_applicantFormId(self, company_share_id):
        """
        Fetch the applicant form ID for a given company share ID.
        """
        r = requests.get(f'{self.BASE_URL}/applicantForm/reapply/{company_share_id}', headers=self.headers, verify='stockmarket/meroshare/meroshare_client/DigiCertGlobalRootG2.crt.pem')
        if r.ok:
            return r.json().get('applicantFormId')
        raise ValueError('Unable to fetch applicant form ID')
    
    def logout(self):
        """
        Logout the current session.
        """
        r = requests.get(
            f'{self.BASE_URL}/auth/logout/',
            headers=self.headers,
            verify='stockmarket/meroshare/meroshare_client/DigiCertGlobalRootG2.crt.pem'
        )
        if not r.ok:
            logger.info(f"Logout failed for {self.username}")