#for unit testing the functions
import os
from resellerAPIs import resellerSoapAPIs as r
wsdl = 'file:///' +  os.path.abspath("./query.jws.xml")
#url = 'https://api.ws.symantec.com/webtrust/query.jws?WSDL'
h = r.TestApi(wsdl,
    'GetOrderByPartnerOrderID',
    UserName='username',
    password='password',
    partnercode='partnercode',
    PartnerOrderID='parterorderid',
    ReturnProductDetail=True,
    ReturnContacts=True,
    criterion = [1,2])
h.process_soap_request()
h.validate_and_capture_response_data(
    returncount=0,
    queryresponseheader_successcode=0)
h.print_relevant_data()

