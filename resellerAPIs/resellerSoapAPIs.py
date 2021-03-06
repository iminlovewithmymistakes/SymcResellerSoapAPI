import logging
import os
from suds import client as sudsClient  ##https://bitbucket.org/jurko/suds/issues/93/sudsclient-raise-exception
from suds.cache import NoCache




logging.basicConfig(level=logging.INFO)
logging.getLogger('suds.transport.http').setLevel(logging.DEBUG)


logging.info('''
__maintainer__ = 'debaditya_mohankudo@symantec.com'
>>>Working
>the input data template for an api is dynamically created from wsdl in run time
>this is filled by a recursive function which searches for the parameters from test data
>and posted

>this can also verify the result parameters and mark testcase pass/fail

>hence any new api can be tested without modifying the code 

>>>WARNING: 
>Does not work for hello api
''')

class TestApi():
    """Creates soap object types
       e.g. TestApi(url,'GetOrderByPartnerOrderID',
            authToken_UserName='XXXXX',authtokenpassword='XXXX',
            queryrequestheaderpartnercode='xxxxx',
            QueryRequestHeaderPartnerOrderID='xxxxxx',)
    """
    def __init__(self, wsdl, api_name, **api_params):
        '''
        Initialization
        http://stackoverflow.com/questions/1769403/understanding-kwargs-in-python
        '''
        self.dict_test_data = Util().make_key_lower_in_testdata(api_params)
        self.api_name = api_name
        self.wsdl = wsdl

    def _create_soap_client(self):
        '''create a soap client using suds library
           takes wsdl url OR file as input
        '''
        self.client = sudsClient.Client(self.wsdl, cache=NoCache())

    def _create_input_obj_type(self):
        self.input_soap_template = self.client.factory.create(self.api_name)[0]
        logging.info('>>> Template defination for api')
        logging.info(self.api_name)
        logging.info(self.input_soap_template)

    def _set_input_test_data(self):
        '''
        sets input data for the elements in input soap object type,
        this is a wrapper  actual work done by utilities function
        '''
        (self.input_soap_object_w_test_data,
            self.dict_test_data) = Util(
                ).find_element_recursively_and_set_data(
                      self.input_soap_template,
                      self.dict_test_data,
                      soap_to_dict=False)

    def _post_soap_request(self):
        post_soap_handle = getattr(self.client.service, self.api_name)
        logging.info('--' * 40)
        self.response_soap_object = post_soap_handle(
                                    self.input_soap_object_w_test_data)


    def process_soap_request(self):
        '''This posts the api requst with test data
           and receives the response soap object
        '''
        self._create_soap_client()
        self._create_input_obj_type()
        self._set_input_test_data()
        self._post_soap_request()

    def validate_and_capture_response_data(self, **expected_values):
        '''
            takes expected parameter and corresponding values as input and
            compares each one with acutal values if any one parameter mismatches 
            with expected the api test is failed
        '''
        self.response_soap_object, self.dict_response_data = Util(
                    ).find_element_recursively_and_set_data(
                    self.response_soap_object, dict_data={},
                    soap_to_dict=True)
        self.dict_expected_data = expected_values
        self.exp_vs_act_list, self.param_verify_log = Util().compare_element_values(
                                         self.dict_expected_data, self.dict_response_data)
        self._test_case_result()
        return self.testcase_result, self.dict_response_data
        # this is received the testscenario class

    def _test_case_result(self):
        ''' verify api call test status
        '''
        if False in self.exp_vs_act_list:  # any parameter mismatch
            self.testcase_result = 'FAIL'
        else:
            self.testcase_result = 'PASS'

    def print_relevant_data(self):

        logging.info('--' * 40)
        logging.info('>>>Expected data :::')
        logging.info(self.dict_expected_data)

        logging.info('--' * 40)
        logging.info(">>>test case status")
        logging.info(self.testcase_result)
        logging.info(self.param_verify_log)
        logging.info('--' * 40)


class Util():
    ''' simple utilities
    '''
    def make_key_lower_in_testdata(self, dict_test_data):
        ''''in test data keys can written in mixed cases
            e.g.
            'authToken_UserName' -> 'authtoken_username'
        '''
        for k,v in dict_test_data.items():
            del dict_test_data[k]
            dict_test_data[k.lower()] = v
        return dict_test_data

    def prepare_test_data(self, dict_test_case_data):
        return dict_test_case_data

    def type_soap_object(self, soap_element):
        if hasattr(soap_element, '__module__'):  #: find if it is leaf/branch
            if soap_element.__module__ == 'suds.sudsobject':
                return True


    def find_element_recursively_and_set_data(self,
                                              soap_object,
                                              dict_data,
                                              soap_to_dict=None,
                                              list_temp=[]):

        for (element_name, element_value) in soap_object :
            soap_element = soap_object[element_name]
            if self.type_soap_object(soap_element):
                list_temp.append(element_name)
                self.find_element_recursively_and_set_data(
                    soap_element,dict_data,
                    soap_to_dict)
            else : #: no more child element - xml leaf
                if list_temp:
                    parent = list_temp[-1]
                else:
                    parent = ''
                temp = (''.join([parent , "_", element_name]).lower()
                        , element_name.lower())  #: store both conventions
                #: parent_child, child, test input can be in both ways
                if soap_to_dict is True:  #: output soap response operation
                    #: no duplicate leaf expected in response???
                    dict_data[temp[0]] = soap_object[element_name]
                    dict_data[temp[1]] = soap_object[element_name]
                else:  #: input soap object operation
                    if temp[0] in dict_data:  #: parent_child notation
                        soap_object[element_name] = dict_data[temp[0]]
                    elif temp[1] in dict_data:
                        #: only teh child name in test data
                        soap_object[element_name] = dict_data[temp[1]]
                    else:
                        pass
        if len(list_temp) > 1:  #: coming out of one loop(parent) there must be a parent
            list_temp.pop()     #: if there is only one parent element left dont remove it
        return soap_object, dict_data

    def compare_element_values(self,
                               dict_expected_data,
                               dict_response_data):
        ''' this compares the expected values provided with actual values
        '''
        list_result = ()
        dict_log = {}
        dict_expected_data = self.make_key_lower_in_testdata(dict_expected_data)
        dict_response_data = self.make_key_lower_in_testdata(dict_response_data)
        for expected_param in dict_expected_data:
            expected = str(dict_expected_data[expected_param])
            if expected_param in dict_response_data:
                actual = str(dict_response_data[expected_param])
                result = expected == actual
                list_result += (result,)

            else:
                actual = "Not Found"
                list_result += (result,)
            dict_log[expected_param] = ('expected:', expected,
                                        'actual:', actual)
        return list_result, dict_log

    def print_dict_elements(self, dict_object):
        for k, v in dict_object.items():
            logging.info(k, '-->', v)


#for unit testing the functions
if __name__ == '__main__':
    #wsdl = 'file:///' +  os.path.abspath("./query.jws.xml")  # get from filesystem
    wsdl = "https://XXXXXXXXXX/webtrust/query.jws?wsdl"   # get from url 
    h = TestApi(wsdl,
        api_name='GetOrderByPartnerOrderID',
        UserName='xxxxxxx',
        password='Password',
        queryrequestheader_partnercode='partnercode', # parent_child also allowed - useful when there are duplicate leafs
        QueryRequestHeader_PartnerOrderID='orderid')  #  are case insensitive
    h.process_soap_request()
    h.validate_and_capture_response_data()
    h.print_relevant_data()
