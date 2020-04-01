import click
import turbot
from sgqlc.endpoint.http import HTTPEndpoint


# -c .config/turbot/credentials.yml --profile env --parent 167 --sub 8fd --tenant 7ea --client_id 5b1 --client_key "key"
@click.command()
@click.option('-c', '--config-file', type=click.Path(dir_okay=False), help="Pass an optional yaml config file.")
@click.option('-p', '--profile', default="default", help="Profile to be used from config file.")
@click.option('--parent', required=True, help="The resource id for the parent folder of this subscription")
@click.option('--account_id', required=True, help="The resource id for the parent folder of this subscription")
@click.option('--role', required=True, help="Full ARN for the cross-account role that Turbot will use to manage this account")
@click.option('--external_id', required=True, help="External ID for the cross-account role")
def run_controls(config_file, profile, parent, account_id, role, external_id):
    """Import an AWS Account"""

    config = turbot.Config(config_file, profile)
    headers = {'Authorization': 'Basic {}'.format(config.auth_token)}
    endpoint = HTTPEndpoint(config.graphql_endpoint, headers)

    aws_mutation = '''
mutation CreateAwsAccount($input: CreateResourceInput!) {
  createResource(input: $input) {
    turbot {
      id
    }
  }
}
    '''
    credentials_mutation = '''
mutation SetAwsAccountPolicies($inputIamRole: CreatePolicySettingInput!, $inputIAMRoleExternalIdCommand: CreatePolicySettingInput!) {
  iamRole: createPolicySetting(input: $inputIamRole) {
    turbot {
      id
    }
  }
  iamRoleExternalId: createPolicySetting(input: $inputIAMRoleExternalIdCommand) {
    turbot {
      id
    }
  }
}
        '''

    """
    The parent variable holds the resource ID of the folder where this subscription will be imported.
    """
    aws_variables = {
        "input": {
            "parent": parent,
            "type": "tmod:@turbot/aws#/resource/types/account",
            "data": {
                "Id": "123456789012"
            },
            "metadata": {
                "aws": {
                    "accountId": account_id,
                    "partition": "aws"
                }
            }
        }
    }

    try:
        print("Importing account")
        account_run = endpoint(aws_mutation, aws_variables)
        account_rid = account_run['data']['createResource']['turbot']['id']
        # print("Sub run: {}".format(sub_run))
        print("\tSubscription Resource ID: {}".format(account_rid))

        credentials_variables = {
            "inputIamRole": {
                "type": "tmod:@turbot/aws#/policy/types/turbotIamRole",
                "resource": account_rid,
                "value": role,
                "precedence": "REQUIRED"
            },
            "inputIAMRoleExternalIdCommand": {
                "type": "tmod:@turbot/aws#/policy/types/turbotIamRoleExternalId",
                "resource": account_rid,
                "value": external_id,
                "precedence": "REQUIRED"
            }
        }

        creds_run = endpoint(credentials_mutation, credentials_variables)
        # print("Creds run: {}".format(creds_run))
        print("Import complete")
    except Exception as e:
        print("Create Sub response: {}".format(account_run))
        print("Set Creds response: {}".format(creds_run))
        print("Could not set subscription credentials because of error: {}".format(e))


if __name__ == "__main__":
    run_controls()
