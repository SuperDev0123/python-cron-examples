import os
import json
import requests
from lxml import etree
from requests.exceptions import HTTPError
from requests_toolbelt import SSLAdapter


class Office365(object):
    """
    Class to authenticate Office  365 Sharepoint
    """

    def __init__(self, share_point_site, username, password):
        self.Username = username
        self.Password = password
        self.share_point_site = share_point_site

    def GetSecurityToken(self, username, password):
        """
        Grabs a security Token to authenticate to Office 365 services
        """
        url = "https://login.microsoftonline.com/extSTS.srf"
        body = """
                <s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope"
                  xmlns:a="http://www.w3.org/2005/08/addressing"
                  xmlns:u="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd">
              <s:Header>
                <a:Action s:mustUnderstand="1">http://schemas.xmlsoap.org/ws/2005/02/trust/RST/Issue</a:Action>
                <a:ReplyTo>
                  <a:Address>http://www.w3.org/2005/08/addressing/anonymous</a:Address>
                </a:ReplyTo>
                <a:To s:mustUnderstand="1">https://login.microsoftonline.com/extSTS.srf</a:To>
                <o:Security s:mustUnderstand="1"
                   xmlns:o="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd">
                  <o:UsernameToken>
                    <o:Username>%s</o:Username>
                    <o:Password>%s</o:Password>
                  </o:UsernameToken>
                </o:Security>
              </s:Header>
              <s:Body>
                <t:RequestSecurityToken xmlns:t="http://schemas.xmlsoap.org/ws/2005/02/trust">
                  <wsp:AppliesTo xmlns:wsp="http://schemas.xmlsoap.org/ws/2004/09/policy">
                    <a:EndpointReference>
                      <a:Address>%s</a:Address>
                    </a:EndpointReference>
                  </wsp:AppliesTo>
                  <t:KeyType>http://schemas.xmlsoap.org/ws/2005/05/identity/NoProofKey</t:KeyType>
                  <t:RequestType>http://schemas.xmlsoap.org/ws/2005/02/trust/Issue</t:RequestType>
                  <t:TokenType>urn:oasis:names:tc:SAML:1.0:assertion</t:TokenType>
                </t:RequestSecurityToken>
              </s:Body>
            </s:Envelope>""" % (
            username,
            password,
            self.share_point_site,
        )
        headers = {"accept": "application/json;odata=verbose"}

        response = requests.post(url, body, headers=headers)

        xmldoc = etree.fromstring(response.content)

        token = xmldoc.find(
            ".//{http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd}BinarySecurityToken"
        )
        if token is not None:
            return token.text
        else:
            raise Exception("Check username/password and rootsite")

    def get_cookies(self):
        """
        Grabs the cookies form your Office Sharepoint site
        and uses it as Authentication for the rest of the calls
        """
        sectoken = self.GetSecurityToken(self.Username, self.Password)
        url = self.share_point_site + "/_forms/default.aspx?wa=wsignin1.0"
        response = requests.post(url, data=sectoken)
        return response.cookies


class Site(object):
    """Connect to SharePoint Site
    """

    def __init__(
        self,
        site_url,
        auth=None,
        authcookie=None,
        verify_ssl=True,
        ssl_version=None,
        timeout=None,
    ):
        self.site_url = site_url
        self._verify_ssl = verify_ssl

        self._session = requests.Session()
        if ssl_version is not None:
            self._session.mount("https://", SSLAdapter(ssl_version))

        if authcookie is not None:
            self._session.cookies = authcookie
        else:
            self._session.auth = auth

        self.timeout = timeout

    def _headers(self):
        headers = {"Accept": "application/json;odata=verbose"}
        return headers

    def _headers_digest(self):
        digest = self.getDigest()
        headers = {
            "Accept": "application/json;odata=verbose",
            "X-RequestDigest": digest,
            "Content-Type": "application/json;odata=verbose",
        }
        return headers

    def _do_http_get(self, url):
        response = self._session.get(
            url=url,
            headers=self._headers(),
            verify=self._verify_ssl,
            timeout=self.timeout,
        )
        return response

    def _do_http_post(self, url, data):
        response = self._session.post(
            url=url,
            headers=self._headers(),
            data=data,
            verify=self._verify_ssl,
            timeout=self.timeout,
        )
        return response

    def _do_http_post_with_header(self, url, data, headers):
        try:
            response = self._session.post(
                url=url,
                headers=headers,
                data=data,
                verify=self._verify_ssl,
                timeout=self.timeout,
            )
            # If the response was successful, no Exception will be raised
            response.raise_for_status()
        except HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")  # Python 3.6
        except Exception as err:
            print(f"Other error occurred: {err}")  # Python 3.6
        else:
            print("Success!")

    def get_files(self, folderpath):
        """Get files list from Folder Path
      """
        url = "".join(
            [
                self.site_url,
                f"_api/Web/GetFolderByServerRelativeUrl('{folderpath}')/Files",
            ]
        )
        response = self._do_http_get(url)
        json_data = json.loads(response.content)
        files = json_data["d"]["results"]
        return files

    def create_folder(self, folderpath):
        """Get files list from Folder Path
      """
        url = "".join([self.site_url, f"/_api/Web/Folders/add('{folderpath}')"])

        digest = self.getDigest()

        headers = {
            "Accept": "application/json;odata=verbose",
            "X-RequestDigest": digest,
            "Content-Type": "application/json;odata=verbose",
        }
        response = self._do_http_post_with_header(url, {}, headers)

    def download_file(self, filename, filepath):
        """Download file from relative file path
        """
        url = "".join(
            [self.site_url, f"_api/Web/GetFileByServerRelativeUrl('{filepath}')/$value"]
        )
        response = self._do_http_get(url)

        path = DOWNLOAD_DIR
        if not os.path.exists(path):
            os.makedirs(path)

        with open(f"{path}/{filename}", "wb") as f:
            f.write(response.content)
            f.close()

        return response.content

    def upload_file(self, folderpath, filepath, filename):
        """Upload file to relative file path
        """
        url = "".join(
            [
                self.site_url,
                f"_api/web/GetFolderByServerRelativeUrl('{folderpath}')/Files/add(url='{filename}',overwrite=true)",
            ]
        )
        headers = {
            "accept": "application/json;odata=verbose",
            "X-RequestDigest": self.getDigest(),
            "content-type": "application/x-www-urlencoded; charset=UTF-8",
        }
        with open(os.path.join(filepath, filename), "rb") as read_file:
            content = read_file.read()
            response = self._do_http_post_with_header(url, content, headers)

            return True

        return False

    def move_file(self, src_relative_path, dest_path):
        """Download file from relative file path
        """
        url = "".join(
            [
                self.site_url,
                f"_api/Web/GetFileByServerRelativeUrl('{src_relative_path}')/moveTo (newurl='{dest_path}',flags=1)",
            ]
        )

        digest = self.getDigest()
        headers = {
            "Accept": "application/json;odata=verbose",
            "X-RequestDigest": digest,
            "Content-Type": "application/json;odata=verbose",
        }
        self._do_http_post_with_header(url, {}, headers)

    def copy_file(self, src_relative_path, dest_path):
        """Download file from relative file path
        """
        url = "".join(
            [
                self.site_url,
                f"_api/Web/GetFileByServerRelativeUrl('{src_relative_path}')/copyTo(strNewUrl='{dest_path}',boverwrite=true)",
            ]
        )

        digest = self.getDigest()
        headers = {
            "Accept": "application/json;odata=verbose",
            "X-RequestDigest": digest,
            "Content-Type": "application/json;odata=verbose",
        }
        self._do_http_post_with_header(url, {}, headers)

    def getDigest(self):
        url = "".join([self.site_url, "/_api/contextinfo"])
        response = self._do_http_post(url, {})
        json_data = json.loads(response.content)
        digest = json_data["d"]["GetContextWebInformation"]["FormDigestValue"]
        return digest
