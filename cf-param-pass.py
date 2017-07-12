#!/usr/local/bin/python

import os
import json
import logging
import sys, getopt
from boto3.session import Session


class Stack(object):
    def __init__(self, result=None, stackname=None):
        self.result = result
        self.StackName = None
        self.StackStatus = None

        self.StackName = self.result['Stacks'][0]['StackName']
        self.StackStatus = self.result['Stacks'][0]['StackStatus']


    def getStackName(self):
        return self.StackStatus


    def getStackStatus(self):
        return self.StackStatus       


def establish_logger():
    global log
    logging.basicConfig(format='[%(asctime)s] [%(levelname)s]: %(message)s', datefmt='%d/%m/%Y %I:%M:%S')
    log = logging.getLogger()
    log.setLevel(logging.DEBUG)
    logging.getLogger('botocore').setLevel(logging.CRITICAL)


def usage_options():
    WHITE = '\033[1m'
    RESET = '\033[0m'
    print
    print '{white}cf-param-pass{reset} - Pass params to CloudFormation'.format(white=WHITE, reset=RESET)
    print "Parameters and template flag are required fields"
    print
    print "  -?\tDisplay Help"
    print "  -s\t--stackname\t\tStackname"
    print "  -r\t--region\t\tRegion"
    print "  -p\t--params\t\tParameters"
    print "  -t\t--template\t\tTemplate"
    print
    print "{white}Examples:{reset}".format(white=WHITE, reset=RESET)
    print "./cf-param-pass.py -s create-simple-user -t ./simple-new-user.json -p \"Firstname=darth;Surname=Guinea\" --region us-east-1"
    sys.exit(1)


def boto_connect(region='ap-southeast-2'):
    session = None
    session = Session(region_name=region)
    return session


def expand_params(params=None):
    emptylist = []
    for p in params.split(';'):
        #new_param = { p.split('=')[0]: p.split('=')[1] }
        new_param = { 'ParameterKey': p.split('=')[0], 'ParameterValue': p.split('=')[1] }
        emptylist.append(new_param)

    log.info("Expanding params {0}".format(emptylist))
    
    return emptylist


def does_stack_exist(region='ap-southeast-2', stackname=None):
    StackStatuses = [
                'IN_PROGRESS',
                'ROLLBACK_COMPLETE',
                ]

    session = boto_connect(region=region)
    cf = session.client('cloudformation')

    try: 
        ''' Update stack '''
        result = cf.describe_stacks(StackName=stackname)
        stack = Stack(result, stackname)
        if stack.StackStatus in StackStatuses:
            log.error('Sorry, this task cannot be completed at this time. ' \
                        'Wrong Cloudformation status: [{0}]'.format(stack.StackStatus))
            sys.exit(1)
        log.info("Found stack [{0}], I am updating this stack".format(stackname))
        return True
    except:
        ''' Create stack '''
        log.info("Could not find stack [{0}], creating a new one with this name".format(stackname))
    return False


def get_template_file(filename=None):
    template = None
    if os.path.isfile(filename):
        f = open(filename)
        template = f.read()
    return template


def create_stack(region=None, stackname=None, template=None, params=None):
    function_parameters = { }

    log.info("Attempting to create stack with parameters " \
        "for region [{0}]".format(region))

    parameters = expand_params(params)
    session = boto_connect(region=region)

    function_parameters = {
        'StackName': stackname,
        'Parameters': parameters,
        'Capabilities': ['CAPABILITY_NAMED_IAM'],
    }

    log.info("Executing Params [{0}]".format(function_parameters))

    if 's3' not in template:
        function_parameters['TemplateBody'] = get_template_file(template)
    else:
        function_parameters['TemplateURL'] = template

    cf = session.client('cloudformation')
    if does_stack_exist(region, stackname):
        ''' Update Stack '''
        cf.update_stack(**function_parameters)
    else:
        ''' Create Stack '''
        cf.create_stack(**function_parameters)


def main(argv):
    params = None
    template = None
    stackname = None
    region = 'ap-southeast-2'

    establish_logger()

    try:
        opts, args = getopt.getopt(argv, "?p:t:r:s:", ["region=", "params=", "template=", "stackname="])
    except getopt.GetoptError:
        usage_options()

    for opt, arg in opts:
        if opt == '-?':
            usage_options()
        elif opt in ('-p', '--params'):
            params = arg
        elif opt in ('-s', '--stackname'):
            stackname = arg
        elif opt in ('-t', '--template'):
            template = arg
        elif opt in ('-r', '--region'):
            region = arg

    if params is None:
        usage_options()
    if template is None:
        usage_options()
    if stackname is None:
        usage_options()

    create_stack(region=region, stackname=stackname, \
                    template=template, params=params)


if __name__ == '__main__':
    main(sys.argv[1:])


