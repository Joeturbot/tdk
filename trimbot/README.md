# TrimBot

This is a general clean up tool that is extensible by creating your own ingredients and adding them to a clean up recipe.

TrimBot can clean up multiple environments in a single run and is by default run in `dry-run` mode.

The application comes with a recipe to clear down V3 resources, which can be found in the file [managed_recipe.yaml](recipes/managed_recipe.yaml) 

Trimbot works by authenticating to the Turbot Master AWS account then assuming the specified role in the managed account that you want to remove.  Any role can be used by Trimbot, though `turbot_superuser` is always available and has sufficient privileges to do what Trimbot needs. 

The path of authentication for managed accounts goes:

> Workstation (Trimbot Scripts ) -> STS/Access Keys to Turbot Master -> Assume into the role in managed account specified in the workspace.yaml file -> Perform required operations.


## Sections:

- [Requirements and Planning](#Requirements)
- [Installing Trimbot](#Installing)
- [Configuring Trimbot](#Configuring)
- [Running Trimbot](#Running)
- [Uninstalling](#Uninstalling)

## Requirements

### Requirements for IAM Policy for access to Turbot Master Account
The user or role used to authenticate to the Turbot Master must have permissions to assume into the `turbot_superuser` role in all accounts.  The below policy is taken from the `arn:aws:iam::111122223333:role/turbot/turbot_console` deployed in every v3 Turbot Master.
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Action": [
                "sts:AssumeRole"
            ],
            "Resource": [
                "arn:aws:iam::*:role/turbot/core/turbot_metadata",
                "arn:aws:iam::*:role/turbot/core/turbot_superuser"
            ],
            "Effect": "Allow"
        }
    ]
}
```

## Planning
### Cleaning up a v3 Environment
1. Decommission resources out of managed accounts
    1. Get a list of all imported accounts.
    2. Set the `Turbot > Logs > Retention in Days` to `1` from the default of `90`.  This will help with cleaning up the regional logging buckets. 
    3. Provision or get access to a user/role that can assume into the turbot_superuser role in the target managed account(s).
    4. Install and configure Trimbot as specified in the [Installation](#Installation) section.
    5. Pick a pilot account to test with.
    6. Configure `config/managed_account.yaml` to include the AWS CLI profile
    7. Run Trimbot in dry-run mode first.  Closely verify that the resources in the child account are what you want to remove.
    8. After verifying Trimbot's output, go ahead and run it in `--approve` set.
    9. If this is successful, configure more workspaces for Trimbot work on as seen in the `config/multiple_accounts.yaml` file.  Repeat steps 7 and 8 till all desired accounts have been removed.
    
2. Decommission Turbot Master
    1.  Follow steps 5 to 7 from above but directed at the Turbot Master account itself.  As it was very common to import the Turbot Master account into Turbot, the event handling infrastructure needs to be cleaned up there too.
    2.  Turbot Customer Support recommends that all accounts should be removed from Turbot before complete decommissioning.  This ensures that there aren't any orphan event handlers or logging buckets.  
    3. Cleaning up the Turbot application is as simple as deleting the various CloudFormation templates (`Turbot-DB*`, `Turbot-Console`, `Turbot-Q`).

## Installing

To install the application will require you to [create a virtual environment](#Creating%20the%20virtual%20environment) and then [install the application](#Installing%20the%20application).

### Creating the virtual environment

This sections details how to set up a virtual environment in order for the script to run.

### Virtual environments activation

This application uses the Python version 3 module, [venv](https://docs.python.org/3/library/venv.html) to create the a virtual environment.

1. Navigate to the the root folder of the Trimbot application.
2. Use the following command to create the virtual environment. <BR>The command will create a folder called `.venv` which is a child of the root folder for the applications.

```shell
python3 -m venv .venv
```

3. Activate the environment by running the following command.

```shell
source .venv/bin/activate
```

### Installing the application

1. Ensure that the virual enviroment is activated.
1. Navigate to the the root folder of the Trimbot application.
1. Install application Python library dependencies by running the following command.

```shell
pip3 install .
```

### AWS CLI
The AWS CLI is essential for proper operation of Trimbot.  It must be installed and configured with access to the Turbot Master AWS Account.  The profile name will be used in the workspace YAML files. More details on configuring the AWS CLI can be found in the [AWS documentation](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html).

## Configuring
These configuration sections are in rough order required for decommissioning a v3 environment. They can be used in any order required.

Available recipes:

- managed_recipe.yaml

### Configuring managed account

To clean up a managed account is similar to cleaning a master account but this time we provide a role.
The role will be used to assume the role to access the managed account.

```yaml
recipe: "./recipes/managed_recipe.yaml"
workspaces:
  - account: "333322221111"
    profile: v3-master
    roleArn: arn:aws:iam::333322221111:role/turbot-service-role
    externalId: keyphrase
    turbot:
      account: aab
      cluster: awscluster
      host: https://test.turbot.com/
      accessKey: "11112222-fac3-424e-94fb-325db1d65503"
      secretAccessKey: 424e94fb-1b3c-4681-944d-cb27d3a325db
```

| Field                       | Purpose                                                                           | Needed |
| --------------------------- | --------------------------------------------------------------------------------- | ------ |
| recipe                      | Configures which recipe to use for all workspaces configured to run with TrimBot. | Yes    |
| workspaces                  | Runs the recipe against the configured workspaces.                                | Yes    |
| workspaces.account          | The AWS account number of the account that will be uninstalled.                   | Yes    |
| workspaces.profile          | The AWS profile of the master account where Turbot master is installed.           | No     |
| workspaces.roleArn          | The AWS role which will be assumed to access the managed account.                 | Yes    |
| workspaces.externalId       | The External ID for the role if there is one needed.                              | No     |
| workspaces.turbot.account   | The Turbot Account ID of the account to uninstall.                                | Yes    |
| workspaces.turbot.cluster   | The Turbot Cluster ID of the account to uninstall.                                | Yes    |
| workspaces.turbot.host      | The Turbot Host where the account was installed.                                  | Yes    |
| workspaces.turbot.accessKey | The access key used to preform API calls against the Turbot Host.                 | Yes    |
| workspaces.turbot.cluster   | The secret access key used to preform API calls against the Turbot Host.          | Yes    |

The above configuration will set the entire run to use the recipe located at `./recipes/managed_recipe.yaml`.
The account that will be removed from Turbot management is the AWS account with ID `333322221111` using the AWS role.
The account is given the ID of `aab` in cluster `awscluster`.

### Configuring master account

To clean up a master account, all you will need is for the AWS client to have a profile that connects to the AWS master account.  The AWS profile should have sufficient permissions to perform the required steps. A typical configuration looks as follows:

```yaml
recipe: "./recipes/managed_recipe.yaml"
workspaces:
  - account: "111122223333"
    profile: v3-master
    turbot:
      account: aaa
      cluster: maincluster
      host: https://test.turbot.com/
      accessKey: "11112222-fac3-424e-94fb-325db1d65503"
      secretAccessKey: 424e94fb-1b3c-4681-944d-cb27d3a325db
```

| Field                       | Purpose                                                                           | Needed |
| --------------------------- | --------------------------------------------------------------------------------- | ------ |
| recipe                      | Configures which recipe to use for all workspaces configured to run with TrimBot. | Yes    |
| workspaces                  | Runs the recipe against the configured workspaces.                                | Yes    |
| workspaces.account          | The AWS account number of the account that will be uninstalled.                   | Yes    |
| workspaces.profile          | The AWS profile of the master account where Turbot master is installed.           | No     |
| workspaces.turbot.account   | The Turbot Account ID of the account to uninstall.                                | Yes    |
| workspaces.turbot.cluster   | The Turbot Cluster ID of the account to uninstall.                                | Yes    |
| workspaces.turbot.host      | The Turbot Host where the account was installed.                                  | Yes    |
| workspaces.turbot.accessKey | The access key used to preform API calls against the Turbot Host.                 | Yes    |
| workspaces.turbot.cluster   | The secret access key used to preform API calls against the Turbot Host.          | Yes    |

The above configuration will set the entire run to use the recipe located at `./recipes/managed_recipe.yaml`.
The account that will be removed from Turbot management is the AWS account with ID `111122223333` using the AWS profile `v3-master`.
The account is given the ID of `aaa` in cluster `maincluster`.



### Configuring multiple accounts

```yaml
recipe: "./recipes/managed_recipe.yaml"
turbot:
  host: https://test.turbot.com/
  accessKey: "11112222-fac3-424e-94fb-325db1d65503"
  secretAccessKey: 424e94fb-1b3c-4681-944d-cb27d3a325db
workspaces:
  - account: "111122223333"
    profile: v3-master
    turbot:
      account: aaa
      cluster: maincluster
  - account: "333322221111"
    profile: v3-master
    roleArn: arn:aws:iam::333322221111:role/turbot-service-role
    externalId: keyphrase
    turbot:
      account: aab
      cluster: awscluster
  - account: "222233331111"
    roleArn: arn:aws:iam::222233331111:role/turbot-service-role
    turbot:
      account: rex
      cluster: awsaccount
      host: https://production.turbot.com/
      accessKey: "11112222-aaaa-bbbb-cccc-325db1d65503"
      secretAccessKey: 424e94fb-bbbb-aaaa-dddd-cb27d3a325db
```

There is no needed to repeat Turbot host information for each workspace.
If you configure the Turbot details at the parent level, it will be applied to each workspace.
You can override the Turbot connection details on an individual workspace as seen for the Turbot account `rex`.

## Running

### Getting available options

Use the terminal to get available options:

```shell
trimbot --help
```

### TrimBot dry run

To run a dry run clean, you will need a configuration file.

```shell
trimbot --config-file './path/to/file.yaml'
```

### TrimBot trace approved run

To run an approved clean up run, you will need to add the option `--approve`.

```shell
trimbot --config-file './path/to/file.yaml' --approve
```

### TrimBot s3 bucket check run

To run check ingredients only, you will have to add the option `--check`.
The check ingredient for recipe `managed_recipe.yaml` checks to see if the S3 buckets are ready to be deleted.

```shell
trimbot --config-file './path/to/file.yaml' --check
```

## Uninstalling

In order to uninstall the application, it is advised to simply remove the virtual folder that was created when [creating a virtual enviroment](#Creating%20the%20virtual%20environment).

If the virtual environment is currently active, you will have to [deactivate the virtual environnment](#Deactivating%20current%20virtual%20environment) before removing the folder.

### Deactivating current virtual environment

This is accomplished by running the command in the same folder that we created the environment by applying the command:

```shell
deactivate
```

### Remove the folder

In the same directory that we created the virtual enviroment, you can remove the vitual environment by running the command:

```shell
rm -rf ./.venv
```
