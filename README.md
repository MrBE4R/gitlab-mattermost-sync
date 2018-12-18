# gitlab-mattermost-sync

Python project to sync GitLab groups and project membership to mattermost

The script will create the missing GitLab groups and projects into mattermost and sync membership of all GitLab groups and projects. 

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites

This project has been tested on CentOS 7.6 with GitLab 11.x.x and Mattermost 5.x.x .

```
Python           : 3.4.9
pip3             : 8.1.2
python-gitlab    : 1.6.0
mattermostdriver : 6.1.1
```

### Installing

You could either install requirements system wide or use virtual environment / conda, choose your poison.

To get this up and running you just need to do the following :

* Clone the repo
```bash
git clone https://github.com/MrBE4R/gitlab-mattermost-sync.git
```
* Install requirements
```bash
pip3 install -r ./gitlab-mattermost-sync/requirements.txt
```
* Edit config.json with you values
```bash
EDITOR ./gitlab-mattermost-sync/config.json
```
* Start the script and enjoy your sync users and groups being synced
```bash
cd ./gitlab-mattermost-sync && ./gitlab-mattermost-sync.py
```

You should get something like this :
```bash
Initializing gitlab-ldap-sync.
Done.
Connecting to GitLab
Done.
Connecting to Mattermost
Done.
Getting all groups from GitLab.
Done.
Getting all projects from GitLab.
Done.
Getting all groups from Mattermost.
Done.
Importing groups from GitLab
|- Workgin on < Group Name >.
|  |- < Group Name > already not exist in Mattermost, skipping creation.
|  |  |- User < login > present in GitLab and Mattermost, skipping
|  |  |- User < login > present in GitLab but not in Mattermost, updating Mattermost
|  |  |  |- User < login > does not have a mattermost account, skipping.
|  |- Done
|- Done
Done.
Importing project from GitLab
|- Workgin on < Project Name >.
|  |- < Project Name > already not exist in Mattermost, skipping creation.
|  |  |- User < login > present in GitLab and Mattermost, skipping
|  |  |- User < login > present in GitLab and Mattermost, skipping
|  |  |- User < login > present in GitLab and Mattermost, skipping
|- Done
Done.
Cleaning Mattermost membership
|- Workgin on < Channel Name >.
|  |  |- User gitlab present in GitLab and Mattermost, skipping
|- Done.
|- Workgin on < Channel Name >.
|  |  |- User < login > present in GitLab and Mattermost, skipping
|  |  |- User < login > present in GitLab and Mattermost, skipping
|  |  |- User < login > present in GitLab and Mattermost, skipping
|- Done.
Done.

```

You could add the script in a cron to run it periodically.
## Deployment

How to configure config.json
```json5
{
  "syncInterval": "10m",                     // Actually not using it for now
  "log": "/tmp/gitlab-mattermost-sync.log",  // Actually not using it for now
  "gitlab": {
    "api": "https://gitlab.example.com",     // Url of your GitLab 
    "private_token": "xxxxxxxxxxxxxxxxxxxx", // Token generated in GitLab for an user with admin access
    "oauth_token": "",
  },
  "mattermost": {
    "api": "https://mattermost.example.com", // Url of your Mattermost 
    "private_token": "xxxxxxxxxxxxxxxxxxxx", // Token generated in GitLab for an user with admin access
    "username": "",                          // Login of mattermost admin user
    "password": ""                           // Password of mattermost admin user
  },
  "cleanup_mattermost": true
}

```
You should use ```private_token``` or ```oauth_token``` but not both. Check [the gitlab documentation](https://docs.gitlab.com/ce/user/profile/personal_access_tokens.html#creating-a-personal-access-token) for how to generate the personal access token.

You should use ```private_token``` or ```username``` and ```password``` but not both. Check [the mattermost documentation](https://docs.mattermost.com/developer/personal-access-tokens.html) for how to generate the personal access token.

The accounts used should have admin right in GitLab and Mattermost.

```cleanup_mattermost``` If set to true, the script will add and remove users in mattermost channels depending of their groups in GitLab.
## TODO

* Maybe implement sync interval directly in the script to avoid using cron or systemd
* Use a true logging solution (no more silly print statements)
* Find a way to create users in Mattermost from GitLab
* your suggestions
## Built With

* [Python](https://www.python.org/)
* [python-mattermost](https://vaelor.github.io/python-mattermost-driver/)
* [python-gitlab](https://python-gitlab.readthedocs.io/en/stable/)

## Contributing

Please read [CONTRIBUTING.md](https://gist.github.com/PurpleBooth/b24679402957c63ec426) for details on our code of conduct, and the process for submitting pull requests to us.

## Authors

* **Jean-François GUILLAUME (Jeff MrBear)** - *Initial work* - [MrBE4R](https://github.com/MrBE4R)

See also the list of [contributors](https://github.com/MrBE4R/gitlab-mattermost-sync/contributors) who participated in this project.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details

## Acknowledgments

* Hat tip to anyone whose code was used