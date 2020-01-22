from zeep import Client
from zeep.wsse.username import UsernameToken
from requests.auth import HTTPBasicAuth 
from zeep.transports import Transport
from requests import Session
from requests_ntlm import HttpNtlmAuth
import json

session = Session()
session.auth = HttpNtlmAuth('WIN-C1A8J5A01OV\\crmsynchuser', 'synchuser@1')

cl = Client('http://52.62.6.209:7047/DynamicsNAV110/WS/CRONUS%20Australia%20Pty.%20Ltd./Codeunit/DeliverMe?WSDL',
            transport=Transport(session=session))

req_data = {
'username': 'crmsynchuser',
'password': 'synchuser@1',
'domain': 'WIN-C1A8J5A01OV'
}

def send_request(client, data):
	print(client)
	r = client.service.UpdateShipment(jsonText=json.dumps(data))
	return r

r = send_request(cl, req_data)
print(r)